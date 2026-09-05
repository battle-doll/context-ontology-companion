"""CLI and optional local stdio JSON-RPC adapter. No network or file writes."""
from __future__ import annotations

import argparse
import json
import sys

from .validator import (CONTRACT_VERSION, MAX_BYTES, PROFILES, InvalidInput, _parse,
                        compatibility, migration_plan, read_artifact, validate_bytes)


def _object(properties, required=None):
    return {"type": "object", "properties": properties,
            "required": list(properties) if required is None else required, "additionalProperties": False}


STRING = {"type": "string"}
NULL_STRING = {"type": ["string", "null"]}
STRINGS = {"type": "array", "items": STRING}
ERROR = _object({"pointer": STRING, "rule_id": STRING, "message": STRING})
VALIDATION_OUTPUT = _object({"status": {"type": "string", "enum": ["valid", "invalid", "unsupported"]},
    "contract_version": NULL_STRING, "profile": NULL_STRING,
    "layers": _object({key: {"type": "string", "enum": ["valid", "invalid", "unsupported", "not_checked"]}
                       for key in ("L0_parse", "L1_schema", "L2_profile", "L3_compatibility", "external_verification")}),
    "errors": {"type": "array", "maxItems": 32, "items": ERROR}, "not_checked": STRINGS})
COMPATIBILITY_OUTPUT = _object({"status": {"type": "string", "enum": ["compatible", "unsupported"]},
    "producer_version": NULL_STRING, "consumer_version": NULL_STRING, "profile": NULL_STRING,
    "basis": STRING, "direction": {"type": "string", "const": "producer_to_consumer"},
    "consumer_runtime": {"type": "string", "const": "not_checked"}})
MIGRATION_OUTPUT = _object({"status": {"type": "string", "enum": ["identity_plan", "unsupported"]},
    "writes_performed": {"type": "boolean", "const": False}, "source_validation": VALIDATION_OUTPUT,
    "target_version": NULL_STRING, "target_profile": NULL_STRING, "preserved": STRINGS,
    "transformed": STRINGS, "losses": STRINGS, "not_checked": STRINGS})
BOUNDED = {"type": "string", "minLength": 1, "maxLength": 160}
ARTIFACT_JSON = {"type": "string", "minLength": 1, "maxLength": MAX_BYTES}
ANNOTATIONS = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
TOOLS = [
    {"name": "validate_artifact", "description": "Validate explicitly supplied ontology artifact JSON offline against bundled draft profiles. No truth, identity, runtime, or authorization check.",
     "inputSchema": _object({"artifact_json": ARTIFACT_JSON}), "outputSchema": VALIDATION_OUTPUT,
     "annotations": dict(ANNOTATIONS)},
    {"name": "compare_versions", "description": "Check the explicit bundled producer-to-reader version/profile fixture pairing. Does not test an installed consumer.",
     "inputSchema": _object({"producer_version": BOUNDED, "consumer_version": BOUNDED, "profile": BOUNDED}),
     "outputSchema": COMPATIBILITY_OUTPUT, "annotations": dict(ANNOTATIONS)},
    {"name": "plan_migration", "description": "Return a plan only. Only same-profile same-version identity preservation is supported; other migrations remain unsupported. Writes no files.",
     "inputSchema": _object({"artifact_json": ARTIFACT_JSON, "target_version": BOUNDED, "target_profile": BOUNDED}, ["artifact_json", "target_version"]),
     "outputSchema": MIGRATION_OUTPUT, "annotations": dict(ANNOTATIONS)},
]


def invoke(name, arguments):
    tool = next((row for row in TOOLS if row["name"] == name), None)
    if not tool or not isinstance(arguments, dict):
        raise InvalidInput("unknown_tool_or_arguments")
    schema = tool["inputSchema"]
    if set(arguments) - set(schema["properties"]) or set(schema["required"]) - set(arguments):
        raise InvalidInput("tool_arguments")
    for key, value in arguments.items():
        limit = schema["properties"][key]["maxLength"]
        if not isinstance(value, str) or not 1 <= len(value) <= limit:
            raise InvalidInput("tool_arguments")
    if name == "validate_artifact":
        return validate_bytes(arguments["artifact_json"].encode("utf-8"))
    if name == "compare_versions":
        return compatibility(arguments["producer_version"], arguments["consumer_version"], arguments["profile"])
    return plan_bytes(arguments["artifact_json"].encode("utf-8"), arguments["target_version"], arguments.get("target_profile"))


