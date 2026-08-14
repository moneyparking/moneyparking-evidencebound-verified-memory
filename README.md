# EvidenceBound Verified Memory — Time-Travel for AI Decisions

> **Most agents remember answers. EvidenceBound remembers the proof.**

EvidenceBound Verified Memory is a new, isolated CockroachDB × AWS hackathon integration layer. It persists a verified decision together with the evidence/provenance-bound snapshot needed to prove why that decision was reached. A later independent session reloads the historical record from CockroachDB, verifies integrity, compares current evidence deterministically, re-evaluates applicability, recalls prior verification incidents through CockroachDB vector indexing, and asks Amazon Bedrock to explain the already-trusted result.

SignalReview.co is the real pre-existing reference application. This repository is not a rebrand of SignalReview and the controlled judge fixture is explicitly not presented as live sports data.

## Judge question

**What changed since my last review, and can you prove it?**

Secondary question: **Why did we reach this conclusion previously?**

## Public demo

AWS Lambda Function URL:

**https://rshqlqgie4jsugx2unkgwywtu40vbyfw.lambda-url.us-east-1.on.aws/**

Judge path:

1. **Save T0 / End Session A** — persist a verified historical snapshot to CockroachDB.
2. **Open fresh Session B** — open a new browser tab carrying only the public `memory_id`; no Lambda process-local state is reused.
3. **Reopen T1** — retrieve T0 from CockroachDB, verify historical integrity, compute the deterministic T1 diff, re-evaluate current applicability, recall the prior verification incident through the Cockroach vector index, and request a bounded Amazon Bedrock explanation.

No credentials are required for the public controlled demo.

## Canonical result

- T0 historical decision: `VERIFIED`
- T1 historical integrity: `VERIFIED`
- T1 current applicability: `REVIEW_REQUIRED`
- deterministic changes include `UNCHANGED`, `CHANGED`, `STALE`, `NEW`
- a hash change does **not** automatically mean `REFUTED`
- tampering with the historical payload produces `FAIL_CLOSED`
- Bedrock explains the deterministic result but cannot change trusted state

Historical integrity and current applicability are deliberately separate. A historical decision can remain verified while new evidence makes it unsafe to reuse without review.

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
EvidenceBound historical integrity verification
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
  → Amazon S3 deployment artifact
  → AWS CloudFormation
  → AWS Lambda + Function URL
  → CockroachDB Cloud + Amazon Bedrock
```

No long-lived AWS access key is stored in GitHub.

## CockroachDB is a behavioral dependency

The application does not merely mention CockroachDB. Live acceptance writes T0 using one repository/service instance, ends Session A, then constructs a fresh Session B repository/service instance and reloads T0 from CockroachDB. Session B behavior depends on that persisted record.

Hackathon-owned tables/index:

- `evidencebound_verified_memories`
- `evidencebound_verification_incidents`
- `evidencebound_verification_incidents_embedding_idx`

History is append-oriented and tamper-evident at the application/proof layer. This repository does **not** describe CockroachDB as a blockchain, WORM store, or immutable database.

## Two CockroachDB tools used authentically

### 1. Distributed Vector Indexing

Verification incidents are stored as `VECTOR(1024)` with a real CockroachDB vector index. The representation is a deterministic EvidenceBound incident signature rather than an LLM-generated embedding, keeping trusted representation deterministic while making vector recall a real database behavior.

### 2. CockroachDB Agent Skills Repo

Schema/query work applies the official `cockroachdb-sql` skill from:

`cockroachlabs/cockroachdb-skills/skills/cockroachdb-query-and-schema-design/cockroachdb-sql/SKILL.md`

Pinned source blob used by executable acceptance:

`2690e972a99fe632818f0fc1a434080bc7acd917`

The connected live gate runs `EXPLAIN` for verified-memory retrieval and vector retrieval before the behavioral T0/T1 acceptance.

## AWS services used

- **Amazon Bedrock** — Amazon Nova Micro generates a bounded explanation after deterministic state is finalized.
- **AWS Lambda** — public judge service and independent request execution.
- **Amazon S3** — Lambda deployment artifact storage.
- **AWS CloudFormation** — reproducible Lambda/runtime IAM/Function URL deployment.
- **AWS STS + GitHub OIDC** — short-lived deployment identity; no stored AWS access keys.

## Trusted-state boundary

EvidenceBound owns:

- evidence canonicalization
- evidence/provenance binding
- SHA-256 evidence and record hashes
- policy/proof version binding
- historical integrity
- deterministic diff classification
- current applicability
- fail-closed behavior

Bedrock receives only the minimum deterministic classifications needed for explanation: historical integrity, historical decision, current applicability, and `{evidence_id, change}` pairs. Evidence values, proof hashes, and provenance internals are not sent to the model. Tests verify that model output cannot mutate the trusted result object.

## Fail-closed semantics

`REFUTED` is reserved for a valid contradiction under deterministic EvidenceBound rules. A changed value or changed hash is `CHANGED` unless the stricter refutation contract is satisfied.

Missing, malformed, or tampered historical memory never falls back to a plausible answer. Integrity failure returns `FAIL_CLOSED` and Bedrock is not called.

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

Cloud acceptance is executable in `.github/workflows/cockroach-live.yml`.

### Production acceptance status

**PASS on `main`.** The post-merge `main` workflows are green.

Verified public path:

```text
GitHub OIDC / AWS STS          PASS
CockroachDB live acceptance   PASS
S3 deployment artifact        PASS
CloudFormation / Lambda       PASS
GET /health                   HTTP 200
POST /api/save                HTTP 200
POST /api/reopen              HTTP 200
historical_integrity          VERIFIED
historical_decision           VERIFIED
current_applicability         REVIEW_REQUIRED
changes                       CHANGED, NEW, STALE, UNCHANGED
Cockroach vector recall       PASS
Bedrock Nova Micro            explanation present
fresh Session B               PASS
```

The executable workflow prints:

`AWS_PUBLIC_ACCEPTANCE=PASS integrity=VERIFIED applicability=REVIEW_REQUIRED changes=CHANGED,NEW,STALE,UNCHANGED vector_signature=deterministic bedrock_model=nova-micro explanation=present fresh_session=true`

For detailed receipts see [`docs/JUDGE_ACCEPTANCE.md`](docs/JUDGE_ACCEPTANCE.md).

## New vs. pre-existing disclosure

**Pre-existing:** EvidenceBound verification concepts/method, SignalReview.co, and prior verified-memory ideas.

**Built for this hackathon in this new repository (started 2026-08-13):** the isolated Verified Memory integration layer; CockroachDB schema and append-oriented persistence; vector incident recall and live Agent Skill `EXPLAIN` gates; independent Session A/Session B flow; deterministic time-travel diff/applicability contract; GitHub OIDC AWS deployment; Lambda public judge surface; and bounded Bedrock explanation integration.

## Submission package

- [`docs/JUDGE_ACCEPTANCE.md`](docs/JUDGE_ACCEPTANCE.md) — executable acceptance receipts and judge journey
- [`docs/DEVPOST_SUBMISSION.md`](docs/DEVPOST_SUBMISSION.md) — prepared Devpost answers
- [`docs/VIDEO_SCRIPT.md`](docs/VIDEO_SCRIPT.md) — <3 minute demo script and shot list

## License

MIT. See [`LICENSE`](LICENSE).
