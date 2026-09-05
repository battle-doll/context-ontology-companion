"""Package/contract tests, not product runtime or security certification."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_design as design


class DesignPackageTests(unittest.TestCase):
    def test_normal_relative_path_is_accepted(self):
        self.assertEqual(str(design.safe_relative("docs/02_ARCHITECTURE.md")), "docs/02_ARCHITECTURE.md")

    def test_unsafe_paths_are_rejected(self):
        for path in ("/etc/passwd", "../escape.md", "docs/../escape.md", "docs//file.md", "./file.md", "C:/file.md", "docs\\file.md", "", ".git/config", ".env", ".env.local", "data.db", "secret.pem", "user-data/private.json"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                design.safe_relative(path)

    def test_outside_source_cannot_be_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                design.source_file(Path(tmp), "../outside.md")

    def test_missing_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                design.source_file(Path(tmp), "missing.md")

    def test_symlink_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.md"
            target.write_text("synthetic", encoding="utf-8")
            try:
                (root / "link.md").symlink_to(target)
            except OSError:
                self.skipTest("Symlink creation unavailable in this environment")
            with self.assertRaisesRegex(ValueError, "Symlink"):
                design.source_file(root, "link.md")

    def test_manifest_round_trip_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "DESIGN_VERSION").write_text("0.1.0-draft.1\n", encoding="utf-8")
            (root / "README.md").write_text("# synthetic\n", encoding="utf-8")
            self.assertEqual(design.write_manifest(root), 2)
            self.assertEqual(set(design.verify_manifest(root)), {"DESIGN_VERSION", "README.md"})
            (root / "README.md").write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Manifest mismatch"):
                design.verify_manifest(root)

    def test_unlisted_file_invalidates_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "DESIGN_VERSION").write_text("0.1.0-draft.1\n", encoding="utf-8")
            design.write_manifest(root)
            (root / "extra.md").write_text("unexpected", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "file set"):
                design.verify_manifest(root)

    def test_manifest_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "DESIGN_VERSION").write_text("0.1.0-draft.1\n", encoding="utf-8")
            design.write_manifest(root)
            first = (root / design.MANIFEST).read_bytes()
            design.write_manifest(root)
            self.assertEqual(first, (root / design.MANIFEST).read_bytes())

    def test_broken_markdown_link_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "README.md"
            doc.write_text("[missing](missing.md)\n", encoding="utf-8")
            errors, count = design.markdown_checks(root, [doc])
            self.assertEqual(count, 1)
            self.assertEqual(len(errors), 1)

    def test_unclosed_markdown_fence_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "README.md"
            doc.write_text("```text\nnot closed\n", encoding="utf-8")
            errors, _ = design.markdown_checks(root, [doc])
            self.assertTrue(any("Unclosed" in e for e in errors))

    def test_external_links_and_code_examples_are_not_local_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "README.md"
            doc.write_text("[docs](https://example.invalid/docs)\n```text\n[example](not-a-file.md)\n```\n", encoding="utf-8")
            errors, count = design.markdown_checks(root, [doc])
            self.assertFalse(errors)
            self.assertEqual(count, 0)

    def test_schema_and_synthetic_fixture_expectations(self):
        result = design.schema_checks()
        if result["status"] == "SKIPPED":
            self.skipTest(result["reason"])
        self.assertEqual(result["schemas"], 3)
        self.assertEqual(result["fixtures"], 8)
        self.assertEqual(result["invalid_fixtures_rejected"], 4)

    def test_product_cases_are_not_falsely_marked_executed(self):
        data = json.loads((design.ROOT / "evals/design-cases.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(data["cases"]), 37)
        self.assertTrue(all(c["execution_status"] == "not_run" for c in data["cases"]))

    def test_no_fabricated_submission_manifest(self):
        submission_path=design.ROOT / "chatgpt-app-submission.json"
        if submission_path.exists():
            import subprocess
            import sys
            actual=json.loads(subprocess.check_output([sys.executable,str(design.ROOT/"scripts/run.py"),"tools"],text=True))
            submission=json.loads(submission_path.read_text(encoding="utf-8"))
            self.assertEqual(set(submission["tools"]),{t["name"] for t in actual["tools"]})
            for tool in actual["tools"]:
                self.assertTrue(tool.get("inputSchema"))
                self.assertTrue(tool.get("outputSchema"))
                self.assertEqual(submission["tools"][tool["name"]]["annotations"],{k:tool["annotations"][k] for k in ("readOnlyHint","destructiveHint","openWorldHint")})
            state=json.loads((design.ROOT/"release-state.json").read_text(encoding="utf-8"))["states"]
            self.assertTrue(state["local-implemented"])
            self.assertFalse(state["submitted"])
            self.assertFalse(state["published"])
        draft = json.loads((design.ROOT / "submission/review-cases.draft.json").read_text(encoding="utf-8"))
        self.assertEqual(draft["status"], "DESIGN_ONLY_NOT_SUBMITTABLE")
        self.assertEqual(len(draft["test_cases"]), 5)
        self.assertEqual(len(draft["negative_test_cases"]), 3)

    def test_package_is_internally_consistent(self):
        result = design.validate()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["scope"], "DESIGN_PACKAGE_ONLY")
        self.assertEqual(result["product_evaluations_executed"], 0)


if __name__ == "__main__":
    unittest.main()
