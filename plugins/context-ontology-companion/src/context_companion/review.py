"""Authenticated loopback human review; no approval tool or OAuth claim.

Setup callers must obtain the password directly from the human (e.g. getpass).
Knowledge and credentials belong outside the repository. POSIX private modes are
checked; Windows ACL protection is NOT established by this adapter. This local
profile trusts the OS user/administrator and is not a production security claim.
HTTP is accepted only on IPv4 loopback; a remote service requires separate TLS
and authentication design. No browser is opened and no request body is logged.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from html import escape
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import socket
import stat
import time
from urllib.parse import parse_qs, urlsplit

from .store import ContextError, Principal, Store, canonical, text_field, validate_project

PBKDF2_ITERATIONS = 600_000
SESSION_SECONDS = 900
MAX_BODY_BYTES = 16_384
REJECT_DRAIN_BYTES = 65_536
REJECT_DRAIN_SECONDS = 0.5
MAX_SESSIONS = 64
COOKIE = "context_review_session"
CONFIG_NAME = "operator.json"
DATABASE_NAME = "context.sqlite3"
SOURCE_ROOT = Path(__file__).resolve().parents[2]


def _path(path):
    value = Path(path).expanduser()
    if not value.is_absolute() or ".." in value.parts:
        raise ContextError("UNSAFE_STORAGE_PATH")
    for part in (value, *value.parents):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise ContextError("UNSAFE_STORAGE_PATH")
        if os.name == "nt" and part.exists():
            # Python 3.11 has no Path.is_junction; reject reparse points too.
            if getattr(part.lstat(), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
                raise ContextError("UNSAFE_STORAGE_PATH")
    if value == SOURCE_ROOT or SOURCE_ROOT in value.parents:
        raise ContextError("STORAGE_MUST_BE_OUTSIDE_REPOSITORY")
    for part in (value, *value.parents):
        if (part / ".git").exists():
            raise ContextError("STORAGE_MUST_BE_OUTSIDE_REPOSITORY")
    return value


def _private(path, directory=False):
    _path(path)
    info = path.stat()
    if (directory and not stat.S_ISDIR(info.st_mode)) or (not directory and not stat.S_ISREG(info.st_mode)):
        raise ContextError("UNSAFE_STORAGE_PATH")
    if os.name == "posix" and (info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077):
        raise ContextError("INSECURE_STORAGE_PERMISSIONS")
    if not directory and info.st_nlink != 1:
        raise ContextError("UNSAFE_STORAGE_PATH")


def _create_private(path, contents=b""):
    _path(path)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(contents)
        stream.flush()
        os.fsync(stream.fileno())
    _private(path)


def init_local(home, project, username, password):
    """Provision one local operator; does not approve context or echo a password.

    Never call with a model-chosen production password. Tests use synthetic data.
    Existing operator/database files are never overwritten.
    """
    base = _path(home)
    validate_project(project)
    text_field(username, 160)
    if not isinstance(password, str) or not 12 <= len(password) <= 1024:
        raise ContextError("PASSWORD_LENGTH_INVALID")
    missing = []
    candidate = base
    while not candidate.exists():
        missing.append(candidate)
        candidate = candidate.parent
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)
    _private(base, directory=True)
    config_path, database_path = base / CONFIG_NAME, base / DATABASE_NAME
    if config_path.exists() or database_path.exists():
        raise ContextError("LOCAL_ALREADY_INITIALIZED")
    salt = secrets.token_bytes(32)
    principal = Principal("local_" + secrets.token_hex(16))
    config = {"version": 1, "username": username, "subject": principal.subject,
              "password_salt": salt.hex(), "password_hash": hashlib.pbkdf2_hmac(
                  "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS).hex(),
              "password_iterations": PBKDF2_ITERATIONS}
    _create_private(database_path)
    store = Store(database_path)
    try:
        store.provision_project(principal, project)
    finally:
        store.close()
    _create_private(config_path, canonical(config).encode("utf-8"))
    return {"initialized": True, "project": project,
            "storage_protection": "posix_owner_only" if os.name == "posix" else "windows_acl_not_verified"}


def _load_config(home):
    base = _path(home)
    _private(base, directory=True)
    config_path, database_path = base / CONFIG_NAME, base / DATABASE_NAME
    _private(config_path)
    _private(database_path)
    if config_path.stat().st_size > 8192:
        raise ContextError("INVALID_LOCAL_CONFIGURATION")
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if set(config) != {"version", "username", "subject", "password_salt", "password_hash", "password_iterations"}:
            raise ValueError()
        if config["version"] != 1 or config["password_iterations"] != PBKDF2_ITERATIONS:
            raise ValueError()
        text_field(config["username"], 160)
        if not re.fullmatch(r"local_[0-9a-f]{32}", config["subject"]):
            raise ValueError()
        if len(bytes.fromhex(config["password_salt"])) != 32 or len(bytes.fromhex(config["password_hash"])) != 32:
            raise ValueError()
    except (ValueError, KeyError, TypeError, UnicodeError):
        raise ContextError("INVALID_LOCAL_CONFIGURATION") from None
    return database_path, config


def load_local(home):
    """Resolve the model-facing adapter's principal from trusted operator config."""
    path, config = _load_config(home)
    return path, Principal(config["subject"])


