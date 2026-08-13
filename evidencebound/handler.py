from __future__ import annotations

import hashlib
import json
from typing import Any

from .bedrock import BedrockClient
from .repository import CockroachRepository
from .service import EvidenceBoundService


def _service() -> EvidenceBoundService:
    return EvidenceBoundService(CockroachRepository(), BedrockClient())


def _response(status: int, body: Any, content_type: str = "application/json") -> dict[str, Any]:
    payload = body if isinstance(body, str) else json.dumps(body, sort_keys=True)
    return {"statusCode": status, "headers": {"content-type": content_type, "cache-control": "no-store", "x-content-type-options": "nosniff", "content-security-policy": "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; form-action 'self'; base-uri 'none'"}, "body": payload}


def _page() -> str:
    return """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EvidenceBound Verified Memory</title><style>body{font-family:ui-monospace,monospace;max-width:980px;margin:40px auto;padding:0 18px;background:#0b0d10;color:#e7ecf2}button{padding:12px 18px;margin:8px 8px 8px 0;background:#e7ecf2;color:#0b0d10;border:0;font-weight:700;cursor:pointer}pre{white-space:pre-wrap;background:#141820;padding:16px;border:1px solid #2b3340;min-height:140px}small{color:#99a4b3}</style></head><body><h1>EvidenceBound Verified Memory</h1><p>Most agents remember answers. EvidenceBound remembers the proof.</p><p><small>Controlled judge fixture. No live sports fact is claimed. Trusted state is deterministic; Bedrock explains only.</small></p><button onclick="saveT0()">1. Save T0 / End Session A</button><button onclick="reopen()">2. Fresh Session B / Reopen T1</button><pre id="out">Ready.</pre><script>let memoryId=null;async function call(path,body){const r=await fetch(path,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body||{})});const j=await r.json();document.getElementById('out').textContent=JSON.stringify(j,null,2);return j}async function saveT0(){const j=await call('/api/save',{});memoryId=j.memory_id}async function reopen(){if(!memoryId){document.getElementById('out').textContent='Save T0 first.';return}await call('/api/reopen',{memory_id:memoryId})}</script></body></html>"""


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
            memory_id = payload.get("memory_id")
            if not isinstance(memory_id, str) or len(memory_id) > 64:
                return _response(400, {"error": "valid memory_id required"})
            return _response(200, _service().reopen_t1(memory_id))
        return _response(404, {"error": "not_found"})
    except Exception as exc:
        fingerprint = hashlib.sha256(type(exc).__name__.encode()).hexdigest()[:12]
        return _response(500, {"error": "fail_closed", "fingerprint": fingerprint})