def plan_bytes(raw, target_version, target_profile=None):
    try:
        artifact = _parse(raw)
    except InvalidInput:
        output = migration_plan(None, target_version, target_profile)
        output["source_validation"] = validate_bytes(raw)
        return output
    return migration_plan(artifact, target_version, target_profile)


def _response(request_id, result=None, code=None, message=None):
    value = {"jsonrpc": "2.0", "id": request_id}
    value["error" if code else "result"] = {"code": code, "message": message} if code else result
    return value


def serve_stdin():
    """Bounded newline JSON-RPC subset for initialize, ping and tools methods.

    Local smoke tests cover this transport; external MCP host integration is a
    separate gate. No automatic host/server registration is performed.
    """
    initialized = False
    while True:
        raw = sys.stdin.buffer.readline(MAX_BYTES + 1)
        if not raw:
            return 0
        request_id = None
        try:
            if len(raw) > MAX_BYTES:
                print(json.dumps(_response(None, code=-32700, message="Request limit exceeded.")), flush=True)
                return 2  # fail closed; never parse the remainder as another request
            request = _parse(raw)
            if not isinstance(request, dict) or request.get("jsonrpc") != "2.0" or not isinstance(request.get("method"), str):
                raise InvalidInput("request")
            request_id = request.get("id")
            if request_id is not None and (type(request_id) not in (str, int) or isinstance(request_id, str) and len(request_id) > 160):
                request_id = None
                raise InvalidInput("request_id")
            method = request["method"]
            params = request.get("params", {})
            if not isinstance(params, dict):
                raise InvalidInput("params")
            if "id" not in request:
                continue
            if method == "initialize":
                initialized = True
                result = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {"listChanged": False}},
                          "serverInfo": {"name": "ontology-companion-contracts", "version": CONTRACT_VERSION}}
            elif not initialized:
                print(json.dumps(_response(request_id, code=-32000, message="Initialize first.")), flush=True)
                continue
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                output = invoke(params.get("name"), params.get("arguments", {}))
                result = {"content": [{"type": "text", "text": json.dumps(output, sort_keys=True)}],
                          "structuredContent": output, "isError": False}
            else:
                print(json.dumps(_response(request_id, code=-32601, message="Method not found.")), flush=True)
                continue
            print(json.dumps(_response(request_id, result=result), sort_keys=True), flush=True)
        except (InvalidInput, UnicodeError, ValueError):
            print(json.dumps(_response(request_id, code=-32602, message="Invalid or unsupported request.")), flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline bounded ontology contract validator (draft; no authorization checks).")
    parser.add_argument("--version", action="version", version=CONTRACT_VERSION)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="Validate one explicitly selected regular JSON file; never modifies it.")
    validate.add_argument("path")
    pair = commands.add_parser("compatibility", help="Check a bundled producer-to-reader fixture pairing.")
    pair.add_argument("--producer-version", required=True)
    pair.add_argument("--consumer-version", required=True)
    pair.add_argument("--profile", required=True)
    migrate = commands.add_parser("migration-plan", help="Produce an identity plan or explicit unsupported result; writes nothing.")
    migrate.add_argument("path")
    migrate.add_argument("--target-version", required=True)
    migrate.add_argument("--target-profile")
    commands.add_parser("tools", help="Print implemented local tool descriptors.")
    commands.add_parser("stdio", help="Run optional local stdio JSON-RPC tools; no registration performed.")
    args = parser.parse_args(argv)
    if args.command == "stdio":
        return serve_stdin()
    try:
        if args.command == "validate":
            output = validate_bytes(read_artifact(args.path))
        elif args.command == "compatibility":
            output = compatibility(args.producer_version, args.consumer_version, args.profile)
        elif args.command == "migration-plan":
            raw = read_artifact(args.path)
            output = plan_bytes(raw, args.target_version, args.target_profile)
        else:
            output = {"tools": TOOLS}
        print(json.dumps(output, indent=2, sort_keys=True, ensure_ascii=True))
        return 0 if output.get("status") in (None, "valid", "compatible", "identity_plan") else 2
    except (OSError, InvalidInput):
        print(json.dumps({"status": "invalid", "errors": [{"pointer": "", "rule_id": "input_file", "message": "Selected file is unavailable, unsafe, or unsupported."}]}))
        return 2
