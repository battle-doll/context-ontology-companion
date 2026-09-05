#!/usr/bin/env python3
"""Validate this design package, not the future product. No network requests."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "FILE_MANIFEST.json"
IGNORED_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".pytest_cache", "runtime-data", "user-data", "backups", "exports", "logs", ".local", "dist", "build"}
REQUIRED = [
    "README.md", "START_HERE.md", "AGENTS.md", "DESIGN_VERSION", "docs/INDEX.md",
    "docs/07_RELEASE_ROADMAP.md", "docs/10_CODEX_HANDOFF.md",
    "docs/13_SOURCES_AND_VERIFICATION.md", "docs/agent/CURRENT_STATE.md",
    "docs/agent/NEXT_ACTIONS.md", "docs/agent/reports/2026-08-29-design-bootstrap.md",
    "contracts/fixture-index.json", "evals/design-cases.json",
    "submission/review-cases.draft.json", "scripts/bootstrap_github.py",
]


def safe_relative(value: str) -> PurePosixPath:
    """Allow only normal relative package paths, never credentials or Git internals."""
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError(f"Invalid relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError(f"Unsafe package path: {value!r}")
    if any(part in IGNORED_DIRS for part in path.parts):
        raise ValueError(f"Excluded directory: {value!r}")
    name = path.name.lower()
    if name == ".env" or name.startswith(".env.") or name == ".bootstrap-state.json":
        raise ValueError(f"Private-state file forbidden: {value!r}")
    if path.suffix.lower() in {".pem", ".key", ".p12", ".pfx", ".db", ".sqlite", ".sqlite3", ".pyc"}:
        raise ValueError(f"Sensitive/runtime file forbidden: {value!r}")
    return path


def source_file(root: Path, relative: str) -> Path:
    rel = safe_relative(relative)
    root = root.resolve()
    path = root.joinpath(*rel.parts)
    current = root
    for part in rel.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Symlink forbidden: {relative}")
    if not path.resolve().is_relative_to(root) or not path.is_file():
        raise ValueError(f"Missing or out-of-scope file: {relative}")
    return path


def package_files(root: Path) -> list[Path]:
    result = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        if path.name in {MANIFEST, ".bootstrap-state.json", ".DS_Store", "Thumbs.db"} or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise ValueError(f"Symlink forbidden: {relative.as_posix()}")
        if path.is_file():
            safe_relative(relative.as_posix())
            result.append(path)
    return result


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(root: Path = ROOT) -> int:
    files = package_files(root)
    payload = {
        "manifest_version": 1,
        "package": "context-ontology-companion",
        "design_version": (root / "DESIGN_VERSION").read_text(encoding="utf-8").strip(),
        "intended_repository": "battle-doll/context-ontology-companion",
        "files": [{"path": p.relative_to(root).as_posix(), "sha256": digest(p), "bytes": p.stat().st_size} for p in files],
    }
    (root / MANIFEST).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(files)


def verify_manifest(root: Path = ROOT) -> list[str]:
    data = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    if data.get("manifest_version") != 1 or data.get("package") != "context-ontology-companion":
        raise ValueError("Unexpected manifest identity/version")
    names: list[str] = []
    for entry in data.get("files", []):
        relative = entry["path"]
        path = source_file(root, relative)
        if relative in names:
            raise ValueError(f"Duplicate manifest path: {relative}")
        if path.stat().st_size != entry["bytes"] or digest(path) != entry["sha256"]:
            raise ValueError(f"Manifest mismatch: {relative}")
        names.append(relative)
    actual = {p.relative_to(root).as_posix() for p in package_files(root)}
    if not names or set(names) != actual:
        raise ValueError("Manifest file set does not match the package")
    return names


def markdown_checks(root: Path, files: list[Path]) -> tuple[list[str], int]:
    errors: list[str] = []
    links = 0
    pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in files:
        if path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        fence: str | None = None
        prose: list[str] = []
        for line in text.splitlines():
            match = re.match(r"^\s*(`{3,}|~{3,})", line)
            if match:
                marker = match.group(1)[0]
                if fence is None:
                    fence = marker
                elif fence == marker:
                    fence = None
                continue
            if fence is None:
                prose.append(line)
        if fence is not None:
            errors.append(f"Unclosed Markdown fence: {path.relative_to(root)}")
        for target in pattern.findall("\n".join(prose)):
            target = target.strip().strip("<>")
            if urlsplit(target).scheme or target.startswith(("#", "//")):
                continue
            local = unquote(target.split("#", 1)[0].split("?", 1)[0])
            if not local:
                continue
            links += 1
            resolved = (path.parent / local).resolve()
            if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
                errors.append(f"Broken local link: {path.relative_to(root)} -> {target}")
    return errors, links


def schema_checks(root: Path = ROOT, require: bool = False) -> dict:
    if importlib.util.find_spec("jsonschema") is None or importlib.util.find_spec("referencing") is None:
        if require:
            raise ValueError("jsonschema/referencing unavailable; install only with explicit environment authorization")
        return {"status": "SKIPPED", "reason": "optional jsonschema/referencing not installed"}
    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry, Resource
    from referencing.exceptions import NoSuchResource

    def no_network(uri: str):
        raise NoSuchResource(ref=uri)

    schemas = {}
    registry = Registry(retrieve=no_network)
    for path in sorted((root / "contracts/draft-0.1").glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        schemas[path.relative_to(root / "contracts").as_posix()] = schema
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    cases = json.loads((root / "contracts/fixture-index.json").read_text(encoding="utf-8"))["cases"]
    for case in cases:
        payload = json.loads(source_file(root / "contracts", case["file"]).read_text(encoding="utf-8"))
        validator = Draft202012Validator(schemas[case["schema"]], registry=registry, format_checker=FormatChecker())
        errors = list(validator.iter_errors(payload))
        if (not errors) != case["expected_valid"]:
            detail = errors[0].message if errors else "unexpectedly accepted invalid fixture"
            raise ValueError(f"Fixture expectation failed: {case['file']}: {detail}")
    return {"status": "PASS", "schemas": len(schemas), "fixtures": len(cases), "invalid_fixtures_rejected": sum(not c["expected_valid"] for c in cases)}


def validate(root: Path = ROOT, require_schema: bool = False, require_manifest: bool = False) -> dict:
    errors = [f"Missing required file: {n}" for n in REQUIRED if not (root / n).is_file()]
    files = package_files(root)
    json_count = 0
    for path in files:
        if path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
            json_count += 1
        if path.suffix in {".md", ".json", ".py"}:
            text = path.read_text(encoding="utf-8")
            if re.search(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", text):
                errors.append(f"Possible private key material: {path.relative_to(root)}")
            if re.search(r"gh[pousr]_[A-Za-z0-9]{30,}", text):
                errors.append(f"Possible credential material: {path.relative_to(root)}")
    md_errors, links = markdown_checks(root, files)
    errors.extend(md_errors)
    evaluations = json.loads((root / "evals/design-cases.json").read_text(encoding="utf-8"))["cases"]
    ids = [c["id"] for c in evaluations]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate evaluation case IDs")
    required_ids = {f"FR-{i:02d}" for i in range(1, 15)} | {f"NFR-{i:02d}" for i in range(1, 9)}
    mapped = {c["requirement"] for c in evaluations}
    if missing := required_ids - mapped:
        errors.append(f"Requirements lacking a planned evaluation: {sorted(missing)}")
    submission = json.loads((root / "submission/review-cases.draft.json").read_text(encoding="utf-8"))
    if len(submission["test_cases"]) != 5 or len(submission["negative_test_cases"]) != 3:
        errors.append("Submission draft must contain exactly 5 positive and 3 negative cases")
    if submission.get("status") != "DESIGN_ONLY_NOT_SUBMITTABLE":
        errors.append("Submission draft status must not imply a real submission")
    if errors:
        raise ValueError("\n".join(errors))
    schema_result = schema_checks(root, require_schema)
    manifest_result = "NOT_PRESENT"
    if (root / MANIFEST).exists():
        verify_manifest(root)
        manifest_result = "PASS"
    elif require_manifest:
        raise ValueError("FILE_MANIFEST.json missing")
    return {"status": "PASS", "scope": "DESIGN_PACKAGE_ONLY", "files_excluding_manifest": len(files), "json_files_excluding_manifest": json_count, "local_links_checked": links, "schema_validation": schema_result, "planned_product_evaluations": len(evaluations), "planned_v2_product_evaluations": len(json.loads((root / "evals/v2-design-cases.json").read_text(encoding="utf-8"))["cases"]) if (root / "evals/v2-design-cases.json").exists() else 0, "product_evaluations_executed": 0, "submission_positive_cases": 5, "submission_negative_cases": 3, "manifest": manifest_result}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-schema", action="store_true", help="Fail if optional JSON Schema validator is unavailable")
    parser.add_argument("--require-manifest", action="store_true")
    parser.add_argument("--write-manifest", action="store_true", help="Explicitly refresh hashes after reviewing all intended files")
    args = parser.parse_args()
    try:
        if args.write_manifest:
            write_manifest()
        result = validate(require_schema=args.require_schema, require_manifest=args.require_manifest)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
