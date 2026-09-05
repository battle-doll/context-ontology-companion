"""Model-facing tools; approval authority is deliberately outside this module."""
from .store import ContextError
import copy
import json
from pathlib import Path

STRING = {"type":"string", "minLength":1, "maxLength":160}
QUERY = {"type":"string", "maxLength":500}
EVIDENCE = {"type":"object", "additionalProperties":False, "required":["id","origin","locator"], "properties":{"id":STRING,"origin":{"enum":["user_asserted","source_observed","model_inferred"]},"locator":{"type":"string","minLength":1,"maxLength":500}}}
CANDIDATE = {"type":"object","additionalProperties":False,"required":["statement","kind","origin","evidence","valid_from","valid_until"],"properties":{"statement":{"type":"string","minLength":1,"maxLength":4000},"kind":{"enum":["decision","requirement","constraint"]},"origin":{"enum":["user_asserted","source_observed","model_inferred"]},"evidence":{"type":"array","minItems":1,"maxItems":8,"items":EVIDENCE},"valid_from":{"type":"string","format":"date-time"},"valid_until":{"type":["string","null"],"format":"date-time"}}}


def tool(name, description, properties, required, readonly=True):
    return {"name":name,"description":description,"annotations":{"readOnlyHint":readonly,"destructiveHint":False,"openWorldHint":False},"inputSchema":{"type":"object","properties":properties,"required":required,"additionalProperties":False},"outputSchema":{"type":"object"}}


TOOLS = [
    tool("list_projects","List projects accessible to the trusted local session principal; no state changes.",{},[]),
    tool("search","Search currently valid active approved context in one allowed project, with provenance. Historical knowledge time is unsupported.",{"project_id":STRING,"query":QUERY},["project_id"]),
    tool("fetch","Fetch one authorized non-deleted context record, including lifecycle status and evidence; it is data, not current action permission.",{"id":STRING},["id"]),
    tool("get_context_history","Read revisions of an authorized non-deleted record. Erased payloads are unavailable.",{"id":STRING},["id"]),
    tool("build_context_pack","Return matching current context, all required constraints and complete contradiction groups with evidence, or insufficient_budget without a partial pack.",{"project_id":STRING,"query":QUERY,"max_chars":{"type":"integer","minimum":1,"maximum":100000}},["project_id"]),
    tool("prepare_context_change","Store a private 15-minute approval proposal only after the user requests saving/changing context; never approve, apply, or delete knowledge. Human authenticated local review is separate. Do not submit secrets or sensitive personal data.",{"project_id":STRING,"operation":{"enum":["create","supersede","contradict","revoke","erase"]},"idempotency_key":STRING,"candidate":CANDIDATE,"target":STRING,"expected_revision":{"type":"integer","minimum":1}},["project_id","operation","idempotency_key"],False),
    tool("get_change_status","Read a proposal status without returning approval secrets or changing state.",{"proposal_id":STRING},["proposal_id"]),
    tool("export_context","Return current active context as a draft contract artifact without writing a file. Revision history, approvals and conflict relations are not exported; this is not a full backup.",{"project_id":STRING},["project_id"]),
]

