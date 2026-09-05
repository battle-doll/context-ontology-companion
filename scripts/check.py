#!/usr/bin/env python3
"""Portable product acceptance checks, independent of sibling installations."""
from pathlib import Path
import json
import hashlib
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    if sys.version_info<(3,11): raise SystemExit("Python 3.11+ required")
    pin=json.loads((ROOT/"vendor/CONTRACTS_PIN.json").read_text(encoding="utf-8"))
    actual={p.relative_to(ROOT/"vendor").as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/"vendor/companion_contracts").rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix!=".pyc"}
    if actual!=pin["files"]: raise SystemExit("Vendored contract digest mismatch")
    if hashlib.sha256((ROOT/"vendor/CONTRACTS_LICENSE").read_bytes()).hexdigest()!=pin["license_sha256"]: raise SystemExit("Vendored license digest mismatch")
    for args in [["-m","unittest","discover","-s","tests_product","-v"],["scripts/run.py","demo"],["scripts/run.py","tools"]]:
        result=subprocess.run([sys.executable,*args],cwd=ROOT,capture_output=True,text=True,encoding="utf-8")
        if result.returncode:
            print(result.stdout); print(result.stderr,file=sys.stderr); return result.returncode
        if "unittest" in args: print(result.stderr)
        else: json.loads(result.stdout)
    print(json.dumps({"status":"PASS","scope":"LOCAL_PRODUCT_SYNTHETIC","vendor_digest":"PASS","host_e2e":"not_run"}))
    return 0


if __name__=="__main__": raise SystemExit(main())
