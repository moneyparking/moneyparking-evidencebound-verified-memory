CREATE TABLE IF NOT EXISTS verified_memories (
  id UUID PRIMARY KEY,
  source_ref STRING NOT NULL,
  decision_status STRING NOT NULL CHECK (decision_status IN ('VERIFIED','BLOCKED')),
  decision_reason STRING NOT NULL,
  policy_version STRING NOT NULL,
  model_version STRING NOT NULL,
  canonicalization_version STRING NOT NULL,
  snapshot_payload JSONB NOT NULL,
  integrity_hash STRING(64) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS decision_snapshots (
  id UUID PRIMARY KEY,
  memory_id UUID NOT NULL REFERENCES verified_memories(id),
  snapshot_payload JSONB NOT NULL,
  integrity_hash STRING(64) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  INDEX decision_snapshots_memory_idx (memory_id, created_at)
);

CREATE TABLE IF NOT EXISTS evidence_items (
  id UUID PRIMARY KEY,
  memory_id UUID NOT NULL REFERENCES verified_memories(id),
  snapshot_id UUID NOT NULL REFERENCES decision_snapshots(id),
  ordinal INT NOT NULL,
  evidence_key STRING(160) NOT NULL,
  item_payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (snapshot_id, evidence_key),
  INDEX evidence_items_memory_idx (memory_id, evidence_key)
);

CREATE TABLE IF NOT EXISTS verification_events (
  id UUID PRIMARY KEY,
  memory_id UUID NOT NULL REFERENCES verified_memories(id),
  event_type STRING(64) NOT NULL,
  trusted_state STRING(64) NOT NULL,
  details JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  INDEX verification_events_memory_idx (memory_id, created_at)
);

CREATE TABLE IF NOT EXISTS verification_incidents (
  id UUID PRIMARY KEY,
  memory_id UUID NOT NULL REFERENCES verified_memories(id),
  kind STRING(64) NOT NULL,
  summary STRING NOT NULL,
  tags JSONB NOT NULL,
  signature VECTOR(8) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  INDEX verification_incidents_memory_idx (memory_id, created_at)
);

CREATE VECTOR INDEX IF NOT EXISTS verification_incidents_signature_idx
ON verification_incidents (signature);
