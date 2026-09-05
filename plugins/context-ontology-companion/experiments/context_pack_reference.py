"""Reference experiment: bounded, atomic selection of synthetic context groups.

NOT a product compiler, auth layer, retriever, temporal engine or truth validator.
The caller must supply already-authorized, time-selected, correctly grouped data.
Production integration must recheck permissions/deletions and supply a real unit
counter. The default unit is UTF-8 bytes, never an inferred token count.

Algorithm: include all required groups, then optional groups by descending
priority with a stable ID tie-breaker. It is a greedy policy, not a claim of
optimal retrieval or globally optimal packing. Every group includes its evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Callable, Iterable


@dataclass(frozen=True)
class Claim:
    claim_id: str
    statement: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class Group:
    group_id: str
    required: bool
    priority: int
    claims: tuple[Claim, ...]
    kind: str = "context"


@dataclass(frozen=True)
class Result:
    serialized: str
    measured_size: int
    budget: int
    unit: str
    included: tuple[str, ...]
    omitted: tuple[str, ...]


class InsufficientBudget(ValueError):
    """Required groups plus metadata cannot fit; no success payload is emitted."""
    def __init__(self, required_size: int, budget: int) -> None:
        self.required_size = required_size
        self.budget = budget
        super().__init__(f"insufficient_budget: required={required_size}, budget={budget}")


def utf8_bytes(text: str) -> int:
    return len(text.encode("utf-8"))


def _identifier(value: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,96}", value):
        raise ValueError("invalid bounded identifier")


def _validate(groups: list[Group]) -> None:
    if len(groups) > 100:
        raise ValueError("too many groups")
    seen_groups: set[str] = set()
    seen_claims: set[str] = set()
    for group in groups:
        if not isinstance(group, Group):
            raise ValueError("expected Group")
        _identifier(group.group_id)
        if group.group_id in seen_groups:
            raise ValueError("duplicate group id")
        seen_groups.add(group.group_id)
        if type(group.required) is not bool or type(group.priority) is not int:
            raise ValueError("invalid required or priority type")
        if not -10000 <= group.priority <= 10000:
            raise ValueError("priority outside experiment bound")
        if group.kind not in {"context", "conflict_set"}:
            raise ValueError("unsupported group kind")
        if not isinstance(group.claims, tuple) or not 1 <= len(group.claims) <= 16:
            raise ValueError("invalid claim group size")
        if group.kind == "conflict_set" and len(group.claims) < 2:
            raise ValueError("a conflict group needs at least two claims")
        for claim in group.claims:
            if not isinstance(claim, Claim):
                raise ValueError("expected Claim")
            _identifier(claim.claim_id)
            if claim.claim_id in seen_claims:
                raise ValueError("overlapping claim groups must be normalized upstream")
            seen_claims.add(claim.claim_id)
            if (not isinstance(claim.statement, str) or not claim.statement.strip()
                    or len(claim.statement) > 2000):
                raise ValueError("invalid bounded statement")
            if (not isinstance(claim.evidence_refs, tuple)
                    or not 1 <= len(claim.evidence_refs) <= 8):
                raise ValueError("claim requires bounded evidence references")
            if len(set(claim.evidence_refs)) != len(claim.evidence_refs):
                raise ValueError("duplicate evidence reference")
            for evidence in claim.evidence_refs:
                _identifier(evidence)
    if len(seen_claims) > 200:
        raise ValueError("too many claims")


def _render(all_groups: list[Group], selected: set[str]) -> str:
    ordered = sorted(all_groups, key=lambda g: (not g.required, -g.priority, g.group_id))
    omitted = sorted(g.group_id for g in ordered if g.group_id not in selected)
    payload = {
        "reference_only": True,
        "authorization_check": "not_performed_by_reference",
        "retrieval_completeness": "not_assessed",
        "candidate_coverage": "partial" if omitted else "complete",
        "required_groups_complete": True,
        "groups": [
            {
                "group_id": g.group_id,
                "kind": g.kind,
                "required": g.required,
                "claims": [
                    {"id": c.claim_id, "statement": c.statement,
                     "evidence_refs": list(c.evidence_refs)}
                    for c in g.claims
                ],
            }
            for g in ordered if g.group_id in selected
        ],
        "omitted_group_ids": omitted,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def assemble(groups: Iterable[Group], *, budget: int,
             measure: Callable[[str], int] = utf8_bytes,
             unit: str = "utf8_bytes") -> Result:
    """Select atomic groups and bound the entire serialized result.

    `measure` must be deterministic and use the declared unit. A caller using
    tokens must supply an actual tokenizer; this module provides none. Exceptions
    are internal outcomes, not automatically rendered oversized model messages.
    """
    if type(budget) is not int or budget < 0:
        raise ValueError("budget must be a nonnegative integer")
    if not isinstance(unit, str) or not unit.strip() or len(unit) > 96:
        raise ValueError("unit is required")
    # Bound enumeration too: never consume an unbounded iterator indefinitely.
    items: list[Group] = []
    for item in groups:
        items.append(item)
        if len(items) > 100:
            raise ValueError("too many groups")
    _validate(items)

    def measured(text: str) -> int:
        size = measure(text)
        if type(size) is not int or size < 0:
            raise ValueError("measure must return a nonnegative integer")
        return size

    selected = {g.group_id for g in items if g.required}
    first = _render(items, selected)
    required_size = measured(first)
    if required_size > budget:
        raise InsufficientBudget(required_size, budget)
    for group in sorted((g for g in items if not g.required), key=lambda g: (-g.priority, g.group_id)):
        candidate = selected | {group.group_id}
        if measured(_render(items, candidate)) <= budget:
            selected = candidate
    serialized = _render(items, selected)
    size = measured(serialized)
    if size > budget:
        # Protect against a changed/nondeterministic counter; do not assert success.
        raise ValueError("measurement changed or final budget violated")
    return Result(
        serialized=serialized, measured_size=size, budget=budget, unit=unit,
        included=tuple(sorted(selected)),
        omitted=tuple(sorted(g.group_id for g in items if g.group_id not in selected)),
    )
