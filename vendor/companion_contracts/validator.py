"""Bounded stdlib validator for the bundled schema subset, never remote schemas.

Schema metadata ($schema/$id) is descriptive. Only trusted local schema files are
loaded; this is deliberately not a general purpose JSON Schema implementation.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
from pathlib import Path
import re
import stat

CONTRACT_VERSION = "0.1.0-draft.1"
CO_NAMESPACE = "https://battle-doll.github.io/code-ontology-explorer/schema#"
PROFILES = ("context-decision", "code-reference")
MAX_BYTES = 524288
MAX_DEPTH = 32
MAX_NODES = 20000
MAX_ITEMS = 1000
MAX_STRING = 8192
MAX_ERRORS = 32
LAYERS = ("L0_parse", "L1_schema", "L2_profile", "L3_compatibility", "external_verification")
NOT_CHECKED = ["content_truth", "source_access", "current_authorization", "runtime_behavior",
               "producer_identity", "consumer_runtime", "archive_completeness"]
_SCHEMAS = Path(__file__).parent / "_schemas"


class InvalidInput(ValueError):
    """An input error containing only a bounded, non-payload diagnostic."""


def _result(status="invalid", artifact=None):
    artifact = artifact if isinstance(artifact, dict) else {}
    # Never reflect arbitrary caller strings in diagnostic metadata.
    return {"status": status,
            "contract_version": CONTRACT_VERSION if artifact.get("contract_version") == CONTRACT_VERSION else None,
            "profile": artifact.get("profile") if artifact.get("profile") in PROFILES else None,
            "layers": {key: "not_checked" for key in LAYERS},
            "errors": [], "not_checked": list(NOT_CHECKED)}


def _error(result, pointer, rule, message):
    if len(result["errors"]) < MAX_ERRORS:
        result["errors"].append({"pointer": pointer[:512], "rule_id": rule, "message": message})


def _pointer(parent, key):
    # Schema errors refer to public field names/indexes, never unknown user keys.
    return parent + "/" + str(key).replace("~", "~0").replace("/", "~1")


def _pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise InvalidInput("duplicate_key")
        obj[key] = value
    return obj


def _constant(_):
    raise InvalidInput("non_finite_number")


def _bounded(value):
    pending = [(value, 0)]
    nodes = 0
    while pending:
        item, depth = pending.pop()
        nodes += 1
        if depth > MAX_DEPTH or nodes > MAX_NODES:
            raise InvalidInput("structure_limit")
        if isinstance(item, str) and len(item) > MAX_STRING:
            raise InvalidInput("string_limit")
        if isinstance(item, str) and any(0xD800 <= ord(c) <= 0xDFFF for c in item):
            raise InvalidInput("unicode_scalar")
        if isinstance(item, float) and not math.isfinite(item):
            raise InvalidInput("non_finite_number")
        if isinstance(item, (dict, list)):
            if len(item) > MAX_ITEMS:
                raise InvalidInput("collection_limit")
            if isinstance(item, dict):
                pending.extend((key, depth + 1) for key in item)
                pending.extend((part, depth + 1) for part in item.values())
            else:
                pending.extend((part, depth + 1) for part in item)


def _parse(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
        raise InvalidInput("byte_limit")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
        _bounded(value)
        return value
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        if isinstance(exc, InvalidInput):
            raise
        raise InvalidInput("json_parse") from None


def read_artifact(path):
    """Read at most MAX_BYTES+1, reject nonregular files and final symlinks.

    Ancestor symlinks are allowed for normal OS paths such as macOS /tmp. This
    function accepts only the explicitly selected file, never directories/ZIPs.
    """
    selected = Path(path)
    before = selected.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise InvalidInput("regular_file_required")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(selected, flags)
    with os.fdopen(descriptor, "rb") as stream:
        after = os.fstat(stream.fileno())
        if not stat.S_ISREG(after.st_mode) or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise InvalidInput("file_changed")
        return stream.read(MAX_BYTES + 1)


def _type(value, name):
    return {"object": isinstance(value, dict), "array": isinstance(value, list),
            "string": isinstance(value, str), "integer": type(value) is int or type(value) is float and value.is_integer(),
            "null": value is None, "boolean": type(value) is bool}.get(name, False)


def _schema(value, schema, result, pointer=""):
    expected = schema.get("type")
    names = expected if isinstance(expected, list) else [expected]
    if expected and not any(_type(value, name) for name in names):
        _error(result, pointer, "type", "Value has the wrong JSON type.")
        return
    if "const" in schema and value != schema["const"]:
        _error(result, pointer, "constant", "Value does not match the supported constant.")
    if "enum" in schema and value not in schema["enum"]:
        _error(result, pointer, "enum", "Value is outside the supported enumeration.")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                _error(result, _pointer(pointer, key), "required", "Required field is missing.")
        if schema.get("additionalProperties") is False and set(value) - set(props):
            _error(result, pointer, "additional_properties", "Object contains unsupported fields.")
        for key, subschema in props.items():
            if key in value:
                _schema(value[key], subschema, result, _pointer(pointer, key))
    elif isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", MAX_ITEMS):
            _error(result, pointer, "array_bounds", "Array length is outside supported bounds.")
        if schema.get("uniqueItems") and len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            _error(result, pointer, "unique_items", "Array elements must be unique.")
        for index, item in enumerate(value):
            _schema(item, schema.get("items", {}), result, _pointer(pointer, index))
    elif isinstance(value, str):
        if not schema.get("minLength", 0) <= len(value) <= schema.get("maxLength", MAX_STRING):
            _error(result, pointer, "string_bounds", "String length is outside supported bounds.")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            _error(result, pointer, "pattern", "String does not match the supported format.")
    elif type(value) in (int, float):
        if value < schema.get("minimum", value) or value > schema.get("maximum", value):
            _error(result, pointer, "integer_bounds", "Integer is outside supported bounds.")


def _time(value, result, pointer):
    if value is None:
        return None
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", value):
        _error(result, pointer, "utc_timestamp", "Timestamp must be ISO 8601 UTC ending in Z.")
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        _error(result, pointer, "calendar_timestamp", "Timestamp is not a valid calendar date.")
        return None


def _portable(path):
    return bool(path) and not (path.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", path)
        or "\\" in path or any(part in ("", ".", "..") for part in path.split("/"))
        or any(ord(c) < 32 or ord(c) == 127 for c in path))


def _semantics(artifact, result):
    evidence = {}
    for index, item in enumerate(artifact["evidence"]):
        if item["id"] in evidence:
            _error(result, f"/evidence/{index}/id", "duplicate_id", "Evidence IDs must be unique.")
        evidence[item["id"]] = item
    payload = artifact["payload"]
    scope = payload["scope"] if artifact["profile"] == "context-decision" else payload["repository"]
    for index, item in enumerate(artifact["evidence"]):
        if item["scope"] != scope:
            _error(result, f"/evidence/{index}/scope", "evidence_scope", "Evidence must belong to the payload scope.")

    def refs(row, pointer):
        values = []
        for index, ref in enumerate(row["evidence_refs"]):
            if ref not in evidence:
                _error(result, f"{pointer}/evidence_refs/{index}", "dangling_evidence", "Evidence reference does not resolve.")
            else:
                values.append(evidence[ref])
        return values

    rows = payload["decisions"] if artifact["profile"] == "context-decision" else payload["symbols"]
    key = "decisions" if artifact["profile"] == "context-decision" else "symbols"
    ids = set()
    for index, row in enumerate(rows):
        pointer = f"/payload/{key}/{index}"
        if row["id"] in ids:
            _error(result, pointer + "/id", "duplicate_id", "Payload IDs must be unique.")
        ids.add(row["id"])
        sources = refs(row, pointer)
        if key == "decisions":
            start = _time(row["valid_from"], result, pointer + "/valid_from")
            end = _time(row["valid_until"], result, pointer + "/valid_until")
            _time(row["recorded_at"], result, pointer + "/recorded_at")
            if start and end and end <= start:
                _error(result, pointer + "/valid_until", "interval_order", "Validity interval must have positive duration.")
            if sources and row["origin"] not in {source["origin"] for source in sources}:
                _error(result, pointer + "/origin", "origin_lineage", "Origin must be represented by referenced evidence.")
        else:
            if row["end_line"] < row["start_line"]:
                _error(result, pointer + "/end_line", "span_order", "Source span end precedes start.")
            if not _portable(row["source_path"]):
                _error(result, pointer + "/source_path", "portable_path", "Source path must be a normalized relative path.")
    if key == "symbols":
        for index, relation in enumerate(payload["relations"]):
            pointer = f"/payload/relations/{index}"
            refs(relation, pointer)
            for side in ("source", "target"):
                if relation[side] not in ids:
                    _error(result, pointer + "/" + side, "dangling_symbol", "Relation endpoint does not resolve in this complete reference subset.")


def validate_bytes(raw):
    result = _result()
    try:
        artifact = _parse(raw)
    except InvalidInput as exc:
        result["layers"]["L0_parse"] = "invalid"
        _error(result, "", str(exc), "Input could not be parsed within the supported limits.")
        return result
    result = _result(artifact=artifact)
    result["layers"]["L0_parse"] = "valid"
    if not isinstance(artifact, dict):
        result["layers"]["L1_schema"] = "invalid"
        _error(result, "", "type", "Artifact must be an object.")
        return result
    if ("contract_version" in artifact and artifact["contract_version"] != CONTRACT_VERSION
            or "profile" in artifact and artifact["profile"] not in PROFILES):
        result["status"] = "unsupported"
        result["layers"]["L1_schema"] = "unsupported"
        _error(result, "", "unsupported_contract", "The contract version or profile is not supported.")
        return result
    envelope_schema = json.loads((_SCHEMAS / "envelope.schema.json").read_text(encoding="utf-8"))
    _schema(artifact, envelope_schema, result)
    if artifact.get("profile") in PROFILES:
        profile_schema = json.loads((_SCHEMAS / (artifact["profile"] + ".schema.json")).read_text(encoding="utf-8"))
        _schema(artifact.get("payload"), profile_schema, result, "/payload")
    result["layers"]["L1_schema"] = "invalid" if result["errors"] else "valid"
    if result["errors"]:
        return result
    _semantics(artifact, result)
    result["layers"]["L2_profile"] = "invalid" if result["errors"] else "valid"
    result["status"] = "invalid" if result["errors"] else "valid"
    return result


def validate_artifact(artifact):
    try:
        raw = json.dumps(artifact, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, RecursionError):
        return validate_bytes(b"NaN")
    return validate_bytes(raw)


def compatibility(producer_version, consumer_version, profile):
    supported = producer_version == consumer_version == CONTRACT_VERSION and profile in PROFILES
    return {"status": "compatible" if supported else "unsupported",
            "producer_version": producer_version if producer_version == CONTRACT_VERSION else None,
            "consumer_version": consumer_version if consumer_version == CONTRACT_VERSION else None,
            "profile": profile if profile in PROFILES else None,
            "basis": "bundled synthetic same-version reader fixtures" if supported else "no tested version pairing",
            "direction": "producer_to_consumer", "consumer_runtime": "not_checked"}


def migration_plan(artifact, target_version, target_profile=None):
    validation = validate_artifact(artifact)
    source_profile = artifact.get("profile") if isinstance(artifact, dict) else None
    target_profile = target_profile or source_profile
    identity = (validation["status"] == "valid" and target_version == CONTRACT_VERSION
                and source_profile == target_profile)
    return {"status": "identity_plan" if identity else "unsupported", "writes_performed": False,
            "source_validation": validation,
            "target_version": target_version if target_version == CONTRACT_VERSION else None,
            "target_profile": target_profile if target_profile in PROFILES else None,
            "preserved": ["all supplied fields and values"] if identity else [],
            "transformed": [], "losses": [] if identity else ["No supported loss-aware transformation exists for this request."],
            "not_checked": ["archive_completeness", "external_sources", "authorization"]}
