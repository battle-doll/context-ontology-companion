"""Transactional context domain; callers supply a trusted adapter principal.

This module is not an authentication provider. Approval is intentionally absent
from the model-facing tool dispatcher. OS administrators remain trusted locally.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re
import secrets
import sqlite3

MAX_BYTES = 65_536
ORIGINS = {"user_asserted", "source_observed", "model_inferred"}


class ContextError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class Principal:
    """Resolved by a trusted local session, never from tool arguments."""
    subject: str


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value):
        raise ContextError("INVALID_TIME")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        raise ContextError("INVALID_TIME") from None


def stamp(value):
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def text_field(value, maximum=4000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or any(ord(c) < 32 and c not in "\n\t" for c in value):
        raise ContextError("INVALID_INPUT")
    return value


def validate_project(value):
    text_field(value,160)
    if not re.fullmatch(r"[^\s\x00-\x1f\x7f]+",value):
        raise ContextError("INVALID_PROJECT_ID")
    return value


def validate_candidate(candidate):
    if not isinstance(candidate, dict) or set(candidate) != {"statement", "kind", "origin", "evidence", "valid_from", "valid_until"}:
        raise ContextError("INVALID_INPUT")
    if len(canonical(candidate).encode()) > MAX_BYTES:
        raise ContextError("INPUT_TOO_LARGE")
    text_field(candidate["statement"])
    if not isinstance(candidate["kind"],str) or not isinstance(candidate["origin"],str) or candidate["kind"] not in {"decision", "requirement", "constraint"} or candidate["origin"] not in ORIGINS:
        raise ContextError("INVALID_INPUT")
    start = timestamp(candidate["valid_from"])
    end = candidate["valid_until"]
    if end is not None and timestamp(end) <= start:
        raise ContextError("INVALID_TIME")
    evidence = candidate["evidence"]
    if not isinstance(evidence, list) or not 1 <= len(evidence) <= 8:
        raise ContextError("INVALID_EVIDENCE")
    ids = set()
    for item in evidence:
        if not isinstance(item, dict) or set(item) != {"id", "origin", "locator"}:
            raise ContextError("INVALID_EVIDENCE")
        text_field(item["id"], 160)
        text_field(item["locator"], 500)
        if not isinstance(item["origin"],str) or item["origin"] not in ORIGINS or item["id"] in ids:
            raise ContextError("INVALID_EVIDENCE")
        ids.add(item["id"])
    if candidate["origin"] not in {e["origin"] for e in evidence}:
        raise ContextError("INVALID_EVIDENCE")
    # Defense in depth, not a guarantee of detecting arbitrary sensitive prose.
    raw = canonical(candidate)
    if re.search(r"(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{20,}|-----BEGIN .*PRIVATE KEY|\b\d{3}-\d{2}-\d{4}\b)", raw):
        raise ContextError("SENSITIVE_INPUT_REJECTED")
    return json.loads(raw)


class Store:
    def __init__(self, path: Path, clock=None):
        self.path = Path(path)
        if any(p.is_symlink() or (hasattr(p,"is_junction") and p.is_junction()) for p in (self.path,*self.path.parents)):
            raise ContextError("UNSAFE_STORAGE_PATH")
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA secure_delete=ON")
        self.db.execute("PRAGMA journal_mode=DELETE")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS projects(subject TEXT, project TEXT, PRIMARY KEY(subject,project));
          CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY, subject TEXT, project TEXT,
            revision INTEGER, status TEXT, body TEXT, recorded_at TEXT);
          CREATE TABLE IF NOT EXISTS history(record_id TEXT, revision INTEGER, status TEXT, body TEXT, at TEXT);
          CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY, subject TEXT, project TEXT,
            operation TEXT, target TEXT, expected_revision INTEGER, payload TEXT, digest TEXT,
            nonce TEXT, expires TEXT, idem TEXT, state TEXT, result_id TEXT,
            UNIQUE(subject,project,idem));
          CREATE TABLE IF NOT EXISTS relations(subject TEXT, project TEXT, source TEXT, target TEXT, kind TEXT);
        """)

    def close(self):
        self.db.close()

    def _transaction(self, fn):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            result = fn()
            self.db.execute("COMMIT")
            return result
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def provision_project(self, principal, project):
        """Operator adapter only; never an MCP tool."""
        text_field(principal.subject, 160)
        validate_project(project)
        self.db.execute("INSERT OR IGNORE INTO projects VALUES (?,?)", (principal.subject, project))

    def _access(self, p, project):
        if not isinstance(p, Principal) or not self.db.execute("SELECT 1 FROM projects WHERE subject=? AND project=?", (p.subject, project)).fetchone():
            raise ContextError("NOT_FOUND_OR_FORBIDDEN")

    def list_projects(self, p):
        return {"projects": [r[0] for r in self.db.execute("SELECT project FROM projects WHERE subject=? ORDER BY project", (p.subject,))]}

    def _record(self, p, record_id):
        row = self.db.execute("SELECT * FROM records WHERE id=? AND subject=? AND status!='deleted'", (record_id, p.subject)).fetchone()
        if not row:
            raise ContextError("NOT_FOUND_OR_FORBIDDEN")
        self._access(p, row["project"])
        return row

    def _display(self, row):
        return {"id": row["id"], "scope": row["project"], "revision": row["revision"], "status": row["status"], "recorded_at": row["recorded_at"], **json.loads(row["body"])}

    def fetch(self, p, record_id):
        return self._display(self._record(p, record_id))

    def history(self, p, record_id):
        self._record(p, record_id)
        rows=self.db.execute("SELECT * FROM history WHERE record_id=? ORDER BY revision LIMIT 201", (record_id,)).fetchall()
        if len(rows)>200: raise ContextError("RESULT_TOO_LARGE")
        return {"history": [{"revision": r["revision"], "status": r["status"], "at": r["at"], "record": json.loads(r["body"])} for r in rows]}

    def search(self, p, project, query=""):
        self._access(p, project)
        if not isinstance(query, str) or len(query) > 500:
            raise ContextError("INVALID_INPUT")
        now = self.clock()
        rows = self.db.execute("SELECT * FROM records WHERE subject=? AND project=? AND status='active' ORDER BY id LIMIT 201", (p.subject, project)).fetchall()
        if len(rows)>200: raise ContextError("RESULT_TOO_LARGE")
        matches = []
        for row in rows:
            r = self._display(row)
            if timestamp(r["valid_from"]) > now or (r["valid_until"] and timestamp(r["valid_until"]) <= now):
                continue
            if query.casefold() in r["statement"].casefold():
                matches.append(r)
        if len(matches) > 200 or len(canonical(matches).encode()) > 1_048_576:
            raise ContextError("RESULT_TOO_LARGE")
        return {"records": matches, "knowledge_time": "current", "external_verification": "not_checked"}

    def prepare(self, p, project, operation, idempotency_key, candidate=None, target=None, expected_revision=None):
        self._access(p, project)
        text_field(idempotency_key, 160)
        if not isinstance(operation,str) or operation not in {"create", "supersede", "contradict", "revoke", "erase"}:
            raise ContextError("INVALID_INPUT")
        if operation in {"create", "supersede", "contradict"}:
            candidate = validate_candidate(candidate)
        elif candidate is not None:
            raise ContextError("INVALID_INPUT")
        if operation == "create":
            if target is not None or expected_revision is not None:
                raise ContextError("INVALID_INPUT")
        elif not isinstance(target, str) or type(expected_revision) is not int or expected_revision < 1:
            raise ContextError("INVALID_INPUT")
        payload = {"operation": operation, "target": target, "expected_revision": expected_revision, "candidate": candidate}
        hashed = digest(payload)
        def write():
            previous = self.db.execute("SELECT * FROM proposals WHERE subject=? AND project=? AND idem=?", (p.subject, project, idempotency_key)).fetchone()
            if previous:
                if previous["digest"] != hashed:
                    raise ContextError("IDEMPOTENCY_CONFLICT")
                return self.change_status(p, previous["id"])
            if target is not None:
                row = self._record(p, target)
                if row["project"] != project:
                    raise ContextError("NOT_FOUND_OR_FORBIDDEN")
                if row["revision"] != expected_revision:
                    raise ContextError("REVISION_CONFLICT")
                if operation in {"supersede", "contradict", "revoke"} and row["status"] != "active":
                    raise ContextError("REVISION_CONFLICT")
            count = self.db.execute("SELECT count(*) FROM proposals WHERE subject=? AND state='pending' AND expires>?", (p.subject,stamp(self.clock()))).fetchone()[0]
            if count >= 100:
                raise ContextError("TOO_MANY_PENDING_CHANGES")
            pid = "change_" + secrets.token_hex(16)
            self.db.execute("INSERT INTO proposals VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (pid, p.subject, project, operation, target, expected_revision, canonical(payload), hashed, secrets.token_urlsafe(32), stamp(self.clock()+timedelta(minutes=15)), idempotency_key, "pending", None))
            return self.change_status(p, pid)
        return self._transaction(write)

    def _proposal(self, p, pid):
        row = self.db.execute("SELECT * FROM proposals WHERE id=? AND subject=?", (pid, p.subject)).fetchone()
        if not row:
            raise ContextError("NOT_FOUND_OR_FORBIDDEN")
        self._access(p, row["project"])
        return row

    def change_status(self, p, pid):
        row = self._proposal(p, pid)
        state = row["state"]
        if state == "pending" and timestamp(row["expires"]) <= self.clock():
            state = "expired"
        # Do not expose the approval nonce or payload digest to model tools.
        return {"proposal_id": pid, "state": state, "record_id": row["result_id"] if state == "applied" else None, "expires_at": row["expires"]}

    def review(self, p, pid):
        """Authenticated human adapter only."""
        row = self._proposal(p, pid)
        if self.change_status(p, pid)["state"] != "pending":
            raise ContextError("APPROVAL_NOT_PENDING")
        payload = json.loads(row["payload"])
        return {"proposal_id": pid, "scope": row["project"], "payload": payload, "digest": row["digest"], "nonce": row["nonce"], "target_record": self.fetch(p, row["target"]) if row["target"] else None, "expires_at": row["expires"]}

    def approve(self, p, pid, expected_digest, nonce):
        """Trusted human adapter only. Compare and consume inside one transaction."""
        def apply():
            row = self._proposal(p, pid)
            if self.change_status(p, pid)["state"] != "pending":
                raise ContextError("APPROVAL_NOT_PENDING")
            if not isinstance(expected_digest, str) or not isinstance(nonce, str) or not secrets.compare_digest(row["digest"], expected_digest) or not secrets.compare_digest(row["nonce"], nonce) or digest(json.loads(row["payload"])) != expected_digest:
                raise ContextError("APPROVAL_MISMATCH")
            payload = json.loads(row["payload"])
            operation, target = row["operation"], row["target"]
            if target:
                old = self._record(p, target)
                if old["project"] != row["project"] or old["revision"] != row["expected_revision"]:
                    raise ContextError("REVISION_CONFLICT")
                if operation in {"supersede", "contradict", "revoke"} and old["status"] != "active":
                    raise ContextError("REVISION_CONFLICT")
            now = stamp(self.clock())
            result_id = target
            if operation in {"supersede", "revoke"}:
                status = "superseded" if operation == "supersede" else "revoked"
                self.db.execute("UPDATE records SET status=?,revision=revision+1 WHERE id=?", (status, target))
                self.db.execute("INSERT INTO history VALUES (?,?,?,?,?)", (target, old["revision"]+1, status, old["body"], now))
            if operation in {"create", "supersede", "contradict"}:
                candidate = validate_candidate(payload["candidate"])
                result_id = "ctx_"+secrets.token_hex(16)
                self.db.execute("INSERT INTO records VALUES (?,?,?,?,?,?,?)", (result_id,p.subject,row["project"],1,"active",canonical(candidate),now))
                self.db.execute("INSERT INTO history VALUES (?,?,?,?,?)", (result_id,1,"active",canonical(candidate),now))
                if target:
                    self.db.execute("INSERT INTO relations VALUES (?,?,?,?,?)", (p.subject,row["project"],result_id,target,"contradicts" if operation == "contradict" else "supersedes"))
            if operation == "erase":
                self.db.execute("UPDATE records SET body='{}',status='deleted',revision=revision+1 WHERE id=?", (target,))
                self.db.execute("DELETE FROM history WHERE record_id=?", (target,))
                self.db.execute("DELETE FROM relations WHERE source=? OR target=?", (target,target))
                # Scrub every pending or applied copy, including creation proposal.
                self.db.execute("UPDATE proposals SET payload='{}',nonce='',state='erased',result_id=NULL WHERE subject=? AND (target=? OR result_id=?)", (p.subject,target,target))
            # Applied proposal retains no knowledge payload or nonce.
            self.db.execute("UPDATE proposals SET state='applied',result_id=?,payload='{}',nonce='' WHERE id=?", (result_id,pid))
            return self.change_status(p, pid)
        return self._transaction(apply)

    def purge_expired(self):
        """Operator maintenance; no implicit write in read-only tool handlers."""
        self.db.execute("UPDATE proposals SET payload='{}',nonce='',state='expired' WHERE state='pending' AND expires<=?", (stamp(self.clock()),))

    def pack(self, p, project, query="", max_chars=12000):
        self.db.execute("BEGIN")
        try:
            result=self._pack(p,project,query,max_chars)
            self.db.execute("COMMIT")
            return result
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def _pack(self, p, project, query, max_chars):
        if type(max_chars) is not int or not 1 <= max_chars <= 100_000:
            raise ContextError("INVALID_INPUT")
        all_rows = {r["id"]:r for r in self.search(p, project)["records"]}
        if not isinstance(query,str) or len(query)>500:
            raise ContextError("INVALID_INPUT")
        matched = {rid for rid,r in all_rows.items() if query.casefold() in r["statement"].casefold()}
        selected = matched | {rid for rid,r in all_rows.items() if r["kind"] in {"constraint","requirement"}}
        edges = [dict(r) for r in self.db.execute("SELECT source,target,kind FROM relations WHERE subject=? AND project=? AND kind='contradicts'", (p.subject, project)) if r["source"] in all_rows and r["target"] in all_rows]
        changed = True
        while changed:
            before = len(selected)
            for edge in edges:
                if edge["source"] in selected or edge["target"] in selected:
                    selected.update((edge["source"],edge["target"]))
            changed = len(selected) != before
        content = {"scope":project,"records":[all_rows[rid] for rid in sorted(selected)],"contradictions":[e for e in edges if e["source"] in selected],"evidence_authority":"data_only_not_execution_permission"}
        result={"status":"complete","required_chars":0,"pack":content}
        size=0
        while len(canonical(result))!=size:
            size=len(canonical(result))
            result["required_chars"]=size
        if size > max_chars:
            return {"status":"insufficient_budget","required_chars":size,"pack":None}
        return result

    def export(self, p, project):
        rows = self.search(p, project)["records"]
        evidence, decisions = [], []
        for r in rows:
            refs = []
            for i,e in enumerate(r["evidence"]):
                eid = r["id"]+"_e"+str(i)
                evidence.append({**e,"id":eid,"scope":project})
                refs.append(eid)
            decisions.append({"id":r["id"],"statement":r["statement"],"kind":r["kind"],"origin":r["origin"],"evidence_refs":refs,"valid_from":r["valid_from"],"valid_until":r["valid_until"],"recorded_at":r["recorded_at"]})
        artifact={"contract_version":"0.1.0-draft.1","profile":"context-decision","artifact_id":"export_"+digest(decisions)[:24],"producer":{"name":"context-ontology-companion","version":"0.1.0-draft.1"},"evidence":evidence,"payload":{"scope":project,"decisions":decisions}}
        from companion_contracts import validate_artifact
        if validate_artifact(artifact)["status"]!="valid":
            raise ContextError("EXPORT_CONTRACT_LIMIT_OR_MISMATCH")
        return artifact
