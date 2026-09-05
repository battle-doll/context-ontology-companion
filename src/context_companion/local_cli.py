"""Persistent explicit-request workflow trusted to the current local OS account.

An authorization literal records the caller's assertion, never a verified human
click. This profile does not reuse HTTP-review credentials or collect project
files/chats. Selected candidate bytes are the only knowledge input read here.
"""
from __future__ import annotations
import ctypes
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys

from .mcp import parse
from .review import _path, _private, _create_private
from .store import ContextError, LocalAuthorization, Principal, Store, MAX_BYTES, canonical, digest, validate_candidate, validate_project

PROFILE = "os_account_explicit_request"
CONFIG = "local-cli.json"
DATABASE = "local-context.sqlite3"
WRITE_COMMANDS = {"save": "create", "update": "supersede", "contradict": "contradict", "revoke": "revoke", "delete": "erase"}


def default_home():
    if sys.platform == "darwin":
        path = Path.home() / "Library/Application Support/ContextOntologyCompanion/local-cli"
    elif os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local")))
        if not base.is_absolute(): base = Path.home() / "AppData/Local"
        path = base / "ContextOntologyCompanion/local-cli"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))
        if not base.is_absolute(): base = Path.home() / ".local/share"
        path = base / "context-ontology-companion/local-cli"
    # Resolve OS-provided aliases for defaults; explicitly passed homes remain
    # subject to the strict no-symlink user-path checks.
    return path.resolve()


def _windows_sid():
    """Read the current process token SID, including domain/account identity."""
    from ctypes import wintypes
    kernel, advapi = ctypes.windll.kernel32, ctypes.windll.advapi32
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    advapi.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    advapi.OpenProcessToken.restype = wintypes.BOOL
    advapi.GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    advapi.GetTokenInformation.restype = wintypes.BOOL
    advapi.ConvertSidToStringSidW.argtypes = [wintypes.LPVOID, ctypes.POINTER(wintypes.LPWSTR)]
    advapi.ConvertSidToStringSidW.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [wintypes.LPVOID]
    kernel.LocalFree.restype = wintypes.LPVOID
    token = wintypes.HANDLE()
    if not advapi.OpenProcessToken(kernel.GetCurrentProcess(), 0x0008, ctypes.byref(token)):
        raise ContextError("OS_ACCOUNT_UNAVAILABLE")
    try:
        needed = wintypes.DWORD()
        advapi.GetTokenInformation(token, 1, None, 0, ctypes.byref(needed))
        if not 0 < needed.value <= 65_536: raise ContextError("OS_ACCOUNT_UNAVAILABLE")
        buffer = ctypes.create_string_buffer(needed.value)
        if not advapi.GetTokenInformation(token, 1, buffer, needed, ctypes.byref(needed)):
            raise ContextError("OS_ACCOUNT_UNAVAILABLE")
        # TOKEN_USER starts with SID_AND_ATTRIBUTES; its first field is PSID.
        sid = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_void_p))[0]
        text = wintypes.LPWSTR()
        if not advapi.ConvertSidToStringSidW(sid, ctypes.byref(text)):
            raise ContextError("OS_ACCOUNT_UNAVAILABLE")
        try: return text.value
        finally: kernel.LocalFree(ctypes.cast(text, wintypes.LPVOID))
    finally:
        kernel.CloseHandle(token)


def account_key():
    if os.name == "posix":
        identity = "posix-uid:" + str(os.getuid())
    elif os.name == "nt":
        identity = "windows-sid:" + _windows_sid()
    else:
        raise ContextError("OS_ACCOUNT_UNAVAILABLE")
    return "os_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()


def project_scope(project=None, project_root=None):
    if (project is None) == (project_root is None):
        raise ContextError("SELECT_PROJECT_OR_PROJECT_ROOT")
    if project is not None:
        return validate_project(project)
    path = Path(project_root).expanduser().resolve()
    if not path.is_dir():
        raise ContextError("PROJECT_ROOT_NOT_DIRECTORY")
    return "project_" + hashlib.sha256(os.path.normcase(str(path)).encode("utf-8")).hexdigest()[:24]


