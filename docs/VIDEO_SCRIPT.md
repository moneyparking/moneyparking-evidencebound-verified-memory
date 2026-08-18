# Canonical <3 Minute Verified Memory Video

Target length: **2:30–2:45**. Hard stop: **< 3:00**.

Primary acceptance target: visibly satisfy the Devpost requirement that the video shows the working project **and the CockroachDB memory layer at work**.

Secondary reuse target: the finished video may later be cited as a **prior EvidenceBound reference implementation** for AI-BOOST Challenge 4 / EvidenceBound ScenarioGraph. It must **not** claim to be a ScenarioGraph demo.

## Narrative primitives

Use this generic EvidenceBound sequence throughout the narration:

**evidence/provenance binding → deterministic verification → persisted trusted state → exact change detection → selective re-evaluation/recovery → bounded LLM explanation**

The LLM never makes or overrides the trust decision.

## 0:00–0:12 — Working public product + trust boundary

Screen: open the public Lambda Function URL. Keep the browser URL visible briefly. Show the on-page EvidenceBound architecture strip and badges:

- `PUBLIC RUNTIME · AWS LAMBDA`
- `PERSISTENT MEMORY · COCKROACHDB CLOUD`
- `LLM OUTSIDE TRUST BOUNDARY`

Voice:

> Most agents remember answers. EvidenceBound remembers the proof. It binds decisions to evidence and provenance, verifies them deterministically, persists trusted state, detects exact changes later, and only then lets an LLM explain the result.

## 0:12–0:38 — Session A → Save T0 → verified CockroachDB write/read-back

Screen: click **1. Save T0 / End Session A**.

Hold on the `CockroachDB memory layer` card until it visibly shows:

- `WRITE + READBACK VERIFIED`
- `CockroachDB Cloud`
- the generated `memory_id`
- `record_hash`
- table `evidencebound_verified_memories`
- real vector index name
- Session A ended

Voice:

> Session A verifies T0 and persists the evidence-bound snapshot to CockroachDB. Save does not report success until the just-written record can be read back through the database boundary with the same proof hash. Session A then ends.

## 0:38–0:55 — Real CockroachDB surface

Screen: briefly switch to the real CockroachDB Cloud SQL surface. Do not expose credentials, connection strings, billing, or secrets.

Query the same public `memory_id` and show one row from the verified-memory table. Safe example:

```sql
SELECT memory_id, session_id, decision_state, record_hash, created_at
FROM evidencebound_verified_memories
WHERE memory_id = '<PUBLIC_MEMORY_ID>';
```

Then show the vector index with a prepared safe query or the CockroachDB index view. Safe SQL example:

```sql
SHOW INDEXES FROM evidencebound_verification_incidents;
```

The same `memory_id` from the public app must be readable on the CockroachDB row.

Voice:

> This is the same T0 in CockroachDB Cloud, keyed by the public memory ID. Verified memory and verification-incident vector recall live in the same persistent database layer.

## 0:55–1:08 — Independent/fresh Session B

Screen: return to the public app and click **2. Open fresh Session B**. A new tab must open.

The new tab should visibly say that Session B input contains **only `memory_id`** and is awaiting a CockroachDB historical read.

Voice:

> Now Session A is gone. This fresh Session B receives only the memory ID. It must reconstruct the historical state from CockroachDB; no process-local answer is carried forward.

## 1:08–1:43 — Reopen T1 from CockroachDB

Screen: click **3. Reopen T1 from CockroachDB**.

Hold on the cards until all of the following are readable together or in a short scroll:

- `HISTORICAL READ VERIFIED`
- `fresh Session B = true`
- `historical integrity = VERIFIED`
- `historical decision = VERIFIED`
- `current applicability = REVIEW_REQUIRED`
- `UNCHANGED`
- `CHANGED`
- `STALE`
- `NEW`
- CockroachDB vector index name
- recalled incident count

Voice:

> Session B reloads T0 from CockroachDB and re-verifies its historical proof. The past decision remains VERIFIED and its integrity remains VERIFIED, while current applicability becomes REVIEW_REQUIRED. The deterministic diff contains UNCHANGED, CHANGED, STALE, and NEW. A changed hash does not automatically mean REFUTED.

## 1:43–2:02 — CockroachDB memory behavior, not a storage checkbox

Screen: keep the memory-layer and change/recall cards visible. If useful, show the real CockroachDB vector/index surface for only a few seconds.

Voice:

> CockroachDB is a behavioral dependency. Without the persisted T0, Session B fails closed. Distributed Vector Indexing recalls prior verification incidents so the agent can reuse verified context without creating a separate consistency boundary.

## 2:02–2:24 — AWS Lambda + bounded Bedrock explanation

Screen: show the `PUBLIC RUNTIME · AWS LAMBDA` badge and the `Bounded LLM explanation` card. Optionally use a very short AWS Lambda console shot showing the deployed function / Function URL, without account-sensitive information.

Voice:

> The public service runs on AWS Lambda. After EvidenceBound has finalized integrity, diff, and applicability, Amazon Bedrock generates a bounded explanation. Bedrock cannot alter evidence, provenance, hashes, classifications, or trusted state. If historical integrity fails, Bedrock is not called.

## 2:24–2:40 — Universal close

Screen: return to the EvidenceBound architecture strip / final trusted-state view.

Voice:

> EvidenceBound keeps generated decisions tied to the evidence and state that made them trustworthy — across sessions, systems and changing inputs.

Do **not** say that this video is ScenarioGraph.

# Recording acceptance checklist

- Duration is **< 3:00**.
- Video is **Public** on YouTube or Vimeo.
- Working public product is shown, not slides only.
- Session A → Save T0 is shown.
- `WRITE + READBACK VERIFIED` is readable on screen.
- Real CockroachDB Cloud surface shows the same public `memory_id` persisted in `evidencebound_verified_memories`.
- CockroachDB vector/index behavior is shown visually.
- Session A ends before Session B is opened.
- Fresh Session B visibly starts with only `memory_id`.
- Session B visibly shows `HISTORICAL READ VERIFIED` from CockroachDB.
- `historical integrity = VERIFIED` and `current applicability = REVIEW_REQUIRED` are both readable.
- `UNCHANGED`, `CHANGED`, `STALE`, and `NEW` are visible.
- AWS Lambda/public runtime is visible.
- Bedrock is presented only as bounded explanation after deterministic trust state.
- No SignalReview branding.
- No automotive/crash ScenarioGraph claim.
- No automotive safety, certification, homologation, or arbitrary compromise-detection claims.
- No secrets, private DB URLs, AWS credentials, billing data, or environment values on screen.
- CockroachDB hackathon branding is not the dominant product identity.
- One canonical video URL is used in Devpost.
- Disable Remix/Shorts remixing if YouTube offers the setting.
