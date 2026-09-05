#!/usr/bin/env python3
"""Build a deterministic versioned source ZIP; never uploads or publishes."""
from pathlib import Path
import hashlib
import json
import zipfile
ROOT=Path(__file__).resolve().parents[1]
IGNORE={".git",".venv","__pycache__","dist","build",".pytest_cache","user-data","runtime-data","logs","exports","backups"}
out=ROOT/"dist"; out.mkdir(exist_ok=True)
version=json.loads((ROOT/".codex-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
target=out/(ROOT.name+"-"+version+"-source.zip")
with zipfile.ZipFile(target,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(ROOT.rglob("*")):
        rel=p.relative_to(ROOT)
        if any(x in IGNORE for x in rel.parts) or p.name in {".DS_Store","Thumbs.db"} or p.suffix==".pyc": continue
        if p.is_symlink(): raise SystemExit("Symlink not allowed")
        if not p.is_file(): continue
        if p.name.startswith(".env") or p.suffix in {".db",".sqlite",".sqlite3",".pem",".key"}: raise SystemExit("Private data forbidden")
        info=zipfile.ZipInfo(ROOT.name+"/"+rel.as_posix(),date_time=(2026,9,5,0,0,0))
        info.create_system=3; info.external_attr=0o100644<<16; info.compress_type=zipfile.ZIP_DEFLATED
        z.writestr(info,p.read_bytes())
print(json.dumps({"artifact":target.name,"sha256":hashlib.sha256(target.read_bytes()).hexdigest(),"status":"source_archive_built"}))
