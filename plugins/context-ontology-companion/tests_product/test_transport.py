from pathlib import Path
import copy
import json
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"src"),str(ROOT/"vendor")]
from context_companion.review import init_local,load_local
from context_companion.store import Store
from context_companion.tools import TOOLS
from context_companion.mcp import Session


class TransportTests(unittest.TestCase):
    def test_subprocess_stdio_rejects_hostile_input_and_recovers(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp).resolve()/"private"
            init_local(home,"synthetic-project","synthetic-operator","synthetic-test-password-only")
            messages=[b'{"jsonrpc":"2.0","id":"\\ud800","method":"ping"}',b'{"jsonrpc":"2.0","id":1e999,"method":"ping"}',json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"synthetic","version":"1"}}}).encode(),b'{"jsonrpc":"2.0","method":"notifications/initialized"}',b'{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{"cursor":null,"_meta":{}}}',b'{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_projects","arguments":{}}}']
            result=subprocess.run([sys.executable,str(ROOT/"scripts/run.py"),"stdio","--home",str(home)],input=b"\n".join(messages)+b"\n",capture_output=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(result.stderr,b"")
            output=[json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual([r["error"]["code"] for r in output[:2]],[-32700,-32700])
            self.assertEqual(len(output[3]["result"]["tools"]),8)
            self.assertEqual(output[4]["result"]["structuredContent"],{"projects":["synthetic-project"]})

    @staticmethod
    def ready_session():
        # Discovery must not require access to a store or approval principal.
        session=Session(None,None)
        initialized=session.handle({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"synthetic","version":"1"}}})
        if "error" in initialized: raise AssertionError(initialized)
        session.handle({"jsonrpc":"2.0","method":"notifications/initialized"})
        return session

    def test_tools_list_accepts_initial_page_metadata_and_null_serialization(self):
        session=self.ready_session()
        accepted=[{},None,{"cursor":None},{"cursor":""},{"_meta":{}},
                  {"cursor":None,"_meta":{"progressToken":"synthetic-request"}},
                  {"cursor":"","_meta":{"client.example/trace":"synthetic"}}]
        requests=[{"jsonrpc":"2.0","id":2,"method":"tools/list"}]
        requests += [{"jsonrpc":"2.0","id":index+3,"method":"tools/list","params":params} for index,params in enumerate(accepted)]
        for request in requests:
            with self.subTest(params=request.get("params","omitted")):
                response=session.handle(request)
                self.assertNotIn("error",response)
                self.assertEqual(response["result"],{"tools":TOOLS})
                self.assertNotIn("nextCursor",response["result"])

    def test_tools_list_rejects_continuation_bad_types_and_unknown_keys(self):
        session=self.ready_session()
        rejected=[{"cursor":"next-page"},{"cursor":0},{"cursor":False},
                  {"cursor":[]},{"cursor":{}},{"_meta":None},{"_meta":[]},
                  {"_meta":"token"},{"_meta":1},{"_meta":False},
                  {"unknown":"value"},[],"",False,0]
        for index,params in enumerate(rejected):
            with self.subTest(params=params):
                response=session.handle({"jsonrpc":"2.0","id":index+2,"method":"tools/list","params":params})
                self.assertEqual(response["error"]["code"],-32602)
                self.assertNotIn("result",response)
        recovered=session.handle({"jsonrpc":"2.0","id":100,"method":"tools/list","params":{"cursor":None,"_meta":{}}})
        self.assertEqual(recovered["result"],{"tools":TOOLS})

    def test_tools_list_initial_page_keeps_session_readiness_gate(self):
        session=Session(None,None)
        response=session.handle({"jsonrpc":"2.0","id":1,"method":"tools/list","params":{"cursor":None,"_meta":{}}})
        self.assertEqual(response["error"]["code"],-32000)
        self.assertNotIn("result",response)

    def test_nested_output_schema_rejects_missing_provenance(self):
        try: from jsonschema import Draft202012Validator
        except ImportError: self.skipTest("optional jsonschema dev validator unavailable")
        tool=next(t for t in TOOLS if t["name"]=="search")
        bad={"records":[{"statement":"unattributed"}],"knowledge_time":"current","external_verification":"not_checked"}
        self.assertTrue(list(Draft202012Validator(tool["outputSchema"]).iter_errors(bad)))
        pack_tool=next(t for t in TOOLS if t["name"]=="build_context_pack")
        self.assertTrue(list(Draft202012Validator(pack_tool["outputSchema"]).iter_errors({"status":"complete","required_chars":1,"pack":None})))


if __name__=="__main__": unittest.main()
