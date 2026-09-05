"""Offline safety tests. GitHub operations are mocked; no remote repo is created."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bootstrap_github as bootstrap


def completed(stdout: str = "", stderr: str = "", code: int = 0):
    return subprocess.CompletedProcess([], code, stdout, stderr)


class BootstrapSafetyTests(unittest.TestCase):
    def test_plan_has_no_network_or_write(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(subprocess, "run", side_effect=AssertionError("unexpected subprocess")):
            dest = Path(tmp) / "new"
            result = bootstrap.plan(dest)
            self.assertEqual(result["mode"], "PLAN_ONLY_NO_NETWORK_NO_WRITES")
            self.assertFalse(dest.exists())

    def test_plan_cli_does_not_create_bytecode_or_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts = root / "scripts"
            scripts.mkdir()
            for name in ("bootstrap_github.py", "validate_design.py"):
                (scripts / name).write_bytes((Path(bootstrap.__file__).parent / name).read_bytes())
            before = {p.relative_to(root).as_posix() for p in root.rglob("*")}
            result = subprocess.run([sys.executable, str(scripts / "bootstrap_github.py"), "--plan"], capture_output=True, text=True, check=True, timeout=10)
            self.assertEqual(json.loads(result.stdout)["mode"], "PLAN_ONLY_NO_NETWORK_NO_WRITES")
            after = {p.relative_to(root).as_posix() for p in root.rglob("*")}
            self.assertEqual(before, after)

    def test_plan_is_fixed_private_separate_repository(self):
        result = bootstrap.plan(Path("unused"))
        self.assertEqual(result["repository"], "battle-doll/context-ontology-companion")
        self.assertEqual(result["visibility"], "private")
        self.assertEqual(result["branch"], "docs/initial-design")
        self.assertIn("merge", result["will_not"])
        self.assertIn("switch public", result["will_not"])

    def test_identity_rejects_other_account(self):
        calls = []
        def runner(args, **kwargs):
            calls.append(args)
            return completed("someone-else\n" if "user" in args else "")
        with self.assertRaisesRegex(bootstrap.BootstrapError, "does not match"):
            bootstrap.verify_identity("battle-doll", runner)
        self.assertFalse(any("create" in args for args in calls))

    def test_identity_accepts_correct_account_and_existing_git_identity(self):
        def runner(args, **kwargs):
            return completed("BATTLE-DOLL\n" if "user" in args else "configured\n")
        bootstrap.verify_identity("battle-doll", runner)

    def test_identity_rejects_missing_git_identity(self):
        def runner(args, **kwargs):
            if args[0] == "git":
                return completed(code=1)
            return completed("battle-doll\n" if "user" in args else "")
        with self.assertRaisesRegex(bootstrap.BootstrapError, "Configure Git"):
            bootstrap.verify_identity("battle-doll", runner)

    def test_existing_repository_is_not_modified(self):
        with self.assertRaisesRegex(bootstrap.BootstrapError, "already exists"):
            bootstrap.require_absent("battle-doll/context-ontology-companion", lambda *args, **kwargs: completed("{}"))

    def test_explicit_404_allows_creation_check(self):
        for response in ("HTTP/2.0 404 Not Found", "gh: Not Found (HTTP 404)"):
            with self.subTest(response=response):
                bootstrap.require_absent("battle-doll/context-ontology-companion", lambda *args, **kwargs: completed(stderr=response, code=1))

    def test_permission_and_network_errors_do_not_mean_absent(self):
        for response in ("HTTP/2.0 403 Forbidden", "HTTP 401", "HTTP 429", "network timeout", "not found without status"):
            with self.subTest(response=response), self.assertRaisesRegex(bootstrap.BootstrapError, "not proven"):
                bootstrap.require_absent("battle-doll/context-ontology-companion", lambda *args, **kwargs: completed(stderr=response, code=1))

    def test_destination_must_not_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            dest = Path(tmp) / "existing"
            dest.mkdir()
            with self.assertRaisesRegex(bootstrap.BootstrapError, "already exists"):
                bootstrap.check_destination(dest, source)

    def test_destination_cannot_overlap_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            for dest in (source, source / "child", Path(tmp)):
                with self.subTest(dest=dest), self.assertRaisesRegex(bootstrap.BootstrapError, "ancestor/descendant"):
                    bootstrap.check_destination(dest, source)

    def test_destination_requires_existing_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            with self.assertRaisesRegex(bootstrap.BootstrapError, "parent does not exist"):
                bootstrap.check_destination(Path(tmp) / "missing" / "new", source)

    def test_new_sibling_destination_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            dest = Path(tmp) / "new"
            self.assertEqual(bootstrap.check_destination(dest, source), dest.resolve())
            self.assertFalse(dest.exists())

    def test_git_auth_is_command_scoped_not_global(self):
        args = bootstrap.git_args("push", "origin", bootstrap.BRANCH)
        self.assertNotIn("--global", args)
        self.assertIn("credential.helper=!gh auth git-credential", args)
        self.assertEqual(args[-3:], ["push", "origin", bootstrap.BRANCH])

    def test_missing_tool_stops_before_any_operation(self):
        with patch.object(bootstrap.shutil, "which", return_value=None), patch.object(bootstrap, "run") as runner:
            with self.assertRaisesRegex(bootstrap.BootstrapError, "Required tool is missing"):
                bootstrap.apply(Path("never-created"))
            runner.assert_not_called()

    def test_full_flow_with_mocked_remote_uses_private_repo_and_draft_pr(self):
        """Checks orchestration only; this does not exercise the real GitHub API."""
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "package"
            source.mkdir()
            (source / "README.md").write_text("# synthetic design\n", encoding="utf-8")
            (source / "FILE_MANIFEST.json").write_text("{}\n", encoding="utf-8")
            destination = Path(tmp) / "clone"
            url = "https://github.com/battle-doll/context-ontology-companion"
            sha = "a" * 40
            commands = []
            def runner(args, **kwargs):
                commands.append(args)
                if args[:3] == ["gh", "repo", "view"]:
                    return completed(json.dumps({"nameWithOwner": "battle-doll/context-ontology-companion", "isPrivate": True, "defaultBranchRef": {"name": "main"}, "url": url}))
                if args[0] == "git" and "clone" in args:
                    destination.mkdir()
                    return completed()
                if args[:3] == ["git", "remote", "get-url"]:
                    return completed(url + ".git\n")
                if args[:3] == ["git", "diff", "--cached"]:
                    return completed("README.md\nFILE_MANIFEST.json\n")
                if args[:2] == ["git", "rev-parse"]:
                    return completed(sha + "\n")
                if "ls-remote" in args:
                    return completed(sha + "\trefs/heads/docs/initial-design\n")
                if args[:3] == ["gh", "pr", "create"]:
                    return completed(url + "/pull/1\n")
                if args[:3] == ["gh", "pr", "view"]:
                    return completed(json.dumps({"url": url + "/pull/1", "isDraft": True, "state": "OPEN", "headRefName": bootstrap.BRANCH, "baseRefName": "main"}))
                return completed()
            with patch.object(bootstrap, "ROOT", source), patch.object(bootstrap, "run", side_effect=runner), patch.object(bootstrap.shutil, "which", return_value="available"), patch.object(bootstrap, "validate", return_value={"status": "PASS", "scope": "TEST_STUB"}), patch.object(bootstrap, "verify_manifest", return_value=["README.md"]), patch.object(bootstrap, "verify_identity"), patch.object(bootstrap, "require_absent"):
                result = bootstrap.apply(destination)
            self.assertEqual(result["status"], "CREATED_AND_VERIFIED")
            self.assertFalse(result["plugin_submitted"])
            self.assertFalse(result["plugin_published"])
            create = next(c for c in commands if c[:3] == ["gh", "repo", "create"])
            self.assertIn("--private", create)
            pr = next(c for c in commands if c[:3] == ["gh", "pr", "create"])
            self.assertIn("--draft", pr)
            self.assertIn(bootstrap.BRANCH, pr)
            stage = next(c for c in commands if c[:2] == ["git", "add"])
            self.assertEqual(stage, ["git", "add", "--", "README.md", "FILE_MANIFEST.json"])
            self.assertFalse(any("merge" in c or "--force" in c or "--public" in c for c in commands))
            self.assertEqual((destination / "README.md").read_text(encoding="utf-8"), "# synthetic design\n")

    def test_partial_remote_creation_failure_is_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "clone"
            def runner(args, **kwargs):
                if args[:3] == ["gh", "repo", "view"]:
                    return completed(json.dumps({"nameWithOwner": "battle-doll/context-ontology-companion", "isPrivate": False}))
                return completed()
            with patch.object(bootstrap, "run", side_effect=runner), patch.object(bootstrap.shutil, "which", return_value="available"), patch.object(bootstrap, "validate", return_value={}), patch.object(bootstrap, "verify_manifest", return_value=[]), patch.object(bootstrap, "verify_identity"), patch.object(bootstrap, "require_absent"):
                with self.assertRaisesRegex(bootstrap.BootstrapError, "Repository creation: CREATED"):
                    bootstrap.apply(destination)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
