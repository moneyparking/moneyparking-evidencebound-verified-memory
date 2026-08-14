# Judge Acceptance — EvidenceBound Verified Memory

## Status

Judge-critical production acceptance is **PASS**.

Public demo:

https://rshqlqgie4jsugx2unkgwywtu40vbyfw.lambda-url.us-east-1.on.aws/

Canonical source:

https://github.com/moneyparking/moneyparking-evidencebound-verified-memory

The integration code was merged to `main` as `fdae5431f3111e974e52facc0886a939a041122e`. A later documentation-only commit may advance `main`; GitHub Actions reruns the same executable acceptance on every `main` push.

## What the executable cloud gate proves

The `Cloud Acceptance` workflow performs all of the following against real services:

1. connects to the real CockroachDB Cloud database;
2. validates schema and query shapes, including Agent Skill-driven `EXPLAIN` checks;
3. writes T0 in Session A;
4. constructs a fresh Session B repository/service instance and retrieves T0 from CockroachDB;
5. verifies historical integrity;
6. computes the deterministic T1 diff;
7. re-evaluates current applicability independently of historical integrity;
8. performs Cockroach vector incident recall;
9. assumes the AWS deployment role through GitHub OIDC and short-lived STS credentials;
10. packages to S3 and deploys through CloudFormation to Lambda;
11. invokes the public Lambda Function URL;
12. performs public `Save T0` and public fresh `Reopen T1` requests;
13. invokes Amazon Bedrock Nova Micro only after trusted state is finalized;
14. asserts the expected trusted result and non-empty explanation.

## Verified receipt

Exact branch acceptance after Bedrock access was enabled:

```text
PUBLIC_HEALTH_HTTP=200
PUBLIC_SAVE_HTTP=200
PUBLIC_REOPEN_HTTP=200
AWS_PUBLIC_ACCEPTANCE=PASS integrity=VERIFIED applicability=REVIEW_REQUIRED changes=CHANGED,NEW,STALE,UNCHANGED vector_signature=deterministic bedrock_model=nova-micro explanation=present fresh_session=true
AWS_DEPLOYMENT_IDENTITY=PASS function_arn=arn:aws:lambda:us-east-1:877348951762:function:evidencebound-verified-memory
```

Post-merge `main`:

- CI workflow: PASS
- Cockroach live job: PASS
- AWS live job: PASS
- Public independent-session acceptance: PASS

## Required adversarial semantics

Executable tests cover:

- tampered historical payload → integrity failure → `FAIL_CLOSED`;
- Bedrock is not called after failed historical integrity;
- changed value/hash does not automatically become `REFUTED`;
- historical integrity can remain `VERIFIED` while current applicability is `REVIEW_REQUIRED`.

## First-time judge journey

1. Open the public demo URL.
2. Read the banner: the fixture is controlled, not claimed as live sports evidence.
3. Click **Save T0 / End Session A**.
4. Copy the displayed `memory_id` or use **Open fresh Session B**.
5. In the new tab/session, submit **Reopen T1**.
6. Confirm:
   - historical integrity = `VERIFIED`;
   - historical decision = `VERIFIED`;
   - current applicability = `REVIEW_REQUIRED`;
   - changes include `UNCHANGED`, `CHANGED`, `STALE`, `NEW`;
   - recalled incidents are present;
   - Bedrock explanation is present.

The judge does not need hidden IDs, AWS credentials, Cockroach credentials, or developer intervention.

## Source-of-truth rule

README text is descriptive. GitHub Actions and the public AWS endpoint are the executable source of truth for PASS claims.
