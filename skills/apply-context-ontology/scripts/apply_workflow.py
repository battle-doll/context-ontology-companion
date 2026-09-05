#!/usr/bin/env python3
"""Conversation-only routing and verified execution of the same-bundle Context CLI.

Capabilities and the shared conversation ledger are caller observations, never
authority or execution receipts. This helper cannot execute another product or
MCP, and does not install plugins or write activation/configuration files.
"""
from __future__ import annotations
import argparse
import copy
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

sys.dont_write_bytecode = True
PRODUCTS = ("code", "context", "contracts")
KEYS = {"installed", "skill_exposed", "mcp_exposed", "verified_cli"}
CANDIDATE_KEYS = {"statement", "kind", "origin", "evidence", "valid_from", "valid_until"}
MAX_JSON = 65_536


class ApplicationError(ValueError):
    pass


def parse_json(raw):
    if not isinstance(raw, (str, bytes)) or len(raw.encode("utf-8") if isinstance(raw, str) else raw) > MAX_JSON:
        raise ApplicationError("INPUT_TOO_LARGE")
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result: raise ApplicationError("DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ApplicationError("NONFINITE_JSON")))
    except (ValueError, UnicodeError, RecursionError):
        raise ApplicationError("INVALID_BOUNDED_JSON") from None


def observations(value):
    if not isinstance(value, dict) or set(value) != set(PRODUCTS):
        raise ApplicationError("CAPABILITIES_REQUIRE_CODE_CONTEXT_CONTRACTS")
    for item in value.values():
        if not isinstance(item, dict) or set(item) != KEYS or any(type(flag) is not bool for flag in item.values()):
            raise ApplicationError("CAPABILITIES_REQUIRE_FOUR_BOOLEAN_OBSERVATIONS")
    return copy.deepcopy(value)


def conversation_ledger(value=None):
    value = {"version": 1, "products": {}} if value is None else value
    if (not isinstance(value, dict) or set(value) != {"version", "products"}
            or type(value["version"]) is not int or value["version"] != 1
            or not isinstance(value["products"], dict) or set(value["products"]) - set(PRODUCTS)):
        raise ApplicationError("INVALID_CONVERSATION_LEDGER")
    for item in value["products"].values():
        if (not isinstance(item, dict) or set(item) != {"request_key", "status", "evidence"}
                or not isinstance(item["request_key"], str) or not 1 <= len(item["request_key"]) <= 160
                or not isinstance(item["status"], str) or item["status"] not in {"pending", "verified", "incomplete"} or not isinstance(item["evidence"], dict)):
            raise ApplicationError("INVALID_CONVERSATION_LEDGER_ENTRY")
    if len(json.dumps(value).encode()) > MAX_JSON: raise ApplicationError("LEDGER_TOO_LARGE")
    return copy.deepcopy(value)


def available(product, item):
    return (product == "context" or item["skill_exposed"]) and (item["mcp_exposed"] or item["verified_cli"])


def plan(capabilities, *, explicit_products=None, ledger=None):
    observed = observations(capabilities)
    receipt = conversation_ledger(ledger)
    explicit = list(dict.fromkeys(explicit_products or []))
    if any(product not in PRODUCTS for product in explicit): raise ApplicationError("UNKNOWN_PRODUCT")
    usable = [product for product in PRODUCTS if available(product, observed[product])]
    selected = explicit or usable
    routes = []
    for product in selected:
        item = observed[product]
        route = ("unavailable" if product not in usable else
                 "already_applied_recheck_freshness" if receipt["products"].get(product, {}).get("status") == "verified" else
                 "host_mcp_handoff" if item["mcp_exposed"] else
                 "verified_sibling_cli" if product == "context" else "host_cli_handoff")
        routes.append({"product": product, "route": route, "executionPerformed": False})
    return {"status": "planned", "activationStatus": "NOT_EXECUTED", "executionPerformed": False,
            "selectionBasis": "explicit_product" if explicit else "observed_availability", "availableCount": len(usable),
            "selectedProducts": selected, "observedAvailableProducts": usable, "routes": routes,
            "observations": observed, "ledger": receipt, "ledgerScope": "current_conversation_only"}


def trusted_bundle():
    raw = Path(__file__).absolute()
    root = raw.parents[3]
    for path in (raw, root / ".codex-plugin/plugin.json", root / "scripts/run.py",
                 root / "src/context_companion/store.py", root / "src/context_companion/local_cli.py"):
        for part in (path, *path.parents):
            if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
                raise ApplicationError("UNTRUSTED_BUNDLE_LINK")
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ApplicationError("UNTRUSTED_BUNDLE_FILE")
    if json.loads((root / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))["name"] != "context-ontology-companion":
        raise ApplicationError("WRONG_PRODUCT_BUNDLE")
    return root


def candidate_input(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_JSON:
        raise ApplicationError("CANDIDATE_MUST_BE_BOUNDED_REGULAR_FILE")
    with path.open("rb") as stream: value = parse_json(stream.read(MAX_JSON + 1))
    return value


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def run_context(capabilities, project_root, query, *, home=None, candidate=None, authorization=None,
                request_id=None, target_id=None, expected_revision=None, setup_authorized=False, ledger=None):
    observed = observations(capabilities)
    receipt = conversation_ledger(ledger)
    if not isinstance(query, str) or not query.strip() or len(query) > 500:
        raise ApplicationError("TASK_RELEVANT_QUERY_REQUIRED")
    if type(setup_authorized) is not bool: raise ApplicationError("INVALID_SETUP_AUTHORIZATION")
    if candidate is not None:
        if authorization != "explicit-user-request" or not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/#-]{0,159}", request_id):
            raise ApplicationError("CURRENT_EXPLICIT_SAVE_REQUEST_REQUIRED")
        if not isinstance(candidate, dict) or set(candidate) != CANDIDATE_KEYS:
            raise ApplicationError("INVALID_SELECTED_CANDIDATE")
    if (target_id is None) != (expected_revision is None) or (target_id is not None and candidate is None):
        raise ApplicationError("CORRECTION_REQUIRES_CONFIRMED_TARGET_CANDIDATE_REVISION")
    if expected_revision is not None and (type(expected_revision) is not int or expected_revision < 1):
        raise ApplicationError("INVALID_EXPECTED_REVISION")
    project = Path(project_root).expanduser().resolve()
    if not project.is_dir(): raise ApplicationError("PROJECT_ROOT_NOT_DIRECTORY")
    expected_scope = "project_" + hashlib.sha256(os.path.normcase(str(project)).encode("utf-8")).hexdigest()[:24]
    request_key = request_id or "read-" + fingerprint([str(project), query])[:24]
    result = {"status": "incomplete", "activationStatus": "NOT_EXECUTED", "executionPerformed": False,
              "operations": [], "issues": [], "ledger": receipt, "ledgerScope": "current_conversation_only",
              "taskContinuationRequired": True, "otherProductsExecuted": False,
              "persistentActivation": False, "projectConfigurationChanged": False,
              "globalConfigurationChanged": False, "storageInitialized": False}
    result.update(expectedScope=expected_scope, projectRoot=str(project))
    observation = observed["context"]
    if observation["mcp_exposed"]:
        receipt["products"]["context"] = {"request_key": request_key, "status": "pending", "evidence": {"expected_scope": expected_scope}}
        result.update(status="handoff_required", route="host_mcp_handoff", handoff={
            "product": "context", "executor": "host", "query": query,
            "expectedScope": expected_scope, "projectRoot": str(project),
            "scopePrecondition": "Call list_projects and verify its bound scope exactly equals expectedScope before any read or write. A mismatch remains pending; never choose another project implicitly.",
            "sequence": ["verify list_projects bound scope equals expectedScope", "search related current context", "check exact duplicates and ambiguity before writing",
                         "apply only the current explicitly authorized selected candidate or correction",
                         "fetch separately and verify scope, active revision, source and effective time",
                         "continue the original task with the retrieved evidence"],
            "candidate": candidate, "authorization": authorization, "request_id": request_id,
            "target_id": target_id, "expected_revision": expected_revision,
            "completionEvidence": "Actual current MCP responses; this handoff is not execution."})
        return result
    if not observation["verified_cli"]:
        receipt["products"]["context"] = {"request_key": request_key, "status": "pending", "evidence": {}}
        result.update(status="unavailable", route="unavailable")
        result["issues"].append("NO_OBSERVED_CONTEXT_EXECUTION_ROUTE")
        return result
    root = trusted_bundle()
    # Only same-product validation code is imported; all storage operations below
    # execute the bundled CLI as separate processes, never a target-project file.
    sys.path.insert(0, str(root / "src"))
    from context_companion.store import validate_candidate
    if candidate is not None: candidate = validate_candidate(candidate)
    args = ["--project-root", str(project)] + (["--home", str(home)] if home is not None else [])
    result["route"] = "verified_sibling_cli"

    def call(operation, extra=None, payload=None):
        command = [sys.executable, "-I", "-B", str(root / "scripts/run.py"), "local-" + operation, *args, *(extra or [])]
        result["executionPerformed"] = True
        proc = subprocess.run(command, input=json.dumps(payload, ensure_ascii=False) if payload is not None else None,
                              capture_output=True, text=True, encoding="utf-8", timeout=30)
        if proc.returncode:
            try: error = json.loads(proc.stderr)["error"]
            except (ValueError, KeyError): error = "BUNDLED_CLI_FAILED"
            result["operations"].append({"operation": operation, "status": "failed", "error": error})
            raise ApplicationError(error)
        value = json.loads(proc.stdout)
        result["operations"].append({"operation": operation, "status": "returned", "result": value})
        if value.get("authorization_mode") != "os_account_explicit_request" or value.get("human_review_performed") is not False:
            raise ApplicationError("LOCAL_PROFILE_RECEIPT_MISMATCH")
        if value.get("scope") != expected_scope: raise ApplicationError("LOCAL_SCOPE_RESPONSE_MISMATCH")
        return value

    def fetch_checked(record_id, expected=None):
        response = call("fetch", ["--id", record_id])
        record = response["result"]
        if record["scope"] != result["scope"] or record["status"] != "active":
            raise ApplicationError("RECORD_SCOPE_OR_LIFECYCLE_CHANGED")
        if expected is not None and any(record[key] != value for key, value in expected.items()):
            raise ApplicationError("SELECTED_RECORD_READBACK_MISMATCH")
        return record

    try:
        try:
            searched = call("search", ["--query", query])
        except ApplicationError as error:
            if str(error) != "LOCAL_CLI_NOT_INITIALIZED_USE_LOCAL_INIT" or not setup_authorized: raise
            call("init")
            result["storageInitialized"] = True
            searched = call("search", ["--query", query])
        result["scope"] = searched["scope"]
        relevant = searched["result"]["records"]
        initial_pack = call("pack", ["--query", query, "--max-chars", "100000"])["result"]
        if initial_pack["status"] != "complete": raise ApplicationError("CONTEXT_PACK_INCOMPLETE")
        result["contextPack"] = initial_pack
        if candidate is None:
            if not relevant:
                result["status"] = "needs_input"; result["issues"].append("NO_CURRENT_MATCH_FOR_TASK_QUERY")
                receipt["products"]["context"] = {"request_key": request_key, "status": "pending", "evidence": {"scope": result["scope"]}}
                return result
            records = [fetch_checked(row["id"], {key: row[key] for key in CANDIDATE_KEYS}) for row in relevant]
            result["outcome"] = "retrieved"
        else:
            all_rows = call("search", ["--query", ""])["result"]["records"]
            exact = [row for row in all_rows if all(row[key] == value for key, value in candidate.items())]
            normalized = candidate["statement"].strip().casefold()
            similar = [row for row in all_rows if row not in exact and
                       (row in relevant or difflib.SequenceMatcher(None, normalized, row["statement"].strip().casefold()).ratio() >= 0.65)]
            conflicts = initial_pack["pack"]["contradictions"]
            if len(exact) > 1 or (target_id is None and (similar or conflicts)):
                result.update(status="pending_target_choice", choices=[{"id": row["id"], "revision": row["revision"], "statement": row["statement"]} for row in exact + similar])
                result["issues"].append("AMBIGUOUS_SIMILAR_OR_CONFLICTING_CONTEXT_REQUIRES_USER_CHOICE")
                receipt["products"]["context"] = {"request_key": request_key, "status": "pending", "evidence": {"scope": result["scope"]}}
                return result
            if exact and target_id is None:
                records = [fetch_checked(exact[0]["id"], candidate)]
                result["outcome"] = "reused_exact_candidate"
            else:
                if target_id is not None:
                    target_response = call("fetch", ["--id", target_id])
                    target = target_response["result"]
                    if target["scope"] != result["scope"]: raise ApplicationError("RECORD_SCOPE_OR_LIFECYCLE_CHANGED")
                    if target["status"] == "active" and target["revision"] != expected_revision:
                        raise ApplicationError("REVISION_CONFLICT")
                    # An inactive target can only succeed as the exact same
                    # runtime idempotency-key retry; a fresh correction fails
                    # the Store's lifecycle/revision checks without mutation.
                # Recheck current membership immediately before mutation. A
                # changed query is evidence to reread, never permission to merge.
                fresh = call("search", ["--query", ""])["result"]["records"]
                if fresh != all_rows: raise ApplicationError("CONTEXT_CHANGED_REQUERY_REQUIRED")
                extra = ["--input", "-", "--authorization", authorization, "--request-id", request_id]
                if target_id is not None: extra += ["--id", target_id, "--expected-revision", str(expected_revision)]
                saved = call("update" if target_id is not None else "save", extra, candidate)["result"]
                if saved["state"] != "applied" or not saved.get("record_id"): raise ApplicationError("WRITE_NOT_APPLIED")
                result["writeReceipt"] = saved
                records = [fetch_checked(saved["record_id"], candidate)]
                result["outcome"] = "corrected" if target_id is not None else "saved"
        final = call("search", ["--query", query])["result"]["records"]
        if candidate is None and final != relevant: raise ApplicationError("CONTEXT_CHANGED_REQUERY_REQUIRED")
        final_pack = call("pack", ["--query", query, "--max-chars", "100000"])["result"]
        if final_pack["status"] != "complete": raise ApplicationError("CONTEXT_PACK_INCOMPLETE")
        if candidate is None and final_pack != initial_pack: raise ApplicationError("CONTEXT_CHANGED_REQUERY_REQUIRED")
        result["contextPack"] = final_pack
        for record in records:
            latest = fetch_checked(record["id"], {key: record[key] for key in CANDIDATE_KEYS})
            if latest != record: raise ApplicationError("CONTEXT_CHANGED_REQUERY_REQUIRED")
        now = datetime.now(timezone.utc)
        current_records = [record for record in records if
            datetime.strptime(record["valid_from"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) <= now and
            (record["valid_until"] is None or now < datetime.strptime(record["valid_until"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc))]
        result["verifiedRecords"] = records
        result["continuationEvidence"] = {"query": query, "records": current_records,
            "contextPack": final_pack,
            "instruction": "Use this retrieved evidence to continue the original task while preserving effective time and sources; this helper has not completed that task."}
        evidence = {"scope": result["scope"], "query_sha256": fingerprint(query),
                    "records": [{"id": row["id"], "revision": row["revision"], "candidate_sha256": fingerprint({key: row[key] for key in CANDIDATE_KEYS})} for row in records],
                    "checked_at_utc": datetime.now(timezone.utc).isoformat(), "human_review_performed": False}
        prior = receipt["products"].get("context", {})
        result["previousReceiptMatch"] = prior.get("request_key") == request_key and prior.get("evidence", {}).get("records") == evidence["records"]
        if len(current_records) != len(records):
            receipt["products"]["context"] = {"request_key": request_key, "status": "pending", "evidence": evidence}
            result.update(status="stored_not_current", activationStatus="PENDING_EFFECTIVE_TIME")
            result["issues"].append("SELECTED_RECORD_OUTSIDE_CURRENT_VALID_TIME")
            return result
        receipt["products"]["context"] = {"request_key": request_key, "status": "verified", "evidence": evidence}
        result.update(status="evidence_verified", activationStatus="CONTEXT_EVIDENCE_VERIFIED")
    except (ApplicationError, OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        result["issues"].append(str(error) if isinstance(error, ApplicationError) else "CONTEXT_EXECUTION_OR_RESPONSE_FAILED")
        receipt["products"]["context"] = {"request_key": request_key, "status": "incomplete", "evidence": {}}
    return result


def main():
    if sys.version_info < (3, 11): raise SystemExit("Python 3.11+ required")
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "run-context"):
        p = commands.add_parser(name)
        p.add_argument("--capabilities", required=True)
        p.add_argument("--ledger")
        if name == "plan": p.add_argument("--explicit-product", choices=PRODUCTS, action="append", default=[])
        else:
            p.add_argument("--project-root", required=True); p.add_argument("--query", required=True)
            p.add_argument("--home"); p.add_argument("--input"); p.add_argument("--authorization", choices=["explicit-user-request"])
            p.add_argument("--request-id"); p.add_argument("--target-id"); p.add_argument("--expected-revision", type=int)
            p.add_argument("--setup-authorized", action="store_true")
    args = parser.parse_args()
    try:
        capabilities = parse_json(args.capabilities); ledger = parse_json(args.ledger) if args.ledger else None
        if args.command == "plan": value = plan(capabilities, explicit_products=args.explicit_product, ledger=ledger)
        else: value = run_context(capabilities, args.project_root, args.query, home=args.home,
                    candidate=candidate_input(args.input) if args.input else None, authorization=args.authorization,
                    request_id=args.request_id, target_id=args.target_id, expected_revision=args.expected_revision,
                    setup_authorized=args.setup_authorized, ledger=ledger)
    except (ApplicationError, OSError, ValueError) as error:
        value = {"status": "invalid_input", "activationStatus": "NOT_EXECUTED", "executionPerformed": False,
                 "issues": [str(error) if isinstance(error, ApplicationError) else "INVALID_INPUT_OR_LOCAL_PATH"]}
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return 0 if value["status"] in {"planned", "handoff_required", "evidence_verified"} else 1


if __name__ == "__main__": raise SystemExit(main())
