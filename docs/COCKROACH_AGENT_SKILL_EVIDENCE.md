# CockroachDB Agent Skills usage evidence

Upstream repository: `cockroachlabs/cockroachdb-skills`

Reviewed upstream commit: `e14e86d23ce8ee2e7e40a34ce2944c2502b6eadd`

Skills referenced during implementation:

- `skills/cockroachdb-security-and-governance/hardening-user-privileges/SKILL.md`
- `skills/cockroachdb-security-and-governance/managing-tls-certificates/SKILL.md`

These references informed the runtime identity separation and the CockroachDB Cloud CA / `verify-full` connection repair used by the live acceptance workflow.

This document records implementation provenance only. The Agent Skills repository does not execute application SQL.
