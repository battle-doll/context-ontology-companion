"""Persistent CLI/local-MCP tests with selected synthetic inputs and private temp homes."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "vendor"))
from companion_contracts import validate_artifact
from context_companion.local_cli import PROFILE, project_scope
from context_companion.local_mcp import TOOLS


def candidate(statement="합성 프로젝트 결정"):
    return {"statement": statement, "kind": "decision", "origin": "model_inferred",
            "evidence": [{"id": "selected-source", "origin": "model_inferred", "locator": "selected://synthetic-example"}],
            "valid_from": "2026-01-01T00:00:00Z", "valid_until": None}


class LocalWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="context-local-workflow-")
        self.base = Path(self.temp.name).resolve()
        self.project = self.base / "프로젝트 with spaces"; self.project.mkdir()
        self.cwd = self.base / "unrelated-working-directory"; self.cwd.mkdir()
        self.home = self.base / "private-runtime"
        self.input = self.base / "selected.json"
        self.input.write_text(json.dumps(candidate(), ensure_ascii=False), encoding="utf-8")
        self.environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        self.environment.pop("PYTHONPATH", None)

    def tearDown(self):
        self.temp.cleanup()

    def cli(self, operation, *arguments, expected=0, scoped=True, stdin=None):
        command = [sys.executable, str(ROOT / "scripts/run.py"), "local-" + operation, "--home", str(self.home)]
        if scoped: command += ["--project-root", str(self.project)]
        result = subprocess.run(command + list(arguments), cwd=self.cwd, env=self.environment, input=stdin,
                                text=True, encoding="utf-8", capture_output=True, timeout=20)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout if expected == 0 else result.stderr)

    def save(self, request="save-001", **kwargs):
        return self.cli("save", "--input", str(self.input), "--authorization", "explicit-user-request", "--request-id", request, **kwargs)

    def test_missing_read_does_not_initialize_or_create_files(self):
        result = self.cli("search", expected=1)
        self.assertEqual(result["error"], "LOCAL_CLI_NOT_INITIALIZED_USE_LOCAL_INIT")
        self.assertFalse(self.home.exists())

    def test_init_is_idempotent_and_project_scope_independent_of_cwd(self):
        result = self.cli("init")
        self.assertEqual(result["scope"], project_scope(project_root=self.project))
        before = (self.home / "local-cli.json").read_bytes()
        self.assertEqual(self.cli("init")["scope"], result["scope"])
        self.assertEqual((self.home / "local-cli.json").read_bytes(), before)
        self.assertFalse((self.home / "operator.json").exists())
        self.assertFalse((self.home / "context.sqlite3").exists())

    def test_persistent_save_recover_update_delete_and_idempotent_retries(self):
        self.cli("init")
        first = self.save()
        self.assertEqual(first["profile"], PROFILE)
        self.assertFalse(first["human_review_performed"])
        receipt = first["result"]["authorization"]
        self.assertEqual(receipt["mode"], PROFILE)
        self.assertEqual(receipt["actor_kind"], "local_os_account")
        self.assertFalse(receipt["human_review_performed"])
        self.assertEqual(self.save(), first)
        record_id = first["result"]["record_id"]
        recovered = self.cli("fetch", "--id", record_id)["result"]
        self.assertEqual(recovered["statement"], candidate()["statement"])
        self.assertEqual(recovered["origin"], "model_inferred")
        self.assertEqual(recovered["evidence"], candidate()["evidence"])
        artifact = self.cli("export")
        self.assertEqual(validate_artifact(artifact)["status"], "valid")
        self.assertEqual(artifact["producer"]["version"], "0.1.1")
        self.assertNotIn("authorization", artifact["payload"]["decisions"][0])
        self.input.write_text(json.dumps(candidate("수정한 합성 결정")), encoding="utf-8")
        changed = self.cli("update", "--id", record_id, "--expected-revision", "1", "--input", str(self.input),
                           "--authorization", "explicit-user-request", "--request-id", "update-001")
        self.assertEqual(self.cli("fetch", "--id", record_id)["result"]["status"], "superseded")
        self.assertEqual(len(self.cli("history", "--id", record_id)["result"]["history"]), 2)
        new_id = changed["result"]["record_id"]
        deletion = ("--id", new_id, "--expected-revision", "1", "--authorization", "explicit-user-request", "--request-id", "delete-001")
        removed = self.cli("delete", *deletion)
        self.assertEqual(self.cli("delete", *deletion), removed)
        self.assertEqual(self.cli("fetch", "--id", new_id, expected=1)["error"], "NOT_FOUND_OR_FORBIDDEN")
        self.assertEqual(self.cli("search")["result"]["records"], [])
        self.assertEqual(self.cli("status", "--proposal-id", removed["result"]["proposal_id"])["result"], removed["result"])

    def test_profile_conflicts_and_actor_mismatch_fail_closed(self):
        self.home.mkdir(mode=0o700)
        (self.home / "operator.json").write_text("{}")
        self.assertEqual(self.cli("init", expected=1)["error"], "LOCAL_PROFILE_CONFLICT_USE_SEPARATE_HOME")
        self.assertFalse((self.home / "local-context.sqlite3").exists())
        (self.home / "operator.json").unlink()
        self.cli("init")
        config = json.loads((self.home / "local-cli.json").read_text())
        config["account_key"] = "os_" + "0" * 64
        (self.home / "local-cli.json").write_text(json.dumps(config))
        self.assertEqual(self.cli("search", expected=1)["error"], "LOCAL_OS_ACCOUNT_MISMATCH")

    def test_bad_selected_input_and_duplicate_request_do_not_add_records(self):
        self.cli("init")
        self.save()
        self.input.write_text(json.dumps(candidate("different")))
        self.assertEqual(self.save(expected=1)["error"], "IDEMPOTENCY_CONFLICT")
        for raw in ('{"statement":"first","statement":"second"}', '{"statement":NaN}', '[' * 100 + ']' * 100):
            result = self.cli("save", "--input", "-", "--authorization", "explicit-user-request", "--request-id", "bad-input", stdin=raw, expected=1)
            self.assertEqual(result["error"], "INVALID_CANDIDATE_JSON")
        self.assertEqual(len(self.cli("search")["result"]["records"]), 1)

    def test_wrong_project_cannot_fetch_modify_or_inspect_status(self):
        self.cli("init")
        first = self.save()["result"]
        self.project = self.base / "other-project"; self.project.mkdir()
        self.cli("init")
        self.assertEqual(self.cli("fetch", "--id", first["record_id"], expected=1)["error"], "NOT_FOUND_OR_FORBIDDEN")
        self.assertEqual(self.cli("status", "--proposal-id", first["proposal_id"], expected=1)["error"], "NOT_FOUND_OR_FORBIDDEN")
        self.assertEqual(self.cli("delete", "--id", first["record_id"], "--expected-revision", "1", "--authorization", "explicit-user-request", "--request-id", "wrong-project", expected=1)["error"], "NOT_FOUND_OR_FORBIDDEN")

    def test_read_commands_preserve_database_and_contradictions_keep_both_sides(self):
        self.cli("init")
        first = self.save()["result"]
        self.input.write_text(json.dumps(candidate("합성 반대 결정")))
        other = self.cli("contradict", "--id", first["record_id"], "--expected-revision", "1", "--input", str(self.input),
                         "--authorization", "explicit-user-request", "--request-id", "conflict-001")["result"]
        before = hashlib.sha256((self.home / "local-context.sqlite3").read_bytes()).hexdigest()
        self.cli("fetch", "--id", first["record_id"])
        self.cli("history", "--id", first["record_id"])
        self.cli("search")
        pack = self.cli("pack", "--query", "반대")["result"]
        self.assertEqual(len(pack["pack"]["records"]), 2)
        self.assertEqual(len(pack["pack"]["contradictions"]), 1)
        self.assertEqual(self.cli("pack", "--max-chars", "1")["result"]["status"], "insufficient_budget")
        self.cli("export")
        self.cli("status", "--proposal-id", other["proposal_id"])
        self.cli("projects", scoped=False)
        self.assertEqual(hashlib.sha256((self.home / "local-context.sqlite3").read_bytes()).hexdigest(), before)
        self.cli("revoke", "--id", other["record_id"], "--expected-revision", "1", "--authorization", "explicit-user-request", "--request-id", "revoke-001")
        self.assertEqual(len(self.cli("search")["result"]["records"]), 1)

    def test_actual_local_mcp_initialize_discover_save_search_and_contract_export(self):
        self.cli("init")
        requests = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "synthetic-client", "version": "1"}}},
                    {"jsonrpc": "2.0", "method": "notifications/initialized"},
                    {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": None}]
        for ident, name, arguments in [(3, "save_context", {"candidate": candidate(), "authorization": "explicit-user-request", "request_id": "mcp-save-001"}),
                                       (4, "search", {}), (5, "export_context", {}), (6, "save_context", {"candidate": candidate(), "authorization": "user_approved", "request_id": "forged"}),
                                       (7, "search", {"project_id": "foreign"})]:
            requests.append({"jsonrpc": "2.0", "id": ident, "method": "tools/call", "params": {"name": name, "arguments": arguments}})
        result = subprocess.run([sys.executable, str(ROOT / "scripts/run.py"), "local-stdio", "--home", str(self.home), "--project-root", str(self.project)],
                                cwd=self.cwd, env=self.environment, input="\n".join(json.dumps(request) for request in requests) + "\n", capture_output=True, text=True, encoding="utf-8", timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        responses = {item["id"]: item for item in map(json.loads, result.stdout.splitlines())}
        self.assertEqual(responses[1]["result"]["serverInfo"]["version"], "0.1.1")
        self.assertEqual({tool["name"] for tool in responses[2]["result"]["tools"]}, {tool["name"] for tool in TOOLS})
        self.assertFalse(responses[3]["result"]["isError"])
        self.assertEqual(len(responses[4]["result"]["structuredContent"]["result"]["records"]), 1)
        self.assertEqual(validate_artifact(responses[5]["result"]["structuredContent"])["status"], "valid")
        self.assertTrue(responses[6]["result"]["isError"])
        self.assertTrue(responses[7]["result"]["isError"])
        from jsonschema import Draft202012Validator
        for ident, name in [(3, "save_context"), (4, "search"), (5, "export_context"), (6, "save_context"), (7, "search")]:
            descriptor = next(tool for tool in TOOLS if tool["name"] == name)
            Draft202012Validator(descriptor["outputSchema"]).validate(responses[ident]["result"]["structuredContent"])
        for descriptor in TOOLS:
            if descriptor["name"] in {"save_context", "update_context", "contradict_context", "revoke_context", "delete_context"}:
                self.assertFalse(descriptor["annotations"]["readOnlyHint"])
            if descriptor["name"] in {"update_context", "revoke_context", "delete_context"}:
                self.assertTrue(descriptor["annotations"]["destructiveHint"])


if __name__ == "__main__": unittest.main()
