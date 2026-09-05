#!/usr/bin/env python3
"""Print or explicitly install this plugin's project-local Codex MCP connection."""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True
if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11 or newer is required; no configuration was changed.")

import argparse
import copy
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import tomllib

PRODUCT = "context-ontology-companion"
SERVER = "context_ontology_companion"
IS_CONTEXT = True
ROOT = Path(__file__).resolve().parents[1]
MAX_CONFIG_BYTES = 2 * 1024 * 1024
BEGIN = "# BEGIN ontology-companion-managed: " + SERVER
END = "# END ontology-companion-managed: " + SERVER


class SetupError(ValueError):
    pass


def safe_path(path):
    value = Path(path).expanduser()
    if not value.is_absolute() or ".." in value.parts:
        raise SetupError("ABSOLUTE_CANONICAL_PATH_REQUIRED")
    for part in (value, *value.parents):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise SetupError("SYMLINK_OR_JUNCTION_REJECTED")
        if os.name == "nt" and part.exists():
            attributes = getattr(part.lstat(), "st_file_attributes", 0)
            if attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
                raise SetupError("SYMLINK_OR_JUNCTION_REJECTED")
    return value


def config_path(project):
    project = safe_path(project)
    if not project.is_dir():
        raise SetupError("PROJECT_ROOT_MUST_EXIST")
    directory = safe_path(project / ".codex")
    if directory.exists() and not directory.is_dir():
        raise SetupError("CONFIG_DIRECTORY_INVALID")
    target = safe_path(directory / "config.toml")
    if target.exists() and (not target.is_file() or target.stat().st_nlink != 1):
        raise SetupError("CONFIG_FILE_UNSAFE")
    return target


def read_config(target):
    if not target.exists():
        return None
    if target.stat().st_size > MAX_CONFIG_BYTES:
        raise SetupError("CONFIG_TOO_LARGE")
    with target.open("rb") as stream:
        raw = stream.read(MAX_CONFIG_BYTES + 1)
    if len(raw) > MAX_CONFIG_BYTES:
        raise SetupError("CONFIG_TOO_LARGE")
    return raw


def parse(raw):
    try:
        return tomllib.loads(raw.decode("utf-8"))
    except (UnicodeError, tomllib.TOMLDecodeError):
        raise SetupError("CONFIG_INVALID_UTF8_TOML") from None


def connection(project, private_home=None):
    arguments = [str(ROOT / "scripts/run.py")]
    if IS_CONTEXT:
        arguments += ["local-stdio", "--project-root", str(project)]
        if private_home is not None:
            arguments += ["--home", str(private_home)]
    else:
        arguments += ["stdio"]
    return {"command": os.path.abspath(sys.executable), "args": arguments}


def block(settings, newline="\n"):
    # JSON escaping is compatible with the TOML basic strings used here.
    quote = lambda value: json.dumps(value, ensure_ascii=False)
    lines = [BEGIN, "[mcp_servers." + SERVER + "]",
             "command = " + quote(settings["command"]),
             "args = [" + ", ".join(quote(value) for value in settings["args"]) + "]", END]
    return newline.join(lines) + newline


def other_settings(data):
    result = copy.deepcopy(data)
    servers = result.get("mcp_servers")
    if isinstance(servers, dict):
        servers.pop(SERVER, None)
        if not servers:
            result.pop("mcp_servers")
    return result


