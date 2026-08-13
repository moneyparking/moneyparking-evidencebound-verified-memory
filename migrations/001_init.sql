CREATE TABLE verified_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID NOT NULL,
    session_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    policy_version STRING NOT NULL,
    proof_version STRING NOT NULL,
    decision_state STRING NOT NULL CHECK (decision_state IN ('VERIFIED', 'REVIEW_REQUIRED', 'FAIL_CLOSED')),
    evidence_hash STRING NOT NULL,
    record_hash STRING NOT NULL UNIQUE,
    previous_record_hash STRING NULL,
    snapshot JSONB NOT NULL,
    INDEX verified_memories_memory_created_idx (memory_id, created_at DESC)
);
-- statement-break
CREATE TABLE verification_incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID NOT NULL,
    incident_type STRING NOT NULL,
    incident_text STRING NOT NULL,
    embedding VECTOR(1024) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    INDEX verification_incidents_memory_idx (memory_id)
);
-- statement-break
CREATE VECTOR INDEX verification_incidents_embedding_idx ON verification_incidents (embedding);