def home_path(home=None):
    return _path(default_home() if home is None else home)


def load_profile(home=None):
    base = home_path(home)
    if (base / "operator.json").exists() or (base / "context.sqlite3").exists():
        raise ContextError("LOCAL_PROFILE_CONFLICT_USE_SEPARATE_HOME")
    if not (base / CONFIG).is_file() or not (base / DATABASE).is_file():
        raise ContextError("LOCAL_CLI_NOT_INITIALIZED_USE_LOCAL_INIT")
    _private(base, directory=True)
    _private(base / CONFIG)
    _private(base / DATABASE)
    if (base / CONFIG).stat().st_size > 8192:
        raise ContextError("INVALID_LOCAL_CLI_CONFIGURATION")
    try:
        config = parse((base / CONFIG).read_bytes())
        if not isinstance(config, dict) or set(config) != {"version", "profile", "subject", "account_key"}:
            raise ValueError()
        if type(config["version"]) is not int or config["version"] != 1 or config["profile"] != PROFILE:
            raise ValueError()
        if not isinstance(config["subject"], str) or len(config["subject"]) != 36 or not config["subject"].startswith("cli_") or any(c not in "0123456789abcdef" for c in config["subject"][4:]):
            raise ValueError()
        if config["account_key"] != account_key():
            raise ContextError("LOCAL_OS_ACCOUNT_MISMATCH")
    except (ValueError, TypeError, UnicodeError, RecursionError) as error:
        if isinstance(error, ContextError):
            raise
        raise ContextError("INVALID_LOCAL_CLI_CONFIGURATION") from None
    return base / DATABASE, Principal(config["subject"]), config["account_key"]


def initialize(scope, home=None):
    validate_project(scope)
    base = home_path(home)
    if base.exists():
        _private(base, directory=True)
        if (base / "operator.json").exists() or (base / "context.sqlite3").exists():
            raise ContextError("LOCAL_PROFILE_CONFLICT_USE_SEPARATE_HOME")
        if not (base / CONFIG).exists() and any(base.iterdir()):
            raise ContextError("LOCAL_HOME_NOT_EMPTY_OR_PARTIAL_INITIALIZATION")
    if not (base / CONFIG).exists():
        missing = []
        directory = base
        while not directory.exists():
            missing.append(directory)
            directory = directory.parent
        for directory in reversed(missing):
            directory.mkdir(mode=0o700)
        _private(base, directory=True)
        actor = account_key()
        principal = Principal("cli_" + secrets.token_hex(16))
        _create_private(base / DATABASE)
        store = Store(base / DATABASE)
        store.close()
        _create_private(base / CONFIG, canonical({"version": 1, "profile": PROFILE, "subject": principal.subject, "account_key": actor}).encode("utf-8"))
    path, principal, _ = load_profile(base)
    store = Store(path)
    try:
        store.provision_project(principal, scope)
    finally:
        store.close()
    return {"profile": PROFILE, "scope": scope, "home": str(base), "authorization_mode": PROFILE,
            "human_review_performed": False, "storage_protection": "posix_owner_only" if os.name == "posix" else "windows_acl_not_verified"}


def read_candidate(filename):
    try:
        if str(filename) == "-":
            raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        else:
            path = Path(filename).expanduser()
            if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
                raise ContextError("CANDIDATE_MUST_BE_BOUNDED_REGULAR_FILE")
            with path.open("rb") as stream:
                raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ContextError("INPUT_TOO_LARGE")
        return validate_candidate(parse(raw))
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError) as error:
        if isinstance(error, ContextError):
            raise
        raise ContextError("INVALID_CANDIDATE_JSON") from None


