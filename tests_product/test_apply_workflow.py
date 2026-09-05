"""Actual isolated CLI and routing evidence for the Context apply workflow."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "skills/apply-context-ontology/scripts/apply_workflow.py"
spec = importlib.util.spec_from_file_location("context_apply_workflow", HELPER)
apply = importlib.util.module_from_spec(spec)
spec.loader.exec_module(apply)


def capabilities(*usable, mcp=False):
    return {product: {"installed": product in usable, "skill_exposed": product in usable,
                      "mcp_exposed": mcp and product in usable, "verified_cli": not mcp and product in usable}
            for product in apply.PRODUCTS}


class ApplyWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="context-apply-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.project = self.base / "Selected 프로젝트"
        self.project.mkdir()
        self.home = self.base / "private-home"
        self.candidate = {"statement": "Synthetic platform requirement: support Linux.", "kind": "constraint",
                          "origin": "user_asserted", "evidence": [{"id": "synthetic-source", "origin": "user_asserted", "locator": "conversation:synthetic-test"}],
                          "valid_from": "2020-01-01T00:00:00Z", "valid_until": None}

    def run_context(self, **kwargs):
        return apply.run_context(capabilities("context"), str(self.project), "platform", home=str(self.home), **kwargs)

    def save(self, **kwargs):
        return self.run_context(candidate=self.candidate, authorization="explicit-user-request", request_id="synthetic-save-1", setup_authorized=True, **kwargs)

    def dbhash(self):
        return hashlib.sha256((self.home / "local-context.sqlite3").read_bytes()).hexdigest()

    def cli(self, operation, *args):
        p = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "scripts/run.py"), "local-" + operation,
                            "--project-root", str(self.project), "--home", str(self.home), *args], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)

    def test_generic_zero_one_two_three_and_explicit_selection(self):
        for count in range(4):
            result = apply.plan(capabilities(*apply.PRODUCTS[:count]))
            self.assertEqual(result["availableCount"], count)
            self.assertEqual(result["selectedProducts"], list(apply.PRODUCTS[:count]))
            self.assertFalse(result["executionPerformed"])
        result = apply.plan(capabilities(*apply.PRODUCTS), explicit_products=["context", "contracts", "context"])
        self.assertEqual(result["selectedProducts"], ["context", "contracts"])
        self.assertEqual(apply.plan(capabilities("context"), explicit_products=["code"])["routes"][0]["route"], "unavailable")

    def test_capabilities_and_ledger_are_strict_observations(self):
        value = capabilities(*apply.PRODUCTS)
        value["code"]["skill_exposed"] = False
        self.assertNotIn("code", apply.plan(value)["selectedProducts"])
        value["contracts"] = {key: key == "installed" for key in apply.KEYS}
        self.assertNotIn("contracts", apply.plan(value)["selectedProducts"])
        for invalid in ({}, {**capabilities(), "unknown": {}}, {**capabilities(), "code": {"installed": True}}):
            with self.assertRaises(apply.ApplicationError): apply.plan(invalid)
        with self.assertRaises(apply.ApplicationError):
            apply.conversation_ledger({"version": 1, "products": {"context": {"request_key": "x", "status": {}, "evidence": {}}}})
        for raw in ('{"a":1,"a":2}', '{"a":NaN}', b'\xff', '{"a":'+'['*2000):
            with self.assertRaises(apply.ApplicationError): apply.parse_json(raw)

    def test_mcp_handoff_requires_scope_check_and_performs_no_cli(self):
        with mock.patch.object(apply.subprocess, "run", side_effect=AssertionError("must not execute")):
            result = apply.run_context(capabilities("context", mcp=True), self.project, "platform", home=self.home,
                                       candidate=self.candidate, authorization="explicit-user-request", request_id="synthetic-mcp-1")
        self.assertEqual(result["status"], "handoff_required")
        self.assertFalse(result["executionPerformed"])
        self.assertEqual(result["handoff"]["expectedScope"], result["expectedScope"])
        self.assertIn("list_projects", result["handoff"]["scopePrecondition"])
        self.assertEqual(result["ledger"]["products"]["context"]["status"], "pending")
        self.assertFalse(self.home.exists())

    def test_missing_store_and_permissions_do_not_initialize_without_authority(self):
        result = self.run_context()
        self.assertEqual(result["status"], "incomplete")
        self.assertFalse(self.home.exists())
        with self.assertRaises(apply.ApplicationError): self.run_context(candidate=self.candidate)
        self.assertFalse(self.home.exists())
        self.save(); before = self.dbhash()
        other = self.base / "Other"; other.mkdir()
        result = apply.run_context(capabilities("context"), other, "platform", home=self.home, setup_authorized=True)
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(before, self.dbhash())
        self.assertNotIn("init", [op["operation"] for op in result["operations"]])

    def test_actual_cli_save_readback_final_pack_and_dedup_requery(self):
        first = self.save()
        self.assertEqual(first["status"], "evidence_verified", first)
        self.assertEqual(first["outcome"], "saved")
        record = first["verifiedRecords"][0]
        self.assertIn(record["id"], [row["id"] for row in first["contextPack"]["pack"]["records"]])
        ops = [op["operation"] for op in first["operations"]]
        self.assertLess(ops.index("search"), ops.index("save"))
        self.assertEqual(ops[ops.index("save") + 1], "fetch")
        before = self.dbhash()
        repeated = self.save(ledger=first["ledger"])
        self.assertEqual(repeated["outcome"], "reused_exact_candidate", repeated)
        self.assertEqual(repeated["verifiedRecords"][0]["id"], record["id"])
        self.assertTrue(repeated["previousReceiptMatch"])
        self.assertEqual(before, self.dbhash())
        self.assertNotIn("save", [op["operation"] for op in repeated["operations"]])
        self.assertTrue(repeated["taskContinuationRequired"])
        self.assertFalse((self.project / ".codex").exists())
        self.assertEqual(set(self.project.iterdir()), set())

    def test_similar_candidate_is_pending_and_not_silently_merged(self):
        self.save(); before = self.dbhash()
        changed = {**self.candidate, "statement": "Synthetic platform requirement: support Windows."}
        result = self.run_context(candidate=changed, authorization="explicit-user-request", request_id="synthetic-new-request")
        self.assertEqual(result["status"], "pending_target_choice", result)
        self.assertEqual(before, self.dbhash())
        changed_date = {**self.candidate, "valid_from": "2020-01-02T00:00:00Z"}
        result = self.run_context(candidate=changed_date, authorization="explicit-user-request", request_id="synthetic-new-date")
        self.assertEqual(result["status"], "pending_target_choice")

    def test_correction_requires_revision_and_retry_recovers_same_new_record(self):
        first = self.save(); target = first["verifiedRecords"][0]
        changed = {**self.candidate, "statement": "Synthetic platform requirement: support Windows."}
        args = dict(candidate=changed, authorization="explicit-user-request", request_id="synthetic-correction",
                    target_id=target["id"], expected_revision=target["revision"])
        result = self.run_context(**args)
        self.assertEqual(result["status"], "evidence_verified", result)
        before = self.dbhash()
        retry = self.run_context(**args, ledger=result["ledger"])
        self.assertEqual(retry["status"], "evidence_verified", retry)
        self.assertEqual(result["verifiedRecords"][0]["id"], retry["verifiedRecords"][0]["id"])
        self.assertEqual(before, self.dbhash())
        args["request_id"] = "synthetic-stale-new-request"
        self.assertEqual(self.run_context(**args)["status"], "incomplete")
        self.assertEqual(before, self.dbhash())

    def test_old_ledger_does_not_skip_current_lifecycle_read(self):
        first = self.save(); record = first["verifiedRecords"][0]
        self.cli("revoke", "--id", record["id"], "--expected-revision", str(record["revision"]),
                 "--authorization", "explicit-user-request", "--request-id", "synthetic-revoke")
        before = self.dbhash()
        result = self.run_context(ledger=first["ledger"])
        self.assertEqual(result["status"], "needs_input")
        self.assertEqual(result["ledger"]["products"]["context"]["status"], "pending")
        self.assertEqual(before, self.dbhash())

    def test_child_cli_isolated_from_pythonpath_and_only_current_product_runs(self):
        poison = self.base / "poison"; poison.mkdir()
        marker = self.base / "unexpected-execution"
        (poison / "sitecustomize.py").write_text("from pathlib import Path\nPath(" + repr(str(marker)) + ").write_text('bad')\n")
        with mock.patch.dict(os.environ, {"PYTHONPATH": str(poison)}): result = self.save()
        self.assertEqual(result["status"], "evidence_verified", result)
        self.assertFalse(marker.exists())
        self.assertFalse(result["otherProductsExecuted"])
        self.assertFalse(result["persistentActivation"])

    def test_shared_ledger_keeps_other_products_and_does_not_skip_freshness(self):
        ledger = {"version": 1, "products": {"code": {"request_key": "synthetic-code", "status": "verified", "evidence": {"snapshot": "synthetic"}}}}
        planned = apply.plan(capabilities(*apply.PRODUCTS), ledger=ledger)
        self.assertEqual(planned["routes"][0]["route"], "already_applied_recheck_freshness")
        self.assertFalse(planned["executionPerformed"])
        result = self.save(ledger=ledger)
        self.assertEqual(result["ledger"]["products"]["code"], ledger["products"]["code"])
        self.assertNotIn("context", ledger["products"])

    def test_future_and_expired_records_are_stored_but_not_current_context(self):
        for stamp, until in (("2099-01-01T00:00:00Z", None), ("2000-01-01T00:00:00Z", "2001-01-01T00:00:00Z")):
            candidate = {**self.candidate, "valid_from": stamp, "valid_until": until}
            result = self.run_context(candidate=candidate, authorization="explicit-user-request",
                                      request_id="synthetic-time-" + stamp[:4], setup_authorized=True)
            self.assertEqual(result["status"], "stored_not_current", result)
            self.assertEqual(result["activationStatus"], "PENDING_EFFECTIVE_TIME")
            self.assertEqual(result["continuationEvidence"]["records"], [])
            self.assertEqual(result["contextPack"]["pack"]["records"], [])
            self.assertEqual(len(result["verifiedRecords"]), 1)
            self.assertEqual(result["ledger"]["products"]["context"]["status"], "pending")


if __name__ == "__main__": unittest.main()