def render_update(raw, settings):
    old = raw or b""
    data = parse(old)
    text = old.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines) if line.strip() == BEGIN]
    ends = [index for index, line in enumerate(lines) if line.strip() == END]
    replacement = block(settings, newline)
    servers = data.get("mcp_servers", {})
    if not isinstance(servers, dict):
        raise SetupError("MCP_SERVERS_TABLE_INVALID")
    if not starts and not ends:
        if SERVER in servers:
            raise SetupError("UNMANAGED_SERVER_ALREADY_EXISTS")
        separator = "" if not text or text.endswith(("\n", "\r")) else newline
        updated = text + separator + (newline if text else "") + replacement
    else:
        if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
            raise SetupError("MANAGED_MARKERS_INVALID")
        first, last = starts[0], ends[0]
        managed = parse("".join(lines[first:last + 1]).encode("utf-8"))
        expected_shape = {"mcp_servers": {SERVER: servers.get(SERVER)}}
        if managed != expected_shape or not isinstance(servers.get(SERVER), dict):
            raise SetupError("MANAGED_BLOCK_MODIFIED")
        if set(servers[SERVER]) != {"command", "args"}:
            raise SetupError("MANAGED_BLOCK_CUSTOM_OPTIONS_PRESERVED")
        updated = "".join(lines[:first]) + replacement + "".join(lines[last + 1:])
    candidate = updated.encode("utf-8")
    if len(candidate) > MAX_CONFIG_BYTES:
        raise SetupError("CONFIG_TOO_LARGE")
    new_data = parse(candidate)
    if new_data.get("mcp_servers", {}).get(SERVER) != settings:
        raise SetupError("GENERATED_SERVER_MISMATCH")
    if other_settings(data) != other_settings(new_data):
        raise SetupError("OTHER_CONFIGURATION_WOULD_CHANGE")
    return candidate


def initialize_context(project, private_home):
    if not IS_CONTEXT:
        return
    command = [os.path.abspath(sys.executable), str(ROOT / "scripts/run.py"),
               "local-init", "--project-root", str(project)]
    if private_home is not None:
        command += ["--home", str(private_home)]
    result = subprocess.run(command, capture_output=True, timeout=30,
                            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    if result.returncode:
        # Keep operator/configuration contents and subprocess details out of logs.
        raise SetupError("CONTEXT_LOCAL_INIT_FAILED")


def atomic_install(project, target, original, updated):
    if original == updated:
        return False
    directory = target.parent
    directory.mkdir(mode=0o700, exist_ok=True)
    config_path(project)  # Recheck every path after creating our directory.
    descriptor, temporary = tempfile.mkstemp(prefix=".ontology-mcp-", suffix=".tmp", dir=directory)
    temporary_path = Path(temporary)
    try:
        if os.name == "posix" and target.exists():
            os.fchmod(descriptor, stat.S_IMODE(target.stat().st_mode))
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        config_path(project)
        if read_config(target) != original:
            raise SetupError("CONFIG_CHANGED_DURING_INSTALL")
        os.replace(temporary_path, target)
        if os.name == "posix":
            directory_fd = os.open(directory, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        # Only remove the temporary file created by this exact invocation.
        if temporary_path.exists():
            temporary_path.unlink()
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True,
                        help="Absolute existing project directory; only its .codex/config.toml may be configured")
    parser.add_argument("--install", action="store_true",
                        help="Explicitly install/update this helper's owned block; default only prints TOML")
    if IS_CONTEXT:
        parser.add_argument("--home", type=Path,
                            help="Optional absolute private local CLI home, forwarded to local-init/local-stdio")
    args = parser.parse_args(argv)
    project = safe_path(args.project_root)
    target = config_path(project)
    private_home = getattr(args, "home", None)
    if private_home is not None:
        private_home = safe_path(private_home)
    settings = connection(project, private_home)
    if not args.install:
        print(block(settings), end="")
        return 0
    original = read_config(target)
    updated = render_update(original, settings)
    # Validate conflicts before creating local storage or changing configuration.
    initialize_context(project, private_home)
    changed = atomic_install(project, target, original, updated)
    print(json.dumps({"status": "installed" if changed else "unchanged",
                      "server": SERVER, "config": str(target),
                      "scope": "project_only", "other_configuration": "preserved",
                      "local_context": "initialized" if IS_CONTEXT else "not_required"},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        raise SystemExit(main())
    except (SetupError, OSError, subprocess.SubprocessError) as exc:
        error = str(exc) if isinstance(exc, SetupError) else type(exc).__name__
        print(json.dumps({"status": "error", "error": error}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