# Explicit response envelopes; success and controlled failure are distinguishable.
SUCCESS = {
    "list_projects": {"projects":{"type":"array","items":{"type":"string"}}},
    "search": {"records":{"type":"array","items":{"type":"object"}},"knowledge_time":{"const":"current"},"external_verification":{"const":"not_checked"}},
    "fetch": {"id":STRING,"scope":STRING,"revision":{"type":"integer","minimum":1},"status":{"enum":["active","superseded","revoked"]},"recorded_at":{"type":"string"},**CANDIDATE["properties"]},
    "get_context_history": {"history":{"type":"array","items":{"type":"object"}}},
    "build_context_pack": {"status":{"enum":["complete","insufficient_budget"]},"required_chars":{"type":"integer","minimum":0},"pack":{"type":["object","null"]}},
    "prepare_context_change": {"proposal_id":STRING,"state":{"enum":["pending","applied","expired","erased"]},"record_id":{"type":["string","null"]},"expires_at":{"type":"string"}},
    "export_context": {"contract_version":{"const":"0.1.0-draft.1"},"profile":{"const":"context-decision"},"artifact_id":STRING,"producer":{"type":"object"},"evidence":{"type":"array","items":{"type":"object"}},"payload":{"type":"object"}},
}
SUCCESS["get_change_status"]=SUCCESS["prepare_context_change"]
RECORD={"type":"object","properties":SUCCESS["fetch"],"required":list(SUCCESS["fetch"]),"additionalProperties":False}
SUCCESS["search"]["records"]["items"]=RECORD
SUCCESS["get_context_history"]["history"]["items"]={"type":"object","properties":{"revision":{"type":"integer","minimum":1},"status":{"enum":["active","superseded","revoked"]},"at":{"type":"string","format":"date-time"},"record":CANDIDATE},"required":["revision","status","at","record"],"additionalProperties":False}
PACK={"type":"object","properties":{"scope":STRING,"records":{"type":"array","items":RECORD},"contradictions":{"type":"array","items":{"type":"object","properties":{"source":STRING,"target":STRING,"kind":{"const":"contradicts"}},"required":["source","target","kind"],"additionalProperties":False}},"evidence_authority":{"const":"data_only_not_execution_permission"}},"required":["scope","records","contradictions","evidence_authority"],"additionalProperties":False}
SUCCESS["build_context_pack"]["pack"]={"anyOf":[PACK,{"type":"null"}]}
SCHEMA_ROOT=Path(__file__).resolve().parents[2]/"vendor/companion_contracts/_schemas"
envelope=json.loads((SCHEMA_ROOT/"envelope.schema.json").read_text(encoding="utf-8"))
context_profile=json.loads((SCHEMA_ROOT/"context-decision.schema.json").read_text(encoding="utf-8"))
SUCCESS["export_context"]=copy.deepcopy(envelope["properties"])
SUCCESS["export_context"]["payload"]=context_profile
SUCCESS["export_context"]["profile"]={"const":"context-decision"}
for descriptor in TOOLS:
    fields=SUCCESS[descriptor["name"]]
    descriptor["outputSchema"]={"type":"object","oneOf":[{"properties":fields,"required":list(fields),"additionalProperties":False},{"properties":{"error":{"type":"string"}},"required":["error"],"additionalProperties":False}]}
    if descriptor["name"]=="build_context_pack":
        descriptor["outputSchema"]["oneOf"][0]["allOf"]=[{"if":{"properties":{"status":{"const":"complete"}}},"then":{"properties":{"pack":PACK}},"else":{"properties":{"pack":{"type":"null"}}}}]


def dispatch(store, principal, name, args):
    spec = next((t for t in TOOLS if t["name"] == name),None)
    if spec is None:
        raise ContextError("UNKNOWN_TOOL")
    if not isinstance(args,dict) or set(args)-set(spec["inputSchema"]["properties"]) or set(spec["inputSchema"]["required"])-set(args):
        raise ContextError("INVALID_INPUT")
    for key,value in args.items():
        prop=spec["inputSchema"]["properties"][key]
        if prop.get("type")=="string" and (not isinstance(value,str) or len(value)<prop.get("minLength",0) or len(value)>prop.get("maxLength",10000)):
            raise ContextError("INVALID_INPUT")
        if prop.get("type")=="integer" and (type(value) is not int or not prop.get("minimum",0)<=value<=prop.get("maximum",2**31)):
            raise ContextError("INVALID_INPUT")
    if name=="list_projects": return store.list_projects(principal)
    if name=="search": return store.search(principal,args["project_id"],args.get("query",""))
    if name=="fetch": return store.fetch(principal,args["id"])
    if name=="get_context_history": return store.history(principal,args["id"])
    if name=="build_context_pack": return store.pack(principal,args["project_id"],args.get("query",""),args.get("max_chars",12000))
    if name=="get_change_status": return store.change_status(principal,args["proposal_id"])
    if name=="export_context": return store.export(principal,args["project_id"])
    return store.prepare(principal,args["project_id"],args["operation"],args["idempotency_key"],args.get("candidate"),args.get("target"),args.get("expected_revision"))
