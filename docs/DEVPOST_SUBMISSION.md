# Devpost Submission Draft

Hackathon: **CockroachDB × AWS Hackathon — Build with Agentic Memory**

Project: **EvidenceBound Verified Memory — Time-Travel for AI Decisions**

Tagline: **Most agents remember answers. EvidenceBound remembers the proof.**

Project start date: **08-13-26** (public repository initial commit: 2026-08-13).

## Project description

AI agents increasingly persist conclusions, summaries, and conversation history. That creates a harder question later: when an agent reuses an old decision, can it prove why that decision was valid at the time — and can it distinguish historical integrity from whether the decision is still applicable now?

EvidenceBound Verified Memory is a time-travel layer for AI decisions. Session A verifies a decision, binds it to a canonical evidence/provenance snapshot, and persists that verified memory to CockroachDB. Session A then ends. A genuinely independent Session B later retrieves the historical record from CockroachDB, verifies its integrity, compares current evidence deterministically, classifies what changed, re-evaluates current applicability, recalls related verification incidents through CockroachDB vector indexing, and asks Amazon Bedrock to explain the already-trusted result.

The canonical demo intentionally produces a result that is easy to reason about:

- historical decision = VERIFIED;
- historical integrity = VERIFIED;
- current applicability = REVIEW_REQUIRED;
- T1 contains UNCHANGED, CHANGED, STALE, and NEW evidence.

That separation is the key idea: a past decision can remain valid as a historical record while becoming unsafe to reuse today.

EvidenceBound owns canonicalization, SHA-256 evidence/record hashes, provenance binding, policy/proof version binding, deterministic comparison, trusted states, and fail-closed behavior. Amazon Bedrock is explanation-only. The model cannot fabricate evidence, alter provenance, change classifications, or override the deterministic decision state.

The public demo is deployed on AWS Lambda and requires no judge credentials. Save T0 ends Session A. Opening Session B transfers only the public memory ID; the decision is reloaded from CockroachDB rather than process-local state. The workflow then proves Cockroach vector recall and a real Amazon Nova Micro explanation.

The controlled fixture is explicitly labeled and is not presented as current sports data. SignalReview.co is the real pre-existing reference application; this repository is a new isolated hackathon integration layer rather than a rebrand.

## Functional demo URL

https://rshqlqgie4jsugx2unkgwywtu40vbyfw.lambda-url.us-east-1.on.aws/

## Testing instructions

No credentials are required.

1. Open the demo.
2. Click **Save T0 / End Session A**.
3. Open the fresh Session B link/tab carrying only the returned public `memory_id`.
4. Click **Reopen T1**.
5. Confirm `historical_integrity=VERIFIED`, `historical_decision=VERIFIED`, `current_applicability=REVIEW_REQUIRED`, the four expected change classes, recalled incidents, and a non-empty Bedrock explanation.

## Public repository URL

https://github.com/moneyparking/moneyparking-evidencebound-verified-memory

## License URL

https://github.com/moneyparking/moneyparking-evidencebound-verified-memory/blob/main/LICENSE

## CockroachDB tools

Select:

- **Distributed Vector Indexing**
- **Agent Skills Repo**

### Meaningful CockroachDB integration

CockroachDB is the behavioral memory dependency, not a checkbox. Session A persists T0; a fresh Session B reconstructs the service and reloads T0 from CockroachDB. Verification incidents are stored as `VECTOR(1024)` values with a real vector index and are recalled during T1. The official `cockroachdb-sql` Agent Skill is pinned and applied to schema/query design, and the live acceptance gate runs connected-database `EXPLAIN` checks for both memory retrieval and vector retrieval before executing the Session A/B path.

## AWS services

Select:

- **Amazon Bedrock**
- **AWS Lambda**
- **Amazon S3**
- **Other AWS service** — AWS CloudFormation / STS via GitHub OIDC

### Meaningful AWS integration

GitHub Actions obtains short-lived AWS credentials through OIDC and STS. The Lambda package is stored in S3 and deployed through CloudFormation. Lambda exposes the public judge service. During fresh T1 reopen, Lambda retrieves verified memory from CockroachDB, finalizes the deterministic integrity/diff/applicability state, and then invokes Amazon Bedrock Nova Micro for a bounded explanation. Bedrock receives only trusted classifications and cannot mutate trusted state.

## Pre-existing work disclosure

Pre-existing work includes the EvidenceBound verification concepts/method, SignalReview.co, and earlier verified-memory ideas. The submitted implementation is new work built during the hackathon submission period in the new public repository created on 2026-08-13. New hackathon work includes the isolated CockroachDB/AWS Verified Memory layer, schema and persistence contracts, vector incident recall, Agent Skill query gates, independent Session A/B flow, deterministic time-travel diff/applicability logic, AWS OIDC deployment, Lambda public judge surface, and bounded Bedrock explanation integration.

## Optional CockroachDB feedback

The Agent Skills repo was most useful when treated as an executable engineering constraint rather than documentation: pinning the exact skill source and requiring connected-database `EXPLAIN` validation made the integration more auditable. Distributed vector indexing was also valuable because verification incidents could stay transactionally colocated with the operational memory rather than being copied into a separate vector system.

## Submitter fields requiring owner attestation at submission time

Do not auto-attest these without explicit owner confirmation:

- Submitter type: expected **Individual**
- Country: expected **Ukraine**
- Not employee of sponsors: confirmation required
- Eligible jurisdiction: confirmation required
- Age of majority: confirmation required
- AI tools leveraged: OpenAI ChatGPT used as an AI coding assistant for implementation, debugging, CI repair, and documentation
- Learning derived: suggested **Significant**
- Career AI value: suggested **Yes**

## Required remaining media

Devpost requires a **public YouTube or Vimeo video under 3 minutes** showing the project and CockroachDB memory layer at work. See `docs/VIDEO_SCRIPT.md`.
