# EvidenceBound Verified Memory — Time-Travel for AI Decisions

**Most agents remember answers. EvidenceBound remembers the proof.**

A new hackathon integration layer that preserves the proof behind a decision, then reopens it in a fresh session to prove what changed.

## Judge journey

```text
Session A / T0 -> deterministic verification -> canonical evidence snapshot -> SHA-256 binding -> CockroachDB save -> process ends
fresh Session B / T1 -> CockroachDB retrieve -> historical integrity -> fresh evidence -> deterministic diff -> applicability -> bounded Bedrock explanation
```

Primary question: **What changed since my last review — and can you prove it?**

Historical integrity and current applicability are separate. A T0 decision may remain `VERIFIED` while T1 becomes `REVIEW_REQUIRED`.

Diff states: `UNCHANGED`, `NEW`, `CHANGED`, `STALE`, `MISSING`, `REFUTED`. Hash change alone is `CHANGED`, never automatically `REFUTED`.

## CockroachDB behavioral dependency

Session A writes T0 and exits. Session B receives only a memory ID and reconstructs T0 from CockroachDB. No local file/process state bridges the sessions.

Verification incidents use a domain-bound `VECTOR(8)` signature and a real distributed vector index for similarity recall.

## Tests

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest
```

## Live CockroachDB acceptance

```bash
python -m pip install -e .
python scripts/live_acceptance.py
```

The script launches Session A and Session B as independent processes, requires historical `VERIFIED` plus current `REVIEW_REQUIRED`, requires `UNCHANGED + CHANGED + STALE + NEW`, and confirms real vector-index-backed incident recall.

## CockroachDB hackathon tools

1. **Distributed Vector Indexing** — `VECTOR(8)` + `CREATE VECTOR INDEX` over verification incidents, queried during live acceptance.
2. **Agent Skills Repo** — official CockroachDB skill guidance applied to schema, least privilege, migration safety, indexing and acceptance design; see `docs/COCKROACH_AGENT_SKILL_EVIDENCE.md`.

No tool is claimed working until its evidence passes on the submitted commit.

## AWS

Amazon Bedrock is the bounded explanation layer. `bedrock.py` receives deterministic trusted output and cannot mutate trusted state. Real invocation remains a release gate until verified.

## New vs pre-existing disclosure

SignalReview.co and broader EvidenceBound concepts pre-date this hackathon. This repository is a **new isolated integration layer** built during the CockroachDB × AWS hackathon and does not claim pre-existing work as new.

## Security

Secrets stay in runtime stores. CockroachDB uses a dedicated runtime SQL user. Missing/invalid historical evidence fails closed. History is tamper-evident and append-oriented, not described as blockchain, WORM or immutable.

## License

Apache-2.0. See `LICENSE`.
