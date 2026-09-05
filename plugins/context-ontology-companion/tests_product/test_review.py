"""Synthetic local HTTP integration. Not ChatGPT E2E or Windows ACL proof."""
from html import unescape
from http.client import HTTPConnection
import json
import os
from pathlib import Path
import re
import tempfile
import threading
import unittest
from urllib.parse import urlencode

import sys
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/"src"),str(Path(__file__).resolve().parents[1]/"vendor")]
from context_companion.review import COOKIE, CONFIG_NAME, DATABASE_NAME, MAX_BODY_BYTES, SOURCE_ROOT, init_local, load_local, make_server
from context_companion.store import ContextError, Principal, Store

PASSWORD = "synthetic-review-password-123"
USERNAME = "synthetic-operator"


def candidate():
    return {"statement": '합성 결정: <script>alert("x")</script> 대신 검토합니다.',
            "kind": "decision", "origin": "user_asserted", "valid_from": "2026-01-01T00:00:00Z",
            "valid_until": None, "evidence": [{"id": "synthetic-source", "origin": "user_asserted", "locator": "synthetic://review-example"}]}


def fields(body):
    return {name: unescape(value) for name, value in re.findall(r'<input type="hidden" name="([^"]+)" value="([^"]*)">', body)}


class ReviewHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="context-review-tests-")
        # macOS tempfile can use /var -> /private/var; pass the actual location.
        self.home = Path(self.temp.name).resolve() / "private-home"
        init_local(self.home, "synthetic-project", USERNAME, PASSWORD)
        self.path, self.principal = load_local(self.home)
        store = Store(self.path)
        try:
            self.proposal = store.prepare(self.principal, "synthetic-project", "create", "synthetic-idempotency", candidate())
        finally:
            store.close()
        self.pid = self.proposal["proposal_id"]
        self.server = make_server(self.home)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
        self.thread.start()
        self.cookie = None

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.temp.cleanup()

    def request(self, method, path, data=None, headers=None, cookie=True, raw=None):
        supplied = {"Host": self.server.expected_host}
        if self.cookie and cookie:
            supplied["Cookie"] = self.cookie
        body = None
        if method == "POST":
            body = urlencode(data or {}) if raw is None else raw
            supplied.update({"Origin": self.server.origin, "Content-Type": "application/x-www-form-urlencoded"})
        supplied.update(headers or {})
        conn = HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            conn.request(method, path, body, supplied)
            response = conn.getresponse()
            result = response.status, dict(response.getheaders()), response.read().decode("utf-8")
        finally:
            conn.close()
        if "Set-Cookie" in result[1]:
            self.cookie = result[1]["Set-Cookie"].split(";", 1)[0]
        return result

    def login(self):
        code, headers, body = self.request("GET", "/login")
        self.assertEqual(code, 200)
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        self.assertIn("SameSite=Strict", headers["Set-Cookie"])
        previous = self.cookie
        form = {**fields(body), "username": USERNAME, "password": PASSWORD}
        code, _, body = self.request("POST", "/login", form)
        self.assertEqual(code, 200, body)
        self.assertNotEqual(self.cookie, previous)

    def review_form(self):
        code, _, body = self.request("GET", f"/review/{self.pid}")
        self.assertEqual(code, 200, body)
        return fields(body)

    def current(self):
        store = Store(self.path)
        try:
            return store.change_status(self.principal, self.pid), store.search(self.principal, "synthetic-project")
        finally:
            store.close()

    def test_actual_http_login_review_approve_and_new_connection_recovery(self):
        self.login()
        code, headers, body = self.request("GET", f"/review/{self.pid}")
        self.assertEqual(code, 200)
        self.assertIn("&lt;script&gt;", body)
        self.assertNotIn("<script>", body)
        self.assertIn("synthetic://review-example", body)
        self.assertIn("synthetic-project", body)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
        code, _, _ = self.request("POST", f"/review/{self.pid}/approve", fields(body))
        self.assertEqual(code, 200)
        status, result = self.current()
        self.assertEqual(status["state"], "applied")
        self.assertEqual(result["records"][0]["statement"], candidate()["statement"])
        self.assertEqual(result["records"][0]["evidence"], candidate()["evidence"])

    def test_unauthenticated_review_and_approval_do_not_mutate(self):
        self.assertEqual(self.request("GET", f"/review/{self.pid}")[0], 401)
        self.assertEqual(self.request("POST", f"/review/{self.pid}/approve", {})[0], 401)
        status, result = self.current()
        self.assertEqual(status["state"], "pending")
        self.assertEqual(result["records"], [])

    def test_incorrect_password_and_login_csrf_rejected(self):
        _, _, body = self.request("GET", "/login")
        form = {**fields(body), "username": USERNAME, "password": "wrong-synthetic-password"}
        self.assertEqual(self.request("POST", "/login", form)[0], 401)
        form["csrf"] = "한글"
        self.assertEqual(self.request("POST", "/login", form)[0], 403)
        self.assertEqual(self.current()[0]["state"], "pending")

    def test_missing_or_wrong_csrf_does_not_mutate(self):
        self.login()
        form = self.review_form()
        form.pop("csrf")
        self.assertEqual(self.request("POST", f"/review/{self.pid}/approve", form)[0], 403)
        self.assertEqual(self.current()[0]["state"], "pending")

    def test_wrong_host_and_origin_rejected(self):
        self.assertEqual(self.request("GET", "/login", headers={"Host": "attacker.invalid"})[0], 400)
        self.login()
        form = self.review_form()
        self.assertEqual(self.request("POST", f"/review/{self.pid}/approve", form, {"Origin": "http://attacker.invalid"})[0], 403)
        self.assertEqual(self.request("POST", f"/review/{self.pid}/approve", form, {"Origin": "null"})[0], 403)
        self.assertEqual(self.current()[0]["state"], "pending")

    def test_malformed_url_and_cookie_return_bounded_errors(self):
        self.assertEqual(self.request("GET", "http://[invalid/")[0], 400)
        self.assertEqual(self.request("GET", f"/review/{self.pid}", headers={"Cookie": "=malformed;"})[0], 401)
        self.assertEqual(self.current()[0]["state"], "pending")

    def test_wrong_principal_cannot_review_or_approve(self):
        other = Principal("synthetic-other-principal")
        store = Store(self.path)
        try:
            store.provision_project(other, "synthetic-project")
            other_pid = store.prepare(other, "synthetic-project", "create", "other-key", candidate())["proposal_id"]
            other_review = store.review(other, other_pid)
        finally:
            store.close()
        self.login()
        own_form = self.review_form()
        self.assertEqual(self.request("GET", f"/review/{other_pid}")[0], 404)
        form = {"csrf": own_form["csrf"], "digest": other_review["digest"], "nonce": other_review["nonce"]}
        self.assertEqual(self.request("POST", f"/review/{other_pid}/approve", form)[0], 409)
        store = Store(self.path)
        try:
            self.assertEqual(store.change_status(other, other_pid)["state"], "pending")
            self.assertEqual(store.search(other, "synthetic-project")["records"], [])
        finally:
            store.close()

    def test_nonce_digest_tampering_and_extra_authority_fields_rejected(self):
        self.login()
        form = self.review_form()
        self.assertEqual(self.request("POST", f"/review/{self.pid}/approve", {**form, "digest": "0" * 64})[0], 409)
        self.assertEqual(self.request("POST", f"/review/{self.pid}/approve", {**form, "nonce": "a" * 43})[0], 409)
        self.assertEqual(self.request("POST", f"/review/{self.pid}/approve", {**form, "approved": "true"})[0], 400)
        self.assertEqual(self.current()[0]["state"], "pending")

    def test_replay_and_get_apply_are_not_mutations(self):
        self.login()
        form = self.review_form()
        self.assertEqual(self.request("GET", f"/review/{self.pid}/approve")[0], 404)
        self.assertEqual(self.current()[0]["state"], "pending")
        self.assertEqual(self.request("POST", f"/review/{self.pid}/approve", form)[0], 200)
        self.assertEqual(self.request("POST", f"/review/{self.pid}/approve", form)[0], 409)
        self.assertEqual(len(self.current()[1]["records"]), 1)

    def test_expired_session_denied(self):
        self.login()
        form = self.review_form()
        for session in self.server.sessions.values():
            session.expires = 0
        self.assertEqual(self.request("POST", f"/review/{self.pid}/approve", form)[0], 401)
        self.assertEqual(self.current()[0]["state"], "pending")

    def test_erase_review_displays_exact_target_before_applying(self):
        self.login()
        self.assertEqual(self.request("POST", f"/review/{self.pid}/approve", self.review_form())[0], 200)
        record_id = self.current()[0]["record_id"]
        store = Store(self.path)
        try:
            erase_pid = store.prepare(self.principal, "synthetic-project", "erase", "synthetic-erase-key",
                                      target=record_id, expected_revision=1)["proposal_id"]
        finally:
            store.close()
        code, _, body = self.request("GET", f"/review/{erase_pid}")
        self.assertEqual(code, 200)
        self.assertIn("target_record", body)
        self.assertIn(record_id, body)
        self.assertIn("&lt;script&gt;", body)
        self.assertIn("erase", body)
        self.assertEqual(self.request("POST", f"/review/{erase_pid}/approve", fields(body))[0], 200)
        self.assertEqual(self.current()[1]["records"], [])

    def test_bounded_body_and_duplicate_form_fields(self):
        self.login()
        self.assertEqual(self.request("POST", "/login", raw="x=" + "a" * MAX_BODY_BYTES)[0], 413)
        self.assertEqual(self.request("POST", "/login", raw="csrf=a&csrf=b")[0], 400)
        self.assertEqual(self.current()[0]["state"], "pending")

    def test_rate_limits_and_loopback_bind(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        self.server.request_times = [self.server.clock()] * 120
        self.assertEqual(self.request("GET", "/login")[0], 429)

    def test_login_rate_limit(self):
        _, _, body = self.request("GET", "/login")
        self.server.login_times = [self.server.clock()] * 10
        form = {**fields(body), "username": USERNAME, "password": PASSWORD}
        self.assertEqual(self.request("POST", "/login", form)[0], 429)

    def test_configuration_stores_only_salted_hash_and_no_password_response(self):
        config = json.loads((self.home / CONFIG_NAME).read_text())
        self.assertNotIn(PASSWORD, json.dumps(config))
        self.assertNotEqual(config["password_hash"], PASSWORD)
        self.assertNotIn(PASSWORD, self.request("GET", "/login")[2])


class LocalStorageSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="context-setup-tests-")
        self.root = Path(self.temp.name).resolve()

    def tearDown(self):
        self.temp.cleanup()

    def test_no_overwrite_and_trusted_principal_configuration(self):
        home = self.root / "home"
        result = init_local(home, "synthetic-project", USERNAME, PASSWORD)
        self.assertTrue(result["initialized"])
        _, principal = load_local(home)
        self.assertTrue(principal.subject.startswith("local_"))
        with self.assertRaisesRegex(ContextError, "LOCAL_ALREADY_INITIALIZED"):
            init_local(home, "other", USERNAME, PASSWORD)
        self.assertEqual(load_local(home)[1], principal)

    def test_repository_relative_and_parent_traversal_paths_rejected(self):
        for home in (Path("relative-home"), SOURCE_ROOT / "private-test", self.root / "path" / ".." / "home"):
            with self.subTest(home=home), self.assertRaises(ContextError):
                init_local(home, "synthetic-project", USERNAME, PASSWORD)

    def test_invalid_project_has_no_filesystem_side_effect(self):
        home = self.root / "unused-home"
        with self.assertRaises(ContextError):
            init_local(home, "Research Project", USERNAME, PASSWORD)
        self.assertFalse(home.exists())

    def test_symlink_component_rejected(self):
        real = self.root / "real"
        real.mkdir()
        link = self.root / "linked"
        try:
            link.symlink_to(real, target_is_directory=True)
        except OSError:
            self.skipTest("Symlink creation unavailable on this OS account")
        with self.assertRaisesRegex(ContextError, "UNSAFE_STORAGE_PATH"):
            init_local(link / "home", "synthetic-project", USERNAME, PASSWORD)

    @unittest.skipUnless(os.name == "posix", "Windows ACL behavior is not verified by POSIX modes")
    def test_posix_private_modes_and_insecure_config_fail_closed(self):
        home = self.root / "home"
        init_local(home, "synthetic-project", USERNAME, PASSWORD)
        self.assertEqual(home.stat().st_mode & 0o777, 0o700)
        for filename in (CONFIG_NAME, DATABASE_NAME):
            self.assertEqual((home / filename).stat().st_mode & 0o777, 0o600)
        (home / CONFIG_NAME).chmod(0o644)
        with self.assertRaisesRegex(ContextError, "INSECURE_STORAGE_PERMISSIONS"):
            load_local(home)


if __name__ == "__main__":
    unittest.main()