@dataclass
class Session:
    csrf: str
    expires: float
    authenticated: bool = False


class ReviewServer(HTTPServer):
    """Single-process bounded local review server; sessions are not persisted."""
    allow_reuse_address = False

    def __init__(self, home, port=0):
        self.home = _path(home)
        self.database_path, self.config = _load_config(home)
        self.principal = Principal(self.config["subject"])
        self.sessions = {}
        self.clock = time.monotonic
        self.request_times = []
        self.login_times = []
        self.last_maintenance = 0.0
        super().__init__(("127.0.0.1", port), ReviewHandler)
        self.expected_host = f"127.0.0.1:{self.server_port}"
        self.origin = f"http://{self.expected_host}"

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(3)
        return connection, address

    def handle_error(self, request, client_address):
        # Default socketserver traceback can contain request-derived values.
        pass

    def service_actions(self):
        # Operator-started maintenance, independent from read-only MCP handlers.
        now=self.clock()
        if now-self.last_maintenance>=30:
            _load_config(self.home)
            store=Store(self.database_path)
            try: store.purge_expired()
            finally: store.close()
            self.last_maintenance=now

    def allow_request(self, login=False):
        now = self.clock()
        events = self.login_times if login else self.request_times
        events[:] = [when for when in events if when > now - 60]
        if len(events) >= (10 if login else 120):
            return False
        events.append(now)
        return True

    def new_session(self, authenticated=False):
        now = self.clock()
        self.sessions = {key: value for key, value in self.sessions.items() if value.expires > now}
        if len(self.sessions) >= MAX_SESSIONS:
            raise ContextError("RATE_LIMITED")
        sid = secrets.token_urlsafe(32)
        session = Session(secrets.token_urlsafe(32), now + SESSION_SECONDS, authenticated)
        self.sessions[sid] = session
        return sid, session


