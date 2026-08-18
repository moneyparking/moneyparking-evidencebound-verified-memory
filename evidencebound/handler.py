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
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EvidenceBound Verified Memory</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}body{font-family:Inter,ui-monospace,SFMono-Regular,Menlo,monospace;max-width:1180px;margin:0 auto;padding:32px 22px 64px;background:#090c10;color:#edf3f8}h1{font-size:34px;margin:0 0 8px}.tagline{font-size:18px;color:#b8c5d1;margin:0 0 18px}.note{color:#94a3b3;font-size:13px;line-height:1.55}.runtime{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0}.badge{display:inline-block;border:1px solid #3b4654;background:#121821;padding:7px 10px;border-radius:999px;font-size:12px;font-weight:700}.ok{border-color:#2d8f62;color:#75e0aa}.warn{border-color:#a66a22;color:#f2b969}.bad{border-color:#a63e49;color:#ff8894}.arch{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin:22px 0}.arch div{border:1px solid #2d3744;background:#111720;padding:12px;border-radius:8px;font-size:12px;line-height:1.35}.arch strong{display:block;margin-bottom:5px}.arch .llm{border-color:#815f2d}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:18px}.card{border:1px solid #2d3744;background:#10161e;border-radius:10px;padding:16px;min-height:150px}.card h2{font-size:14px;text-transform:uppercase;letter-spacing:.08em;color:#9fb1c3;margin:0 0 12px}.big{font-size:20px;font-weight:800;margin:8px 0}.kv{display:grid;grid-template-columns:180px 1fr;gap:7px 12px;font-size:13px;line-height:1.45}.kv span:nth-child(odd){color:#8fa1b4}.mono{word-break:break-all;color:#dce7f0}.controls{margin:22px 0 12px;padding:16px;border:1px solid #344150;background:#0f151d;border-radius:10px}button,input{font:inherit;padding:12px;margin:7px 8px 7px 0}button{background:#e7eef5;color:#0b0d10;border:0;border-radius:6px;font-weight:800;cursor:pointer}button:hover{filter:brightness(.92)}input{width:min(720px,95%);background:#0a0f15;color:#edf3f8;border:1px solid #46566a;border-radius:6px}.phase{font-size:13px;color:#b8c5d1;margin-bottom:8px}.raw{margin-top:16px}pre{white-space:pre-wrap;word-break:break-word;background:#0b1118;padding:16px;border:1px solid #26313e;border-radius:8px;min-height:120px;font-size:12px;line-height:1.5}.changes{display:flex;gap:7px;flex-wrap:wrap}.change{padding:5px 8px;border:1px solid #455264;border-radius:5px;font-size:12px}.footer{margin-top:22px;color:#8f9dad;font-size:12px}@media(max-width:820px){.arch{grid-template-columns:1fr 1fr}.grid{grid-template-columns:1fr}.kv{grid-template-columns:140px 1fr}}
</style>
</head>
<body>
<h1>EvidenceBound Verified Memory</h1>
<p class="tagline">Most agents remember answers. EvidenceBound remembers the proof.</p>
<p class="note">Controlled judge fixture. Trusted state is deterministic. Missing or invalid history fails closed. Amazon Bedrock explains only after EvidenceBound finalizes the trust decision.</p>
<div class="runtime"><span class="badge ok">PUBLIC RUNTIME · AWS LAMBDA</span><span class="badge">PERSISTENT MEMORY · COCKROACHDB CLOUD</span><span class="badge">LLM OUTSIDE TRUST BOUNDARY</span></div>
<div class="arch">
  <div><strong>1 · Evidence</strong>evidence + provenance binding</div>
  <div><strong>2 · Verify</strong>deterministic trust decision</div>
  <div><strong>3 · Persist</strong>CockroachDB verified memory</div>
  <div><strong>4 · Compare</strong>exact T0 → T1 change detection</div>
  <div><strong>5 · Re-evaluate</strong>current applicability / recovery</div>
  <div class="llm"><strong>6 · Explain</strong>Bedrock bounded explanation only</div>
</div>
<div class="controls">
  <div id="phase" class="phase">Session A ready. Save T0 to begin.</div>
  <button onclick="saveT0()">1. Save T0 / End Session A</button><br>
  <input id="memory" aria-label="Memory ID" placeholder="memory_id appears here after Save T0"><br>
  <button onclick="openFresh()">2. Open fresh Session B</button>
  <button onclick="reopen()">3. Reopen T1 from CockroachDB</button>
</div>
<div class="grid">
  <section class="card"><h2>CockroachDB memory layer</h2><div id="memoryProof"><div class="big">WAITING FOR T0</div><p class="note">The Save path must persist T0 and read it back before success is returned.</p></div></section>
  <section class="card"><h2>Trusted state</h2><div id="trustProof"><div class="big">NOT EVALUATED</div><p class="note">Historical integrity and current applicability are separate states.</p></div></section>
  <section class="card"><h2>Change / recall proof</h2><div id="changeProof"><div class="big">WAITING FOR T1</div><p class="note">T1 will show deterministic changes and CockroachDB vector recall.</p></div></section>
  <section class="card"><h2>Bounded LLM explanation</h2><div id="llmProof"><div class="big">NOT CALLED</div><p class="note">Bedrock cannot alter evidence, provenance, integrity, change classes, or applicability.</p></div></section>
</div>
<section class="raw"><h2>Raw API evidence</h2><pre id="out">Ready.</pre></section>
<p class="footer">Universal EvidenceBound flow: evidence/provenance binding → deterministic verification → persisted trusted state → exact change detection → selective re-evaluation/recovery → bounded LLM explanation.</p>
<script>
const input=document.getElementById('memory');
const out=document.getElementById('out');
const phase=document.getElementById('phase');
const supplied=new URLSearchParams(location.search).get('memory_id');
function esc(v){return String(v??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function kv(rows){return '<div class="kv">'+rows.map(([k,v])=>'<span>'+esc(k)+'</span><span class="mono">'+esc(v)+'</span>').join('')+'</div>'}
function badge(text,kind='ok'){return '<span class="badge '+kind+'">'+esc(text)+'</span>'}
function render(j,mode){
  out.textContent=JSON.stringify(j,null,2);
  const m=j.memory_layer||{};
  if(mode==='save'){
    const verified=!!m.write_confirmed&&!!m.readback_confirmed;
    document.getElementById('memoryProof').innerHTML='<div>'+badge(verified?'WRITE + READBACK VERIFIED':'MEMORY PROOF FAILED',verified?'ok':'bad')+'</div><div class="big">CockroachDB Cloud</div>'+kv([
      ['table',m.memory_table],['memory_id',j.memory_id],['record_hash',j.record_hash],['vector_index',m.vector_index],['verified rows',m.verified_memory_rows]
    ]);
    document.getElementById('trustProof').innerHTML='<div>'+badge(j.historical_decision||'UNKNOWN',j.historical_decision==='VERIFIED'?'ok':'warn')+'</div>'+kv([
      ['Session A',j.session_a_id],['session ended',j.session_a_ended],['evidence_hash',j.evidence_hash]
    ]);
    phase.textContent='Session A ended. T0 is persisted and read back from CockroachDB. Open a fresh Session B.';
  }else{
    const readOk=!!m.historical_read_confirmed&&!!m.record_hash_reverified;
    document.getElementById('memoryProof').innerHTML='<div>'+badge(readOk?'HISTORICAL READ VERIFIED':'HISTORICAL READ FAILED',readOk?'ok':'bad')+'</div><div class="big">T0 loaded from CockroachDB</div>'+kv([
      ['table',m.memory_table],['memory_id',j.memory_id],['record_hash',j.record_hash],['fresh Session B',j.fresh_session],['Session B',j.session_b_id]
    ]);
    const integrityKind=j.historical_integrity==='VERIFIED'?'ok':'bad';
    const appKind=j.current_applicability==='REVIEW_REQUIRED'?'warn':(j.current_applicability==='FAIL_CLOSED'?'bad':'ok');
    document.getElementById('trustProof').innerHTML='<div>'+badge('INTEGRITY '+(j.historical_integrity||'—'),integrityKind)+' '+badge('APPLICABILITY '+(j.current_applicability||'—'),appKind)+'</div>'+kv([
      ['historical decision',j.historical_decision],['Session A',j.session_a_id],['Session B',j.session_b_id]
    ]);
    const classes=[...new Set((j.changes||[]).map(x=>x.change))];
    document.getElementById('changeProof').innerHTML='<div class="changes">'+classes.map(x=>'<span class="change">'+esc(x)+'</span>').join('')+'</div>'+kv([
      ['vector index',m.vector_index],['recalled incidents',m.recalled_incident_count],['verified rows',m.verified_memory_rows]
    ]);
    const explanation=j.bedrock_explanation||'Not called because trusted state failed closed.';
    document.getElementById('llmProof').innerHTML='<div>'+badge(j.bedrock_explanation?'BEDROCK EXPLANATION ONLY':'BEDROCK NOT CALLED',j.bedrock_explanation?'ok':'bad')+'</div><p class="note">'+esc(explanation)+'</p>';
    phase.textContent='Fresh Session B reconstructed T0 from CockroachDB, verified history, compared T1, recalled prior incidents, then requested bounded explanation.';
  }
}
if(supplied){input.value=supplied;phase.textContent='Fresh Session B input contains only memory_id. Click Reopen T1 from CockroachDB.';document.getElementById('memoryProof').innerHTML='<div>'+badge('SESSION B · MEMORY_ID ONLY')+'</div><div class="big">Awaiting CockroachDB historical read</div>'+kv([['memory_id',supplied]]);}
async function call(path,body){const r=await fetch(path,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body||{})});let j;try{j=await r.json()}catch{j={error:'non_json_response',status:r.status}}if(!r.ok){out.textContent=JSON.stringify(j,null,2)}return j}
async function saveT0(){phase.textContent='Saving T0 to CockroachDB and verifying read-back…';const j=await call('/api/save',{});if(j.memory_id){input.value=j.memory_id;render(j,'save')}else{out.textContent=JSON.stringify(j,null,2)}}
function openFresh(){const id=input.value.trim();if(!id){out.textContent='Save T0 first.';return}window.open('/?memory_id='+encodeURIComponent(id),'_blank','noopener')}
async function reopen(){const id=input.value.trim();if(!id){out.textContent='Enter the T0 memory_id.';return}phase.textContent='Retrieving historical T0 from CockroachDB in Session B…';const j=await call('/api/reopen',{memory_id:id});render(j,'reopen')}
</script>
</body>
</html>"""


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
