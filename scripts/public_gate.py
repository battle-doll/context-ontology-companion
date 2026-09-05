#!/usr/bin/env python3
"""Local OSS source checks, not a public-release approval."""
from pathlib import Path
import json
import re
import subprocess
import sys
from urllib.parse import unquote,urlsplit

ROOT=Path(__file__).resolve().parents[1]
IGNORE={".git",".venv","__pycache__","dist","build",".pytest_cache"}
required=["README.md","README.ko.md","README.ja.md","README.zh-CN.md","README.ru.md","LICENSE","SECURITY.md","PRIVACY.md","SUPPORT.md","CONTRIBUTING.md","CHANGELOG.md",".github/workflows/ci.yml","release-state.json","chatgpt-app-submission.json","mcp-tool-catalog.json","docs/MCP_PROFILES.md"]
errors=["missing: "+p for p in required if not (ROOT/p).is_file()]
links=0
for p in sorted(ROOT.rglob("*")):
    if any(x in IGNORE for x in p.relative_to(ROOT).parts) or p.name in {".DS_Store","Thumbs.db"} or p.suffix==".pyc": continue
    if p.is_symlink(): errors.append("symlink: "+str(p.relative_to(ROOT)))
    if not p.is_file(): continue
    if p.suffix in {".db",".sqlite",".sqlite3",".pem",".key"} or p.name.startswith(".env"): errors.append("private file: "+str(p.relative_to(ROOT)))
    if p.suffix==".json": json.loads(p.read_text(encoding="utf-8"))
    if p.suffix not in {".md",".py",".json",".yml",".toml",".txt"}: continue
    text=p.read_text(encoding="utf-8")
    if re.search(r"gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",text): errors.append("possible secret: "+str(p.relative_to(ROOT)))
    if p.suffix!=".md": continue
    fenced=False
    for line in text.splitlines():
        if line.lstrip().startswith("```"): fenced=not fenced; continue
        if fenced: continue
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)",line):
            target=target.strip("<>")
            if urlsplit(target).scheme or target.startswith("#"): continue
            local=unquote(target.split("#")[0].split("?")[0])
            if not local: continue
            links+=1; resolved=(p.parent/local).resolve()
            if not resolved.is_relative_to(ROOT) or not resolved.exists(): errors.append("broken link: "+str(p.relative_to(ROOT))+" -> "+local)
    if fenced: errors.append("unclosed fence: "+str(p.relative_to(ROOT)))
submission_path=ROOT/"chatgpt-app-submission.json"
profiles={}
for profile in ("review", "local"):
    descriptor=json.loads(subprocess.check_output([sys.executable,str(ROOT/"scripts/run.py"),"tools","--profile",profile],text=True,encoding="utf-8"))
    actual=descriptor["tools"]
    profiles[profile]=actual
    if len({tool["name"] for tool in actual})!=len(actual): errors.append("duplicate tool: "+profile)
    for tool in actual:
        if not tool.get("inputSchema") or not tool.get("outputSchema"): errors.append("missing schema: "+profile+":"+tool["name"])
        hints=tool.get("annotations",{})
        if any(type(hints.get(key)) is not bool for key in ("readOnlyHint","destructiveHint","openWorldHint")):
            errors.append("missing explicit hint: "+profile+":"+tool["name"])
    if profile=="local":
        catalog=ROOT/"mcp-tool-catalog.json"
        if catalog.exists() and json.loads(catalog.read_text(encoding="utf-8"))!=descriptor:
            errors.append("local MCP catalog differs from runtime; regenerate with tools --profile local")
        if descriptor.get("authorization_mode")!="os_account_explicit_request" or descriptor.get("human_review_performed") is not False:
            errors.append("local catalog authority mismatch")
        writes={"save_context","update_context","contradict_context","revoke_context","delete_context"}
        expected=writes|{"list_projects","search","fetch","get_context_history","build_context_pack","export_context","get_change_status"}
        if {tool["name"] for tool in actual}!=expected: errors.append("local profile tool set mismatch")
        for tool in actual:
            name=tool["name"]; schema=tool["inputSchema"]
            if "project_id" in schema.get("properties",{}): errors.append("local scope must be server-bound: "+name)
            if name in writes and (not {"authorization","request_id"}<=set(schema.get("required",[])) or schema.get("properties",{}).get("authorization")!={"const":"explicit-user-request"}):
                errors.append("local write lacks explicit-request input: "+name)
            if tool["annotations"]!={"readOnlyHint":name not in writes,"destructiveHint":name in {"update_context","revoke_context","delete_context"},"openWorldHint":False}:
                errors.append("local write hint mismatch: "+name)
if submission_path.exists():
    submission=json.loads(submission_path.read_text(encoding="utf-8"))
    actual=profiles["review"]
    if set(submission["tools"])!={t["name"] for t in actual}: errors.append("submission tool name mismatch")
    for tool in actual:
        if not tool.get("inputSchema") or not tool.get("outputSchema"): errors.append("missing schema: "+tool["name"])
        declared=submission["tools"].get(tool["name"],{}).get("annotations",{})
        if declared!={k:tool["annotations"].get(k) for k in ("readOnlyHint","destructiveHint","openWorldHint")}: errors.append("submission hint mismatch: "+tool["name"])
    if len(submission.get("test_cases",[]))!=5 or len(submission.get("negative_test_cases",[]))!=3: errors.append("submission case count")
    if "prepare_context_change" not in submission["tools"] or set(submission["tools"]) & {"save_context","update_context","contradict_context","revoke_context","delete_context"}:
        errors.append("authenticated-review submission must remain separate from local direct-write profile")
if errors: raise SystemExit("\n".join(errors))
print(json.dumps({"status":"PASS","scope":"LOCAL_OSS_STRUCTURE_NOT_PUBLIC_APPROVAL","local_links":links,"tool_profiles":{name:len(tools) for name,tools in profiles.items()},"secret_scan":"bounded_pattern_scan_not_comprehensive"}))
