#!/usr/bin/env python3
"""Build/check the self-contained local plugin and deterministic install ZIP.

Only reviewed source categories are copied. No downloads, installation, GitHub
mutation, credentials, runtime data, sibling repository, or platform auth needed.
--check is read-only and checks the exact generated file set and every byte.
--check-directory performs the same tree checks without requiring a local ZIP.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "plugin-bundle.json"
PRODUCTS = {"context-ontology-companion", "ontology-companion-contracts"}
DIRECTORIES = {".codex-plugin", ".github", "assets", "contracts", "design", "docs", "evals", "examples",
               "experiments", "scripts", "skills", "src", "submission", "tests", "tests_product", "vendor"}
ROOT_FILES = {".gitattributes", ".gitignore", "ACTIVE_PLAN.md", "AGENTS.md", "CHANGELOG.md",
              "CONTRIBUTING.md", "CURRENT_STATE.md", "DECISIONS.md", "DESIGN_VERSION", "LICENSE",
              "NEXT_ACTIONS.md", "PRIVACY.md", "README.md", "README.ko.md", "README.ja.md",
              "README.zh-CN.md", "README.ru.md", "RISK_REGISTER.md", "SECURITY.md", "START_HERE.md",
              "SUPPORT.md", "TERMS.md", "TEST_EVIDENCE.md", "artifact-manifest.json", "chatgpt-app-submission.json",
              "release-intent.json", "release-state.json", "requirements-dev.txt", "mcp-tool-catalog.json"}
EXCLUDED = {".git", ".agents", "plugins", "dist", "build", ".venv", "venv", "node_modules",
            "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "cache", "caches",
            "user-data", "runtime-data", "logs", "exports", "backups", ".local"}
SUFFIXES = {".py", ".json", ".md", ".txt", ".yaml", ".yml"}
ASSET_SUFFIXES = {".svg", ".png"}
SPECIAL_FILES = {"vendor/CONTRACTS_LICENSE"}
PRIVATE_NAMES = {"operator.json", "local-cli.json", "credentials.json", "auth.json", ".bootstrap-state.json"}
ZIP_DATE = (2026, 9, 5, 0, 0, 0)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def forbidden(path):
    name = path.name.lower()
    return (name.startswith(".env") or name in PRIVATE_NAMES
            or re.search(r"\.(?:db|sqlite|sqlite3)(?:[-.]|$)", name) is not None
            or path.suffix.lower() in {".key", ".pem", ".p12", ".pfx", ".jks", ".keystore"})


def safe_directory(path):
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise ValueError("Symlink/junction not allowed in package path")


def canonical_files():
    result = {}
    for directory, names, filenames in os.walk(ROOT, followlinks=False):
        parent = Path(directory)
        relative_parent = parent.relative_to(ROOT)
        kept = []
        for name in sorted(names):
            path = parent / name
            if name in EXCLUDED or name.endswith(".egg-info"):
                continue
            safe_directory(path)
            if parent == ROOT and name not in DIRECTORIES:
                raise ValueError("Unreviewed source directory: " + name)
            kept.append(name)
        names[:] = kept
        for name in sorted(filenames):
            path = parent / name
            relative = path.relative_to(ROOT).as_posix()
            if name in {"FILE_MANIFEST.json", MANIFEST, ".DS_Store", "Thumbs.db"} or path.suffix in {".pyc", ".pyo"}:
                continue
            safe_directory(path)
            if forbidden(path):
                raise ValueError("Private/runtime file forbidden: " + relative)
            allowed = name in ROOT_FILES if parent == ROOT else path.suffix in SUFFIXES or relative in SPECIAL_FILES
            if relative.startswith("assets/") and path.suffix in ASSET_SUFFIXES:
                allowed = True
            if not allowed or not path.is_file():
                raise ValueError("Unreviewed source file: " + relative)
            result[relative] = path.read_bytes()
    return dict(sorted(result.items()))


def expected_bundle():
    content = canonical_files()
    metadata = json.loads(content[".codex-plugin/plugin.json"])
    product, version = metadata["name"], metadata["version"]
    if product not in PRODUCTS or product != ROOT.name or not re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z.+-]{0,80}", version):
        raise ValueError("Unsupported plugin identity/version")
    content[MANIFEST] = encoded({
        "manifest_version": 1, "product": product, "plugin_version": version,
        "layout": "self_contained_plugin", "runtime": "Python >=3.11",
        "files": {name: {"sha256": sha(value), "bytes": len(value)} for name, value in content.items()},
        "excluded_metadata": [MANIFEST, "FILE_MANIFEST.json"],
        "assurance": "Deterministic file integrity only; no signature, account authentication, host E2E, or directory approval claim."
    })
    if product == "context-ontology-companion":
        # A fresh internal manifest covers this bundle, never the canonical tree
        # that also contains the generated bundle. plugin-bundle excludes it.
        content["FILE_MANIFEST.json"] = encoded({
            "manifest_version": 1, "package": product,
            "design_version": content["DESIGN_VERSION"].decode("utf-8").strip(),
            "intended_repository": "battle-doll/" + product,
            "files": [{"path": name, "sha256": sha(value), "bytes": len(value)} for name, value in sorted(content.items())]
        })
    return product, version, dict(sorted(content.items()))


def archive_bytes(product, content):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, value in content.items():
            info = zipfile.ZipInfo(product + "/" + name, date_time=ZIP_DATE)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, value, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return output.getvalue()


def actual_files(folder):
    if not folder.is_dir():
        raise ValueError("Generated plugin missing; run scripts/build_plugin.py")
    result = {}
    for path in sorted(folder.rglob("*")):
        safe_directory(path)
        if path.is_file():
            result[path.relative_to(folder).as_posix()] = path.read_bytes()
    return result


def write_bundle(destination, content):
    safe_directory(destination)
    destination.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".plugin-build-", dir=destination.parent) as temp:
        staged = Path(temp) / destination.name
        staged.mkdir()
        for name, value in content.items():
            target = staged / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(value)
        if destination.exists():
            # Only this generated target belongs to the builder. Reject links
            # before removing stale generated files; canonical source is untouched.
            actual_files(destination)
            shutil.rmtree(destination)
        staged.rename(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Verify generated directory and ZIP without changing them")
    mode.add_argument("--check-directory", action="store_true", help="Verify only the generated directory without reading or requiring a ZIP")
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        raise ValueError("Python 3.11 or newer required")
    product, version, content = expected_bundle()
    destination = ROOT / "plugins" / product
    archive_path = ROOT / "dist" / f"{product}-{version}-plugin.zip"
    archive = None if args.check_directory else archive_bytes(product, content)
    if args.check or args.check_directory:
        actual = actual_files(destination)
        if set(actual) != set(content):
            raise ValueError("Generated file-set mismatch: " + json.dumps({"missing": sorted(set(content) - set(actual)), "extra": sorted(set(actual) - set(content))}))
        mismatches = [name for name in content if sha(actual[name]) != sha(content[name])]
        if mismatches:
            raise ValueError("Generated content mismatch: " + ", ".join(mismatches))
        if args.check:
            safe_directory(archive_path)
            if not archive_path.is_file() or archive_path.read_bytes() != archive:
                raise ValueError("Generated ZIP mismatch; rebuild after reviewing canonical changes")
    else:
        write_bundle(destination, content)
        safe_directory(archive_path)
        archive_path.parent.mkdir(exist_ok=True)
        archive_path.write_bytes(archive)
    result = {"status": "PASS", "operation": "check_directory" if args.check_directory else "check" if args.check else "build",
              "product": product, "plugin_version": version, "files": len(content),
              "bundle": destination.relative_to(ROOT).as_posix()}
    if args.check_directory:
        result["archive_check"] = "not_requested"
    else:
        result.update(archive=archive_path.relative_to(ROOT).as_posix(), sha256=sha(archive))
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as error:
        print("Plugin packaging failed: " + str(error), file=sys.stderr)
        raise SystemExit(1)
