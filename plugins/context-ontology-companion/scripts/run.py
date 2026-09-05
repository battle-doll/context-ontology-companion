#!/usr/bin/env python3
"""Cross-platform local CLI; demo uses synthetic approval in a temporary DB."""
import argparse
import getpass
import json
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True
if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11 or newer is required; no operation was performed.")
# JSON is UTF-8 even when Windows redirects output through a legacy code page.
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"vendor"))
from context_companion.store import Store, Principal, ContextError
from context_companion.tools import TOOLS


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("tools")
    sub.add_parser("demo")
    init=sub.add_parser("init-local",help="Human operator only: initialize private local storage with a password prompt")
    init.add_argument("--home",type=Path,required=True)
    init.add_argument("--project",required=True)
    init.add_argument("--username",required=True)
    serve=sub.add_parser("review-server",help="Human operator only: serve authenticated review on IPv4 loopback")
    serve.add_argument("--home",type=Path,required=True)
    serve.add_argument("--port",type=int,default=8765)
    mcp=sub.add_parser("stdio",help="Local MCP with a trusted operator-configured principal")
    mcp.add_argument("--home",type=Path,required=True)
    maintenance=sub.add_parser("purge-expired",help="Local operator maintenance: remove expired proposal payloads")
    maintenance.add_argument("--home",type=Path,required=True)
    args=parser.parse_args()
    if args.command=="tools":
        print(json.dumps({"tools":TOOLS},ensure_ascii=False,indent=2))
    elif args.command=="demo":
        from companion_contracts import validate_artifact
        candidate=json.loads((ROOT/"examples/decision.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="context-synthetic-") as tmp:
            path=Path(tmp).resolve()/"context.sqlite3"
            store=Store(path); principal=Principal("synthetic-reviewer")
            store.provision_project(principal,"synthetic-demo")
            pending=store.prepare(principal,"synthetic-demo","create","synthetic-demo-create",candidate)
            review=store.review(principal,pending["proposal_id"])
            applied=store.approve(principal,pending["proposal_id"],review["digest"],review["nonce"])
            store.close()
            reopened=Store(path)
            recovered=reopened.fetch(principal,applied["record_id"])
            validated=validate_artifact(reopened.export(principal,"synthetic-demo"))
            reopened.close()
            print(json.dumps({"status":"local_synthetic_demo","approval":"simulated_not_human_evidence","new_store_session_recovered":recovered,"contract_validation":validated,"chatgpt_e2e":"not_run"},ensure_ascii=False,indent=2))
    elif args.command=="init-local":
        from context_companion.review import init_local
        if not sys.stdin.isatty(): raise ContextError("INTERACTIVE_OPERATOR_REQUIRED")
        if args.home.resolve().is_relative_to(ROOT): raise ContextError("STORAGE_MUST_BE_OUTSIDE_REPOSITORY")
        password=getpass.getpass("Choose local review password (never paste into chat): ")
        if password!=getpass.getpass("Confirm password: "): raise ContextError("PASSWORD_MISMATCH")
        init_local(args.home,args.project,args.username,password)
        print("Private local configuration created. No host or public registration occurred.")
    elif args.command=="review-server":
        from context_companion.review import serve
        serve(args.home,args.port)
    elif args.command=="stdio":
        from context_companion.mcp import serve_stdio
        serve_stdio(args.home)
    elif args.command=="purge-expired":
        from context_companion.review import load_local
        path,_=load_local(args.home)
        store=Store(path)
        try: store.purge_expired()
        finally: store.close()
        print(json.dumps({"expired_proposal_payloads":"purged"}))


if __name__=="__main__":
    try: main()
    except ContextError as exc:
        print(json.dumps({"error":exc.code}),file=sys.stderr)
        raise SystemExit(1)
