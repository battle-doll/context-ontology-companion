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
required=["README.md","README.ko.md","README.ja.md","README.zh-CN.md","README.ru.md","LICENSE","SECURITY.md","PRIVACY.md","SUPPORT.md","CONTRIBUTING.md","CHANGELOG.md",".github/workflows/ci.yml","release-state.json"]
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
if submission_path.exists():
    submission=json.loads(submission_path.read_text(encoding="utf-8"))
    actual=json.loads(subprocess.check_output([sys.executable,str(ROOT/"scripts/run.py"),"tools"],text=True,encoding="utf-8"))
    actual=actual["tools"] if isinstance(actual,dict) else actual
    if set(submission["tools"])!={t["name"] for t in actual}: errors.append("submission tool name mismatch")
    for tool in actual:
        if not tool.get("inputSchema") or not tool.get("outputSchema"): errors.append("missing schema: "+tool["name"])
        declared=submission["tools"].get(tool["name"],{}).get("annotations",{})
        if declared!={k:tool["annotations"].get(k) for k in ("readOnlyHint","destructiveHint","openWorldHint")}: errors.append("submission hint mismatch: "+tool["name"])
    if len(submission.get("test_cases",[]))!=5 or len(submission.get("negative_test_cases",[]))!=3: errors.append("submission case count")
if errors: raise SystemExit("\n".join(errors))
print(json.dumps({"status":"PASS","scope":"LOCAL_OSS_STRUCTURE_NOT_PUBLIC_APPROVAL","local_links":links,"secret_scan":"bounded_pattern_scan_not_comprehensive"}))
