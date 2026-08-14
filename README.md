# EvidenceBound Verified Memory — Time-Travel for AI Decisions

> **Most agents remember answers. EvidenceBound remembers the proof.**

EvidenceBound Verified Memory is a new, isolated CockroachDB × AWS hackathon integration layer. It stores a verified decision together with the evidence/provenance-bound snapshot needed to prove why that decision was reached, then lets a fresh session re-open the historical record, verify it, compare new evidence deterministically, and ask Amazon Bedrock to explain the already-trusted result.

SignalReview.co is the real pre-existing reference application. This repository is not a rebrand of SignalReview and does not claim that the controlled judge fixture is live sports data.

## Judge question

**What changed since my last review, and can you prove it?**

Secondary question: **Why did we reach this conclusion previously?**

## Public judge surface

AWS Lambda Function URL:

`https://rshqlqgie4jsugx2unkgwywtu40vbyfw.lambda-url.us-east-1.on.aws/`

The page exposes a three-step path:

1. **Save T0 / End Session A** — persist a verified historical snapshot to CockroachDB.
2. **Open fresh Session B** — open a new browser tab carrying only the public `memory_id`; no Lambda process-local state is carried over.
3. **Reopen T1** — retrieve T0 from CockroachDB, verify historical integrity, calculate the deterministic T1 diff, re-evaluate current applicability, recall the prior verification incident through the Cockroach vector index, and request a bounded Bedrock explanation.

The fixture is deliberately controlled and clearly labeled. It demonstrates the trust and persistence contract without pretending that static fixture values are current sports facts.

## Canonical expected result

- T0 historical decision: `VERIFIED`
- historical integrity at T1: `VERIFIED`
- current applicability at T1: `REVIEW_REQUIRED`
- deterministic T1 changes include: `UNCHANGED`, `CHANGED`, `STALE`, `NEW`
- changing a hash does **not** automatically produce `REFUTED`
- tampering with the historical payload produces `FAIL_CLOSED`
- Bedrock may explain the deterministic result but may not change trusted state

Historical integrity and current applicability are intentionally separate. A historical decision can remain cryptographically verified while new evidence makes that decision inappropriate to reuse without review.

## Architecture

```text
Session A
  controlled evidence
      ↓
EvidenceBound canonicalization + verification
      ↓
verified snapshot + record/evidence hashes
      ↓
CockroachDB append-oriented verified memory
      ↓
Session A ends

fresh Session B
  memory_id only
      ↓
CockroachDB T0 retrieval
      ↓
EvidenceBound integrity verification
      ↓
current controlled evidence
      ↓
deterministic diff
      ↓
current applicability
      ↓
CockroachDB vector incident recall
      ↓
Amazon Bedrock bounded explanation
```

AWS deployment path:

```text
GitHub Actions OIDC
  → short-lived AWS STS session
  → S3 deployment artifact
  → CloudFormation
  → Lambda + Lambda Function URL
  → CockroachDB Cloud + Amazon Bedrock
```

No long-lived AWS access key is stored in GitHub.

## CockroachDB is a behavioral dependency

The application does not merely mention CockroachDB. Live acceptance writes T0 using one repository/service instance, discards Session A, then constructs a fresh Session B repository/service instance and reloads T0 from CockroachDB. Session B behavior depends on that persisted record.

The hackathon layer uses unique tables so it does not overwrite older partial experiments:

- `evidencebound_verified_memories`
- `evidencebound_verification_incidents`
- vector index `evidencebound_verification_incidents_embedding_idx`

History is append-oriented and tamper-evident at the application/proof layer. This repository does **not** describe CockroachDB as a blockchain, WORM store, or immutable database.

## Two CockroachDB tools used authentically

### 1. Distributed Vector Indexing

Verification incidents are stored in CockroachDB as `VECTOR(1024)` with a real vector index. The representation is a deterministic EvidenceBound incident signature, not an LLM-generated semantic embedding. This keeps trusted memory representation deterministic while making vector retrieval a real database behavior.

### 2. CockroachDB Agent Skills Repo

Schema/query work applies the official `cockroachdb-sql` skill from:

`cockroachlabs/cockroachdb-skills/skills/cockroachdb-query-and-schema-design/cockroachdb-sql/SKILL.md`

Pinned source blob used by the executable acceptance gate:

`2690e972a99fe632818f0fc1a434080bc7acd917`

The live gate follows the skill's connected-database requirement by running `EXPLAIN` for both the verified-memory retrieval query and vector retrieval query before the behavioral T0/T1 acceptance.

## Trusted-state boundary

EvidenceBound owns:

- evidence canonicalization
- provenance/evidence binding
- SHA-256 evidence and record hashes
- policy/proof version binding
- historical integrity
- deterministic diff classification
- current applicability
- fail-closed behavior

Amazon Bedrock receives only the minimum deterministic classifications needed for an explanation: historical integrity, historical decision, current applicability, and `{evidence_id, change}` pairs. Evidence values, proof hashes, and provenance internals are not sent to the model. A unit gate verifies that the model call cannot mutate the trusted result object.

## Fail-closed semantics

`REFUTED` is reserved for a valid contradiction under the deterministic EvidenceBound rules. A changed value or changed hash is `CHANGED` unless the stricter refutation contract is satisfied.

Missing or malformed historical memory never falls back to a plausible answer. Integrity failure returns `FAIL_CLOSED` and Bedrock is not called.

## Verification

Local quality gates:

```bash
python -m pip install -e '.[dev]'
ruff check . --select E9,F,B,SIM
mypy evidencebound --ignore-missing-imports --allow-untyped-defs
bandit -q -r evidencebound
pytest -q
python -m compileall -q evidencebound tests scripts
```

Cloud acceptance is executable in `.github/workflows/cockroach-live.yml`. It proves the live CockroachDB dependency, OIDC identity, deployment, public health, public T0 save, and public T1 reopen. A green workflow — not this README — is the source of truth for cloud PASS claims.

## Current cloud acceptance status

As of 2026-08-13, the real AWS deployment and public endpoint are live. Public `/health` and `Save T0` pass, including Lambda → CockroachDB persistence. The final `Reopen T1` is intentionally failing closed because this brand-new AWS account currently receives an Amazon Bedrock new-account token-quota throttle for active Amazon Nova text models. The repository does not claim full AWS/Bedrock judge acceptance until the exact-head public `Reopen T1` workflow is green.

## New vs. pre-existing disclosure

**Pre-existing:** EvidenceBound verification concepts/method, SignalReview.co, and prior verified-memory ideas.

**Built for this hackathon in this new repository:** the isolated Verified Memory integration layer; CockroachDB schema, append-oriented persistence, vector incident recall and live Agent Skill `EXPLAIN` gates; independent Session A/Session B flow; deterministic time-travel diff/applicability contract; GitHub OIDC AWS deployment; Lambda public judge surface; and bounded Bedrock explanation integration.

## License

MIT. See `LICENSE`.
