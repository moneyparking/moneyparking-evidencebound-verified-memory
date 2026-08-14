# <3 Minute Judge Video Script

Target length: **2:25–2:45**.

## 0:00–0:12 — Cold open

Screen: public EvidenceBound demo landing page.

Voice:

> Most agents remember answers. EvidenceBound remembers the proof. The question is not only what the agent decided — it is what changed since the last review, and can we prove why the earlier decision existed?

## 0:12–0:32 — Architecture in one sentence

Screen: README architecture diagram.

Voice:

> Session A verifies a decision and saves the evidence-bound snapshot to CockroachDB. Session A ends. A fresh Session B reloads that historical memory from CockroachDB, verifies integrity, compares T1 evidence deterministically, re-evaluates applicability, recalls prior verification incidents through Cockroach vector indexing, and only then asks Amazon Bedrock to explain the trusted result.

## 0:32–0:58 — Save T0

Screen: return to public demo and click **Save T0 / End Session A**.

Point to returned fields.

Voice:

> This is a controlled judge fixture, explicitly not live sports data. T0 is VERIFIED. The response gives us a public memory ID and confirms Session A has ended. The record is now persisted in CockroachDB — there is no process-local memory to rely on.

## 0:58–1:20 — Fresh independent Session B

Screen: click **Open fresh Session B** so a new tab appears with only the memory ID.

Voice:

> This new tab carries only the memory ID. Session B must retrieve the historical decision from CockroachDB. That database dependency is enforced in the live acceptance workflow with a fresh repository and service instance.

## 1:20–1:55 — Reopen and answer the judge question

Screen: click **Reopen T1** and zoom to trusted fields.

Voice:

> Historical integrity is still VERIFIED. But current applicability is REVIEW_REQUIRED. The deterministic diff contains UNCHANGED, CHANGED, STALE, and NEW evidence. A changed hash does not automatically become REFUTED. That distinction prevents an agent from rewriting history just because the world changed.

## 1:55–2:15 — CockroachDB tools

Screen: show README sections for vector index and Agent Skills, then GitHub Actions acceptance log if practical.

Voice:

> CockroachDB is the behavioral memory layer. We use Distributed Vector Indexing for verification-incident recall, and the official CockroachDB SQL Agent Skill with live connected EXPLAIN gates for both memory and vector retrieval. The public flow is backed by real CockroachDB Cloud, not a mock.

## 2:15–2:35 — AWS and Bedrock boundary

Screen: highlight Bedrock explanation on the T1 response, then Actions green run.

Voice:

> The service runs on AWS Lambda, deployed from GitHub OIDC through S3 and CloudFormation. Amazon Nova Micro explains the deterministic result, but it cannot change evidence, provenance, integrity, diff classifications, or applicability. If historical memory is tampered with, EvidenceBound fails closed and Bedrock is not called.

## 2:35–2:45 — Close

Screen: landing page/tagline.

Voice:

> Most agents remember answers. EvidenceBound remembers the proof — and proves what changed.

## Recording checklist

- 1920×1080 or 2560×1440.
- Browser zoom 110–125% so trusted fields are readable.
- Keep the public URL visible once near the beginning.
- Show the new-tab Session B transition clearly.
- Show `VERIFIED` and `REVIEW_REQUIRED` at the same time.
- Show all four change classes.
- Show the Bedrock explanation but do not linger on generated prose.
- Briefly show green GitHub Actions as production evidence.
- Do not show AWS/Cockroach secrets, environment values, billing pages, or credentials.
- Upload public/unlisted-as-required-by-rules to YouTube or Vimeo; Devpost requires a public video URL.
