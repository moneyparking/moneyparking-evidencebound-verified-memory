from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import UUID

from .bedrock import BedrockClient
from .repository import CockroachRepository
from .service import EvidenceBoundService


def _service() -> EvidenceBoundService:
    return EvidenceBoundService(CockroachRepository(), BedrockClient())


def _response(status: int, body: Any, content_type: str = "application/json") -> dict[str, Any]:
    payload = body if isinstance(body, str) else json.dumps(body, sort_keys=True)
    return {
        "statusCode": status,
        "headers": {
            "content-type": content_type,
            "cache-control": "no-store",
            "x-content-type-options": "nosniff",
            "content-security-policy": (
                "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
                "connect-src 'self'; form-action 'self'; base-uri 'none'"
            ),
        },
        "body": payload,
    }


def _page() -> str:
    return """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EvidenceBound Verified Memory</title><style>body{font-family:ui-monospace,monospace;max-width:980px;margin:40px auto;padding:0 18px;background:#0b0d10;color:#e7ecf2}button,input{font:inherit;padding:12px;margin:8px 8px 8px 0}button{background:#e7ecf2;color:#0b0d10;border:0;font-weight:700;cursor:pointer}input{width:min(620px,90%);background:#141820;color:#e7ecf2;border:1px solid #465266}pre{white-space:pre-wrap;background:#141820;padding:16px;border:1px solid #2b3340;min-height:180px}small{color:#99a4b3}.steps{line-height:1.6}</style></head><body><h1>EvidenceBound Verified Memory</h1><p>Most agents remember answers. EvidenceBound remembers the proof.</p><p><small>Controlled judge fixture. No live sports fact is claimed. Trusted state is deterministic; Bedrock explains only.</small></p><div class="steps"><strong>Judge path</strong><br>1. Save T0 and end Session A.<br>2. Open a fresh Session B in a new tab. The public memory ID is carried in the URL; no process-local state is carried over.<br>3. Reopen T1. The Lambda must retrieve T0 from CockroachDB, verify historical integrity, compare T1, re-evaluate applicability, recall the prior incident through the Cockroach vector index, then ask Bedrock to explain the already-trusted result.</div><button onclick="saveT0()">1. Save T0 / End Session A</button><br><input id="memory" aria-label="Memory ID" placeholder="memory_id appears here after Save T0"><br><button onclick="openFresh()">2. Open fresh Session B</button><button onclick="reopen()">3. Reopen T1</button><pre id="out">Ready.</pre><script>const input=document.getElementById('memory');const supplied=new URLSearchParams(location.search).get('memory_id');if(supplied)input.value=supplied;async function call(path,body){const r=await fetch(path,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body||{})});let j;try{j=await r.json()}catch{j={error:'non_json_response',status:r.status}}document.getElementById('out').textContent=JSON.stringify(j,null,2);return j}async function saveT0(){const j=await call('/api/save',{});if(j.memory_id)input.value=j.memory_id}function openFresh(){const id=input.value.trim();if(!id){document.getElementById('out').textContent='Save T0 first.';return}window.open('/?memory_id='+encodeURIComponent(id),'_blank','noopener')}async function reopen(){const id=input.value.trim();if(!id){document.getElementById('out').textContent='Enter the T0 memory_id.';return}await call('/api/reopen',{memory_id:id})}</script></body></html>"""


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    request = event.get("requestContext", {}).get("http", {})
    method, path = request.get("method", "GET"), event.get("rawPath", "/")
    try:
        if method == "GET" and path == "/":
            return _response(200, _page(), "text/html; charset=utf-8")
        if method == "GET" and path == "/health":
            return _response(200, {"status": "ok", "service": "evidencebound-verified-memory"})
        if method == "POST" and path == "/api/save":
            return _response(200, _service().save_t0())
        if method == "POST" and path == "/api/reopen":
            payload = json.loads(event.get("body") or "{}")
            raw_memory_id = payload.get("memory_id")
            try:
                memory_id = str(UUID(raw_memory_id))
            except (AttributeError, TypeError, ValueError):
                return _response(400, {"error": "valid memory_id required"})
            return _response(200, _service().reopen_t1(memory_id))
        return _response(404, {"error": "not_found"})
    except Exception as exc:
        fingerprint = hashlib.sha256(type(exc).__name__.encode()).hexdigest()[:12]
        return _response(500, {"error": "fail_closed", "fingerprint": fingerprint})
