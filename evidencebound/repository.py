from __future__ import annotations

import json
import os
from typing import Any

MEMORY_TABLE = "evidencebound_verified_memories"
INCIDENT_TABLE = "evidencebound_verification_incidents"
VECTOR_INDEX = "evidencebound_verification_incidents_embedding_idx"


class CockroachRepository:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or os.environ["COCKROACH_DATABASE_URL"]

    def _connect(self):
        import psycopg
        return psycopg.connect(self.database_url, autocommit=True)

    def save_snapshot(self, snapshot: dict[str, Any]) -> None:
        from psycopg.types.json import Jsonb
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {MEMORY_TABLE} (memory_id, session_id, created_at, policy_version, proof_version, decision_state, evidence_hash, record_hash, previous_record_hash, snapshot) VALUES (%s::UUID, %s::UUID, %s::TIMESTAMPTZ, %s, %s, %s, %s, %s, %s, %s)",
                (
                    snapshot["memory_id"],
                    snapshot["session_id"],
                    snapshot["created_at"],
                    snapshot["policy_version"],
                    snapshot["proof_version"],
                    snapshot["decision_state"],
                    snapshot["evidence_hash"],
                    snapshot["record_hash"],
                    snapshot["previous_record_hash"],
                    Jsonb(snapshot),
                ),
            )

    def load_latest(self, memory_id: str) -> dict[str, Any] | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT snapshot FROM {MEMORY_TABLE} WHERE memory_id = %s::UUID ORDER BY created_at DESC, id DESC LIMIT 1",
                (memory_id,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return row[0] if isinstance(row[0], dict) else json.loads(row[0])

    @staticmethod
    def _vector(values: list[float]) -> str:
        return "[" + ",".join(f"{value:.9g}" for value in values) + "]"

    def save_incident(self, *, memory_id: str, incident_type: str, text: str, embedding: list[float]) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {INCIDENT_TABLE} (memory_id, incident_type, incident_text, embedding) VALUES (%s::UUID, %s, %s, %s::VECTOR)",
                (memory_id, incident_type, text, self._vector(embedding)),
            )

    def recall_incidents(self, *, memory_id: str, embedding: list[float], limit: int = 3) -> list[dict[str, Any]]:
        vector = self._vector(embedding)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT incident_type, incident_text, embedding <-> %s::VECTOR AS distance FROM {INCIDENT_TABLE} WHERE memory_id = %s::UUID ORDER BY embedding <-> %s::VECTOR LIMIT %s",
                (vector, memory_id, vector, limit),
            )
            rows = cur.fetchall()
        return [{"incident_type": row[0], "text": row[1], "distance": float(row[2])} for row in rows]

    def tooling_evidence(self) -> dict[str, Any]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT index_name FROM [SHOW INDEXES FROM {INCIDENT_TABLE}] WHERE index_name = %s LIMIT 1",
                (VECTOR_INDEX,),
            )
            vector_index = cur.fetchone()
            cur.execute(f"SELECT count(*) FROM {MEMORY_TABLE}")
            memory_count = int(cur.fetchone()[0])
        return {"vector_index": vector_index[0] if vector_index else None, "verified_memory_rows": memory_count}
