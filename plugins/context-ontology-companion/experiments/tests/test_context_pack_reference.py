"""Synthetic reference tests only; no product auth, retrieval or model is tested."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from context_pack_reference import Claim, Group, InsufficientBudget, assemble, utf8_bytes


def group(name: str, *, required: bool = False, priority: int = 0,
          statement: str = "합성 프로젝트의 승인된 제약을 유지합니다.") -> Group:
    return Group(name, required, priority, (Claim("c_" + name, statement, ("src_" + name,)),))


class ContextPackReferenceTests(unittest.TestCase):
    def test_empty_candidates_do_not_claim_global_completeness(self):
        result = assemble([], budget=10000)
        data = json.loads(result.serialized)
        self.assertEqual(data["candidate_coverage"], "complete")
        self.assertEqual(data["retrieval_completeness"], "not_assessed")
        self.assertEqual(data["authorization_check"], "not_performed_by_reference")

    def test_required_groups_all_present_when_fitting(self):
        result = assemble([group("a", required=True), group("b", required=True)], budget=10000)
        self.assertEqual(result.included, ("a", "b"))
        self.assertTrue(json.loads(result.serialized)["required_groups_complete"])

    def test_insufficient_required_budget_emits_no_success(self):
        data = [group("a", required=True)]
        size = assemble(data, budget=10000).measured_size
        with self.assertRaises(InsufficientBudget) as cm:
            assemble(data, budget=size-1)
        self.assertEqual(cm.exception.required_size, size)

    def test_exact_budget_boundary(self):
        data = [group("a", required=True)]
        size = assemble(data, budget=10000).measured_size
        result = assemble(data, budget=size)
        self.assertEqual(result.measured_size, size)

    def test_evidence_remains_attached(self):
        result = assemble([group("a", required=True)], budget=10000)
        claim = json.loads(result.serialized)["groups"][0]["claims"][0]
        self.assertEqual(claim["evidence_refs"], ["src_a"])

    def test_optional_overflow_is_partial(self):
        data = [group("required", required=True), group("large", statement="x"*2000)]
        result = assemble(data, budget=800)
        self.assertEqual(result.included, ("required",))
        self.assertEqual(result.omitted, ("large",))
        self.assertEqual(json.loads(result.serialized)["candidate_coverage"], "partial")
        self.assertLessEqual(result.measured_size, 800)

    def test_conflict_not_split_by_budget(self):
        conflict = Group("conflict", False, 10,
                         (Claim("a", "one"*200, ("src_a",)),
                          Claim("b", "two"*200, ("src_b",))), "conflict_set")
        result = assemble([group("required", required=True), conflict], budget=1500)
        self.assertEqual(result.included, ("required",))
        self.assertNotIn('"id":"a"', result.serialized)
        self.assertNotIn('"id":"b"', result.serialized)
        self.assertIn("conflict", result.omitted)

    def test_required_conflict_overflow_fails(self):
        conflict = Group("conflict", True, 0,
                         (Claim("a", "a"*1000, ("src_a",)),
                          Claim("b", "b"*1000, ("src_b",))), "conflict_set")
        with self.assertRaises(InsufficientBudget):
            assemble([conflict], budget=1000)

    def test_single_claim_conflict_rejected(self):
        invalid = Group("bad", False, 0, (Claim("a", "synthetic", ("src",)),), "conflict_set")
        with self.assertRaisesRegex(ValueError, "at least two"):
            assemble([invalid], budget=10000)

    def test_missing_evidence_rejected(self):
        invalid = Group("bad", True, 0, (Claim("a", "synthetic", ()),))
        with self.assertRaisesRegex(ValueError, "evidence"):
            assemble([invalid], budget=10000)

    def test_duplicate_groups_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate group"):
            assemble([group("a"), group("a")], budget=10000)

    def test_overlapping_claims_rejected(self):
        claim = Claim("shared", "synthetic", ("src",))
        with self.assertRaisesRegex(ValueError, "overlapping"):
            assemble([Group("a", False, 0, (claim,)), Group("b", False, 0, (claim,))], budget=10000)

    def test_input_order_does_not_change_output(self):
        groups = [group("b", priority=5), group("a", priority=5), group("r", required=True)]
        self.assertEqual(assemble(groups, budget=10000), assemble(reversed(groups), budget=10000))

    def test_higher_priority_selected_first(self):
        result = assemble([group("low", priority=1, statement="x"*500),
                           group("high", priority=10, statement="x"*500)], budget=1100)
        self.assertEqual(result.included, ("high",))

    def test_utf8_size_not_character_or_token_estimate(self):
        result = assemble([group("a", required=True)], budget=10000)
        self.assertEqual(result.measured_size, len(result.serialized.encode("utf-8")))
        self.assertGreater(result.measured_size, len(result.serialized))
        self.assertEqual(result.unit, "utf8_bytes")

    def test_custom_counter_must_be_explicit(self):
        result = assemble([group("a")], budget=10000, measure=len, unit="unicode_codepoints_test_only")
        self.assertEqual(result.measured_size, len(result.serialized))
        self.assertEqual(result.unit, "unicode_codepoints_test_only")

    def test_invalid_measure_rejected(self):
        for invalid in (-1, 1.5, True):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                assemble([], budget=10000, measure=lambda _: invalid)

    def test_invalid_budget_rejected(self):
        for invalid in (-1, 1.5, True):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                assemble([], budget=invalid)

    def test_large_group_iterator_bounded(self):
        def unbounded():
            i=0
            while True:
                yield group(f"g{i}")
                i += 1
        with self.assertRaisesRegex(ValueError, "too many groups"):
            assemble(unbounded(), budget=10000)

    def test_reading_or_selection_does_not_mutate_input(self):
        original = group("a", required=True)
        prior = repr(original)
        assemble([original], budget=10000)
        self.assertEqual(repr(original), prior)

if __name__ == "__main__":
    unittest.main()
