"""Bounded newline-delimited local MCP. No HTTP endpoint or approval tool."""
import json
import math
import sqlite3
import sys
from .store import Store, ContextError
from .tools import TOOLS, dispatch

PROTOCOL="2025-11-25"
MAX_LINE=131_072


def pairs(items):
    result={}
    for k,v in items:
        if k in result: raise ValueError("duplicate key")
        result[k]=v
    return result


def parse(raw):
    depth=0; in_string=False; escape=False
    for c in raw:
        if in_string:
            if escape: escape=False
            elif c==92: escape=True
            elif c==34: in_string=False
        elif c==34: in_string=True
        elif c in (91,123):
            depth+=1
            if depth>24: raise ValueError("depth")
        elif c in (93,125): depth-=1
    def reject(_): raise ValueError("nonfinite")
    def finite(value):
        result=float(value)
        if not math.isfinite(result): raise ValueError("nonfinite")
        return result
    result=json.loads(raw.decode("utf-8"),object_pairs_hook=pairs,parse_constant=reject,parse_float=finite)
    def unicode_scalars(value):
        if isinstance(value,str): value.encode("utf-8")
        elif isinstance(value,dict):
            for k,v in value.items(): unicode_scalars(k); unicode_scalars(v)
        elif isinstance(value,list):
            for v in value: unicode_scalars(v)
    unicode_scalars(result)
    return result


class Session:
    def __init__(self, store, principal):
        self.store=store; self.principal=principal; self.initialized=False; self.ready=False

    def handle(self, request):
        ident=request.get("id") if isinstance(request,dict) and type(request.get("id")) in (str,int) else None
        def error(code,message): return {"jsonrpc":"2.0","id":ident,"error":{"code":code,"message":message}}
        if not isinstance(request,dict) or request.get("jsonrpc")!="2.0" or not isinstance(request.get("method"),str) or ("id" in request and (type(ident) not in (str,int))):
            return error(-32600,"Invalid request")
        method=request["method"]; params=request.get("params",{})
        if "id" not in request:
            if method=="notifications/initialized" and self.initialized: self.ready=True
            return None
        # Optional tools/list params may be serialized as null by an MCP client.
        # Normalize only this read-only discovery method; other methods keep
        # their existing parameter requirements.
        if method=="tools/list" and params is None: params={}
        if not isinstance(params,dict): return error(-32602,"Invalid params")
        if method=="initialize":
            if self.initialized: return error(-32600,"Already initialized")
            if not isinstance(params.get("protocolVersion"),str) or not isinstance(params.get("capabilities"),dict) or not isinstance(params.get("clientInfo"),dict): return error(-32602,"Invalid initialize params")
            self.initialized=True
            result={"protocolVersion":PROTOCOL,"capabilities":{"tools":{"listChanged":False}},"serverInfo":{"name":"context-ontology-companion","version":"0.1.0-draft.1"}}
        elif method=="ping": result={}
        elif not self.ready: return error(-32000,"Initialize first")
        elif method=="tools/list":
            if set(params)-{"cursor","_meta"}:
                return error(-32602,"Invalid tools/list params")
            if "_meta" in params and not isinstance(params["_meta"],dict):
                return error(-32602,"Invalid tools/list metadata")
            # This small fixed catalog has one complete page. An omitted,
            # null, or empty cursor requests that first page; continuation
            # tokens and non-string cursor values are unsupported.
            cursor=params.get("cursor")
            if cursor is not None and (not isinstance(cursor,str) or cursor!=""):
                return error(-32602,"Pagination unsupported")
            result={"tools":TOOLS}
        elif method=="tools/call":
            if set(params)-{"name","arguments","_meta"} or not isinstance(params.get("name"),str): return error(-32602,"Invalid tool call")
            try:
                value=dispatch(self.store,self.principal,params["name"],params.get("arguments",{})); failed=False
            except ContextError as exc:
                value={"error":exc.code}; failed=True
            except (sqlite3.Error,ValueError,TypeError,RecursionError):
                value={"error":"OPERATION_FAILED"}; failed=True
            result={"structuredContent":value,"content":[{"type":"text","text":json.dumps(value,ensure_ascii=False)}],"isError":failed}
        else: return error(-32601,"Method not found")
        return {"jsonrpc":"2.0","id":ident,"result":result}


def serve_stdio(home):
    from .review import load_local
    path,principal=load_local(home)
    store=Store(path); session=Session(store,principal)
    try:
        while True:
            raw=sys.stdin.buffer.readline(MAX_LINE+1)
            if not raw: break
            if len(raw)>MAX_LINE:
                response={"jsonrpc":"2.0","id":None,"error":{"code":-32700,"message":"Input too large"}}
                print(json.dumps(response),flush=True)
                break
            try: response=session.handle(parse(raw))
            except (ValueError,UnicodeError,RecursionError):
                response={"jsonrpc":"2.0","id":None,"error":{"code":-32700,"message":"Invalid JSON"}}
            if response is not None: print(json.dumps(response,ensure_ascii=True,allow_nan=False),flush=True)
    finally: store.close()