def execute(store, principal, actor, scope, operation, *, query="", record_id=None,
            expected_revision=None, candidate=None, authorization=None, request_id=None,
            proposal_id=None, max_chars=12000):
    """Common CLI/local-MCP service; the adapter resolves identity and scope."""
    store._access(principal, scope)
    if record_id is not None and operation not in WRITE_COMMANDS:
        record = store.fetch(principal, record_id)
        if record["scope"] != scope:
            raise ContextError("NOT_FOUND_OR_FORBIDDEN")
    if proposal_id is not None and store._proposal(principal, proposal_id)["project"] != scope:
        raise ContextError("NOT_FOUND_OR_FORBIDDEN")
    if operation in WRITE_COMMANDS:
        if authorization != "explicit-user-request":
            raise ContextError("EXPLICIT_LOCAL_AUTHORIZATION_REQUIRED")
        validate_project(request_id)
        action = WRITE_COMMANDS[operation]
        payload = {"operation": action, "target": record_id, "expected_revision": expected_revision, "candidate": candidate}
        pending = store.prepare(principal, scope, action, request_id, candidate, record_id, expected_revision)
        result = store.apply_local(principal, pending["proposal_id"], digest(payload), LocalAuthorization(actor, request_id))
    elif operation == "search": result = store.search(principal, scope, query)
    elif operation == "fetch": result = store.fetch(principal, record_id)
    elif operation == "history": result = store.history(principal, record_id)
    elif operation == "pack": result = store.pack(principal, scope, query, max_chars)
    elif operation == "export": return store.export(principal, scope)
    elif operation == "status": result = store.local_change_status(principal, proposal_id)
    elif operation == "projects": result = {"projects": [scope]}
    else: raise ContextError("UNKNOWN_LOCAL_OPERATION")
    return {"profile": PROFILE, "scope": scope, "authorization_mode": PROFILE,
            "human_review_performed": False, "result": result}


def add_arguments(subparsers):
    for name in ["init", "stdio", "projects", "save", "update", "contradict", "revoke", "delete", "search", "fetch", "history", "pack", "export", "status"]:
        parser = subparsers.add_parser("local-" + name, help="Explicit OS-account local " + name + "; independent of HTTP review")
        parser.add_argument("--home", type=Path, help="Separate private absolute data directory; defaults to OS user-data location")
        if name != "projects":
            scope = parser.add_mutually_exclusive_group(required=True)
            scope.add_argument("--project")
            scope.add_argument("--project-root", type=Path)
        if name in {"save", "update", "contradict"}:
            parser.add_argument("--input", required=True, help="Explicitly selected bounded candidate JSON file, or - for stdin")
        if name in {"update", "contradict", "revoke", "delete", "fetch", "history"}:
            parser.add_argument("--id", required=True)
        if name in {"update", "contradict", "revoke", "delete"}:
            parser.add_argument("--expected-revision", type=int, required=True)
        if name in WRITE_COMMANDS:
            parser.add_argument("--authorization", choices=["explicit-user-request"], required=True,
                                help="Caller confirms a current explicit user request; not independent human authentication")
            parser.add_argument("--request-id", required=True, help="Stable non-sensitive caller request identifier for safe retries")
        if name in {"search", "pack"}: parser.add_argument("--query", default="")
        if name == "pack": parser.add_argument("--max-chars", type=int, default=12000)
        if name == "status": parser.add_argument("--proposal-id", required=True)


def run(args):
    operation = args.command.removeprefix("local-")
    scope = project_scope(getattr(args, "project", None), getattr(args, "project_root", None)) if operation != "projects" else None
    if operation == "init": return initialize(scope, args.home)
    path, principal, actor = load_profile(args.home)
    if operation == "stdio":
        from .local_mcp import serve
        serve(args.home, scope)
        return None
    candidate = read_candidate(args.input) if hasattr(args, "input") else None
    store = Store(path)
    try:
        if operation == "projects":
            return {"profile": PROFILE, "authorization_mode": PROFILE, "human_review_performed": False, "result": store.list_projects(principal)}
        return execute(store, principal, actor, scope, operation, query=getattr(args, "query", ""),
                       record_id=getattr(args, "id", None), expected_revision=getattr(args, "expected_revision", None),
                       candidate=candidate, authorization=getattr(args, "authorization", None), request_id=getattr(args, "request_id", None),
                       proposal_id=getattr(args, "proposal_id", None), max_chars=getattr(args, "max_chars", 12000))
    finally:
        store.close()
