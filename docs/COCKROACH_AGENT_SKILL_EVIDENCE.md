# CockroachDB Agent Skills usage evidence

This integration was designed using the official `cockroachlabs/cockroachdb-skills` Agent Skills repository as an operational guardrail, not as copied documentation.

Applied principles:
- explicit schema migrations;
- least-privilege runtime identity separated from administrative access;
- indexes tied to actual lookup paths;
- append-oriented verification history;
- live acceptance inspects the real schema and vector index;
- failures remain visible and fail closed.

Official sources: Cockroach Labs Agent Skills documentation and `cockroachlabs/cockroachdb-skills`.

This is evidence of skill-guided implementation, not a claim that the Skills repository executed SQL itself.