class ReviewHandler(BaseHTTPRequestHandler):
    server_version = "ContextLocalReview"
    sys_version = ""

    def log_message(self, format, *args):
        pass

    def _respond(self, code, body, cookie=None):
        content = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Pragma", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.send_header("Connection", "close")
        if cookie:
            self.send_header("Set-Cookie", f"{COOKIE}={cookie}; Path=/; HttpOnly; SameSite=Strict; Max-Age={SESSION_SECONDS}")
        self.end_headers()
        self.close_connection = True
        self.wfile.write(content)
        if code >= 400:
            self._finish_rejected_request()

    def _finish_rejected_request(self):
        # RFC 9112 section 9.6: full close with unread/in-flight request bytes
        # can reset the connection and erase the response on the client. Send
        # the rejection first, then half-close and discard only bounded bytes.
        # This is transport cleanup, never parsing or accepting a larger body.
        try:
            self.wfile.flush()
            self.connection.shutdown(socket.SHUT_WR)
            deadline = time.monotonic() + REJECT_DRAIN_SECONDS
            remaining = REJECT_DRAIN_BYTES
            while remaining:
                timeout = deadline - time.monotonic()
                if timeout <= 0:
                    break
                self.connection.settimeout(timeout)
                content = self.rfile.read1(min(4096, remaining))
                if not content:
                    break
                remaining -= len(content)
        except OSError:
            # The response is already sent; a disconnected/stalled peer must
            # not trigger request logging, another response or more processing.
            pass

    def send_error(self, code, message=None, explain=None):
        # Do not echo request paths, input, or Python exceptions in error pages.
        self._respond(code, "Request rejected.")

    def _error(self, code, label):
        self._respond(code, escape(label))

    def _check_request(self, post=False):
        try:
            parsed = urlsplit(self.path)
        except ValueError:
            self._error(400, "INVALID_REQUEST")
            return False
        if (len(self.headers.get_all("Host", [])) != 1 or self.headers["Host"] != self.server.expected_host
                or sum(len(k) + len(v) for k, v in self.headers.items()) > 16_384
                or parsed.scheme or parsed.netloc):
            self._error(400, "INVALID_REQUEST")
            return False
        if self.headers.get("Transfer-Encoding") is not None:
            self._error(400, "INVALID_REQUEST")
            return False
        origins = self.headers.get_all("Origin", [])
        if (post and origins != [self.server.origin]) or (origins and origins != [self.server.origin]):
            self._error(403, "ORIGIN_REJECTED")
            return False
        if not self.server.allow_request():
            self._error(429, "RATE_LIMITED")
            return False
        return True

    def _session(self):
        try:
            raw = self.headers.get_all("Cookie", [])
            if len(raw) != 1 or len(raw[0]) > 1024:
                return None, None
            cookie = SimpleCookie()
            cookie.load(raw[0])
            sid = cookie[COOKIE].value
            session = self.server.sessions.get(sid)
            if session is None or session.expires <= self.server.clock():
                self.server.sessions.pop(sid, None)
                return None, None
            return sid, session
        except (CookieError, KeyError, ValueError):
            return None, None

    @staticmethod
    def _hidden(name, value):
        return f'<input type="hidden" name="{escape(name, quote=True)}" value="{escape(value, quote=True)}">'

    def do_GET(self):
        if not self._check_request():
            return
        parsed = urlsplit(self.path)
        if parsed.query or parsed.fragment:
            self._error(400, "INVALID_REQUEST")
            return
        if parsed.path in {"/", "/login"}:
            try:
                sid, session = self.server.new_session()
            except ContextError:
                self._error(429, "RATE_LIMITED")
                return
            body = ('<!doctype html><meta charset="utf-8"><title>Local Context review</title>'
                    '<h1>Local Context review</h1><p>Authenticate to review a prepared change.</p>'
                    '<form method="post" action="/login">' + self._hidden("csrf", session.csrf) +
                    '<label>Username <input name="username" autocomplete="username" maxlength="160" required></label>'
                    '<label>Password <input type="password" name="password" autocomplete="current-password" maxlength="1024" required></label>'
                    '<button type="submit">Sign in</button></form>')
            self._respond(200, body, cookie=sid)
            return
        match = re.fullmatch(r"/review/(change_[0-9a-f]{32})", parsed.path)
        if not match:
            self._error(404, "NOT_FOUND")
            return
        _, session = self._session()
        if session is None or not session.authenticated:
            self._error(401, "AUTH_REQUIRED")
            return
        store = None
        try:
            _load_config(self.server.home)
            store = Store(self.server.database_path)
            review = store.review(self.server.principal, match.group(1))
            display = {key: review[key] for key in ("proposal_id", "scope", "payload", "target_record", "expires_at")}
            body = ('<!doctype html><meta charset="utf-8"><title>Review prepared change</title>'
                    '<h1>Review prepared change</h1><p>Approve only the exact change below.</p><pre>' +
                    escape(json.dumps(display, ensure_ascii=False, indent=2)) + '</pre>' +
                    f'<form method="post" action="/review/{escape(match.group(1))}/approve">' +
                    self._hidden("csrf", session.csrf) + self._hidden("digest", review["digest"]) +
                    self._hidden("nonce", review["nonce"]) + '<button type="submit">Approve exact change</button></form>')
            self._respond(200, body)
        except (ContextError, OSError):
            self._error(404, "NOT_FOUND_OR_FORBIDDEN")
        finally:
            if store:
                store.close()

    def _form(self):
        lengths = self.headers.get_all("Content-Length", [])
        if len(lengths) != 1 or not re.fullmatch(r"[0-9]{1,6}", lengths[0]):
            raise ContextError("INVALID_INPUT")
        length = int(lengths[0])
        if length > MAX_BODY_BYTES:
            raise ContextError("INPUT_TOO_LARGE")
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip() != "application/x-www-form-urlencoded":
            raise ContextError("INVALID_INPUT")
        content = self.rfile.read(length)
        if len(content) != length:
            raise ContextError("INVALID_INPUT")
        try:
            fields = parse_qs(content.decode("utf-8"), keep_blank_values=True, strict_parsing=True,
                              encoding="utf-8", errors="strict", max_num_fields=8)
        except (ValueError, UnicodeError):
            raise ContextError("INVALID_INPUT") from None
        if any(len(values) != 1 for values in fields.values()):
            raise ContextError("INVALID_INPUT")
        return {key: values[0] for key, values in fields.items()}

    def do_POST(self):
        if not self._check_request(post=True):
            return
        sid, session = self._session()
        if session is None:
            self._error(401, "AUTH_REQUIRED")
            return
        try:
            form = self._form()
        except (ContextError, OSError) as exc:
            self._error(413 if isinstance(exc, ContextError) and exc.code == "INPUT_TOO_LARGE" else 400, "INVALID_INPUT")
            return
        csrf = form.pop("csrf", "")
        if not re.fullmatch(r"[A-Za-z0-9_-]{43}", csrf) or not secrets.compare_digest(csrf, session.csrf):
            self._error(403, "CSRF_REJECTED")
            return
        if self.path == "/login":
            if not self.server.allow_request(login=True):
                self._error(429, "RATE_LIMITED")
                return
            if set(form) != {"username", "password"} or len(form["password"]) > 1024 or len(form["username"]) > 160:
                self._error(400, "INVALID_INPUT")
                return
            config = self.server.config
            hashed = hashlib.pbkdf2_hmac("sha256", form["password"].encode("utf-8"),
                                         bytes.fromhex(config["password_salt"]), config["password_iterations"])
            matches = secrets.compare_digest(hashed, bytes.fromhex(config["password_hash"]))
            matches = secrets.compare_digest(form["username"].encode("utf-8"), config["username"].encode("utf-8")) and matches
            if not matches:
                self._error(401, "AUTH_REQUIRED")
                return
            self.server.sessions.pop(sid, None)
            try:
                authenticated_sid, _ = self.server.new_session(authenticated=True)
            except ContextError:
                self._error(429, "RATE_LIMITED")
                return
            self._respond(200, "Signed in. Open the prepared change review URL in this browser.", cookie=authenticated_sid)
            return
        match = re.fullmatch(r"/review/(change_[0-9a-f]{32})/approve", self.path)
        if not match or set(form) != {"digest", "nonce"}:
            self._error(400, "INVALID_INPUT")
            return
        if not session.authenticated:
            self._error(401, "AUTH_REQUIRED")
            return
        if not re.fullmatch(r"[0-9a-f]{64}", form["digest"]) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", form["nonce"]):
            self._error(400, "INVALID_INPUT")
            return
        store = None
        try:
            _load_config(self.server.home)
            store = Store(self.server.database_path)
            store.approve(self.server.principal, match.group(1), form["digest"], form["nonce"])
            self._respond(200, "Approved change applied.")
        except (ContextError, OSError):
            self._error(409, "APPROVAL_REJECTED")
        finally:
            if store:
                store.close()


def make_server(home, port=0):
    if type(port) is not int or not 0 <= port <= 65535:
        raise ContextError("INVALID_PORT")
    return ReviewServer(home, port)


def serve(home, port=8765):
    """Run only local HTTP; caller may display a credential-free local URL."""
    with make_server(home, port) as server:
        server.serve_forever(poll_interval=0.25)
