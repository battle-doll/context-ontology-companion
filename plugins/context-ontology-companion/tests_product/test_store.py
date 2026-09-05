import copy
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"src"),str(ROOT/"vendor")]
from context_companion.store import Store,Principal,ContextError,canonical
from context_companion.tools import dispatch,TOOLS
from context_companion.mcp import Session,parse


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="context-tests-")
        self.path=Path(self.tmp.name).resolve()/"context.sqlite3"
        self.now=datetime(2026,9,5,tzinfo=timezone.utc)
        self.store=Store(self.path,lambda:self.now)
        self.p=Principal("alice"); self.other=Principal("bob")
        for p,project in [(self.p,"project"),(self.p,"different"),(self.other,"project")]: self.store.provision_project(p,project)
        self.candidate=json.loads((ROOT/"examples/decision.json").read_text(encoding="utf-8"))

    def tearDown(self):
        self.store.close(); self.tmp.cleanup()

    def approve(self, pending):
        review=self.store.review(self.p,pending["proposal_id"])
        return self.store.approve(self.p,pending["proposal_id"],review["digest"],review["nonce"])

    def create(self, candidate=None, key="create"):
        return self.approve(self.store.prepare(self.p,"project","create",key,candidate or self.candidate))["record_id"]

    def test_recover_in_new_process_with_provenance(self):
        rid=self.create()
        code="from context_companion.store import Store,Principal; import json,sys; s=Store(sys.argv[1]); print(json.dumps(s.fetch(Principal('alice'),sys.argv[2]))); s.close()"
        import os
        result=subprocess.run([sys.executable,"-c",code,str(self.path),rid],env={**os.environ,"PYTHONPATH":str(ROOT/"src")},text=True,capture_output=True,check=True)
        data=json.loads(result.stdout)
        self.assertEqual(data["statement"],self.candidate["statement"])
        self.assertEqual(data["evidence"],self.candidate["evidence"])
        self.assertEqual(data["origin"],"user_asserted")

    def test_export_consumed_by_standalone_contract_validator(self):
        from companion_contracts import validate_artifact
        self.create()
        result=validate_artifact(self.store.export(self.p,"project"))
        self.assertEqual(result["status"],"valid",result)

    def test_export_aggregate_limit_fails_without_partial_artifact(self):
        c=copy.deepcopy(self.candidate)
        c["evidence"]=[{**c["evidence"][0],"id":"source-"+str(i)} for i in range(8)]
        for i in range(126): self.create(c,"aggregate-"+str(i))
        with self.assertRaisesRegex(ContextError,"EXPORT_CONTRACT_LIMIT_OR_MISMATCH"):
            self.store.export(self.p,"project")
        self.assertEqual(len(self.store.search(self.p,"project")["records"]),126)

    def test_readonly_tools_leave_database_identical(self):
        import hashlib
        rid=self.create()
        pending=self.store.prepare(self.p,"project","revoke","review-only",target=rid,expected_revision=1)
        cases={"list_projects":{},"search":{"project_id":"project"},"fetch":{"id":rid},"get_context_history":{"id":rid},"build_context_pack":{"project_id":"project"},"get_change_status":{"proposal_id":pending["proposal_id"]},"export_context":{"project_id":"project"}}
        before=hashlib.sha256(self.path.read_bytes()).hexdigest()
        for name,args in cases.items():
            result=dispatch(self.store,self.p,name,args)
            try:
                from jsonschema import Draft202012Validator
            except ImportError: pass
            else:
                descriptor=next(t for t in TOOLS if t["name"]==name)
                Draft202012Validator(descriptor["inputSchema"]).validate(args)
                Draft202012Validator(descriptor["outputSchema"]).validate(result)
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),before)

    def test_concurrent_apply_exactly_one_commits(self):
        from concurrent.futures import ThreadPoolExecutor
        import threading
        pending=self.store.prepare(self.p,"project","create","race",self.candidate)
        review=self.store.review(self.p,pending["proposal_id"])
        barrier=threading.Barrier(2)
        def apply():
            s=Store(self.path,lambda:self.now)
            try:
                barrier.wait(timeout=5)
                s.approve(self.p,pending["proposal_id"],review["digest"],review["nonce"])
                return "applied"
            except ContextError as exc: return exc.code
            finally: s.close()
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures=[executor.submit(apply) for _ in range(2)]
            results=[f.result(timeout=10) for f in futures]
        self.assertEqual(sorted(results),["APPROVAL_NOT_PENDING","applied"])
        self.assertEqual(len(self.store.search(self.p,"project")["records"]),1)

    def test_scope_contract_and_single_time_snapshot(self):
        with self.assertRaisesRegex(ContextError,"INVALID_PROJECT_ID"):
            self.store.provision_project(self.p,"Research Project")
        self.create({**self.candidate,"valid_from":"2026-09-05T00:00:01Z"})
        count=[0]
        def advancing_clock():
            count[0]+=1
            return self.now+timedelta(seconds=count[0]-1)
        self.store.clock=advancing_clock
        result=self.store.pack(self.p,"project","",10000)
        self.assertEqual(result["pack"]["records"],[])
        self.assertEqual(count[0],1)

    def test_draft_not_retrieved_and_no_approval_tool(self):
        p=self.store.prepare(self.p,"project","create","k",self.candidate)
        self.assertEqual(self.store.search(self.p,"project")["records"],[])
        self.assertNotIn("nonce",canonical(p))
        self.assertNotIn("approve",[t["name"] for t in TOOLS])
        for forbidden in [{"approved":True},{"tenant_id":"alice"},{"known_at":"2020"}]:
            with self.assertRaises(ContextError): dispatch(self.store,self.p,"search",{"project_id":"project",**forbidden})

    def test_idempotency_conflict_and_no_duplicate(self):
        pending=self.store.prepare(self.p,"project","create","k",self.candidate)
        self.assertEqual(pending,self.store.prepare(self.p,"project","create","k",self.candidate))
        altered={**self.candidate,"statement":"different"}
        with self.assertRaisesRegex(ContextError,"IDEMPOTENCY_CONFLICT"): self.store.prepare(self.p,"project","create","k",altered)
        applied=self.approve(pending)
        self.assertEqual(applied,self.store.prepare(self.p,"project","create","k",self.candidate))
        self.assertEqual(len(self.store.search(self.p,"project")["records"]),1)

    def test_scope_and_principal_isolation_all_reads(self):
        rid=self.create()
        self.assertEqual(self.store.search(self.other,"project")["records"],[])
        self.assertEqual(self.store.export(self.other,"project")["payload"]["decisions"],[])
        for f in [self.store.fetch,self.store.history]:
            with self.assertRaisesRegex(ContextError,"NOT_FOUND_OR_FORBIDDEN"): f(self.other,rid)
        with self.assertRaisesRegex(ContextError,"NOT_FOUND_OR_FORBIDDEN"): self.store.prepare(self.p,"different","erase","erase",target=rid,expected_revision=1)

    def test_digest_nonce_expiry_and_replay(self):
        pending=self.store.prepare(self.p,"project","create","k",self.candidate); pid=pending["proposal_id"]
        r=self.store.review(self.p,pid)
        for d,n in [("bad",r["nonce"]),(r["digest"],"bad")]:
            with self.assertRaisesRegex(ContextError,"APPROVAL_MISMATCH"): self.store.approve(self.p,pid,d,n)
        with self.assertRaises(ContextError): self.store.review(self.other,pid)
        self.now+=timedelta(minutes=16)
        with self.assertRaisesRegex(ContextError,"APPROVAL_NOT_PENDING"): self.store.approve(self.p,pid,r["digest"],r["nonce"])
        self.store.purge_expired()
        self.assertEqual(self.store.db.execute("SELECT payload FROM proposals WHERE id=?",(pid,)).fetchone()[0],"{}")
        self.now-=timedelta(minutes=16)
        p2=self.store.prepare(self.p,"project","create","new",self.candidate); rr=self.store.review(self.p,p2["proposal_id"])
        self.approve(p2)
        with self.assertRaises(ContextError): self.store.approve(self.p,p2["proposal_id"],rr["digest"],rr["nonce"])

    def test_stale_revision_rolls_back(self):
        rid=self.create()
        first=self.store.prepare(self.p,"project","supersede","one",self.candidate,rid,1)
        second=self.store.prepare(self.p,"project","supersede","two",self.candidate,rid,1)
        self.approve(first)
        with self.assertRaisesRegex(ContextError,"REVISION_CONFLICT"): self.approve(second)
        self.assertEqual(len(self.store.search(self.p,"project")["records"]),1)

    def test_valid_time_and_inference_not_promoted(self):
        c=copy.deepcopy(self.candidate); c["origin"]="model_inferred"; c["evidence"][0]["origin"]="model_inferred"
        rid=self.create(c)
        self.assertEqual(self.store.fetch(self.p,rid)["origin"],"model_inferred")
        future={**self.candidate,"valid_from":"2027-01-01T00:00:00Z"}
        self.create(future,"future")
        self.assertEqual(len(self.store.search(self.p,"project")["records"]),1)
        for bad in [{**future,"valid_until":"2026-01-01T00:00:00Z"},{**future,"valid_from":"2026-01-01"}]:
            with self.assertRaises(ContextError): self.store.prepare(self.p,"project","create","bad",bad)

    def test_constraint_conflict_and_unicode_budget_atomic(self):
        c={**self.candidate,"kind":"decision","statement":"Use option A 한글 🔒"}
        rid=self.create(c)
        opposite={**c,"statement":"Use option B"}
        self.approve(self.store.prepare(self.p,"project","contradict","opposite",opposite,rid,1))
        self.create({**self.candidate,"statement":"mandatory unrelated constraint"},"constraint")
        result=self.store.pack(self.p,"project","option A",10000)
        self.assertEqual(len(result["pack"]["records"]),3)
        self.assertEqual(len(result["pack"]["contradictions"]),1)
        self.assertEqual(result["required_chars"],len(canonical(result)))
        small=self.store.pack(self.p,"project","option A",result["required_chars"]-1)
        self.assertEqual(small["status"],"insufficient_budget"); self.assertIsNone(small["pack"])

    def test_erasure_scrubs_history_pending_and_restart(self):
        rid=self.create()
        self.store.prepare(self.p,"project","supersede","pending-copy",self.candidate,rid,1)
        pending=self.store.prepare(self.p,"project","erase","erase",target=rid,expected_revision=1)
        self.approve(pending)
        for f in [self.store.fetch,self.store.history]:
            with self.assertRaises(ContextError): f(self.p,rid)
        self.assertEqual(self.store.search(self.p,"project")["records"],[])
        self.store.close(); self.store=Store(self.path)
        dumped="\n".join(self.store.db.iterdump())
        self.assertNotIn(self.candidate["statement"],dumped)
        self.assertNotIn(self.candidate["evidence"][0]["locator"],dumped)
        self.assertEqual(self.store.export(self.p,"project")["payload"]["decisions"],[])

    def test_sensitive_input_and_schema_rejected_without_echo(self):
        for c in [{**self.candidate,"approved":True},{**self.candidate,"statement":"sk-"+"x"*20},{**self.candidate,"statement":"x"*4001}]:
            with self.assertRaises(ContextError) as exc: self.store.prepare(self.p,"project","create","bad",c)
            self.assertNotIn(c["statement"],str(exc.exception))

    def test_rpc_lifecycle_and_tool_errors(self):
        s=Session(self.store,self.p)
        self.assertIn("error",s.handle({"jsonrpc":"2.0","id":1,"method":"tools/list"}))
        s.handle({"jsonrpc":"2.0","id":2,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"synthetic","version":"1"}}})
        self.assertIsNone(s.handle({"jsonrpc":"2.0","method":"notifications/initialized"}))
        result=s.handle({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"fetch","arguments":{"id":"missing"}}})
        self.assertTrue(result["result"]["isError"])
        for raw in [b'{"a":1,"a":2}',b'{"n":NaN}',b'{"n":1e999}',b'{"id":"\\ud800"}',b'['*25+b']'*25]:
            with self.assertRaises(ValueError): parse(raw)


if __name__=="__main__": unittest.main()
