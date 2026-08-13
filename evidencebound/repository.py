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
        import certifi
        import psycopg
        from psycopg.conninfo import make_conninfo

        root_cert = os.getenv("PGSSLROOTCERT") or certifi.where()
        connection_url = make_conninfo(
            self.database_url,
            sslmode="verify-full",
            sslrootcert=root_cert,
        )
        return psycopg.connect(connection_url, autocommit=True)

    def save_snapshot(self, snapshot: dict[str, Any]) -> None:
        from psycopg import sql
        from psycopg.types.json import Jsonb
        query = sql.SQL("INSERT INTO {} (memory_id, session_id, created_at, policy_version, proof_version, decision_state, evidence_hash, record_hash, previous_record_hash, snapshot) VALUES (%s::UUID, %s::UUID, %s::TIMESTAMPTZ, %s, %s, %s, %s, %s, %s, %s)").format(sql.Identifier(MEMORY_TABLE))
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query, (snapshot["memory_id"], snapshot["session_id"], snapshot["created_at"], snapshot["policy_version"], snapshot["proof_version"], snapshot["decision_state"], snapshot["evidence_hash"], snapshot["record_hash"], snapshot["previous_record_hash"], Jsonb(snapshot)))

    def load_latest(self, memory_id: str) -> dict[str, Any] | None:
        from psycopg import sql
        query = sql.SQL("SELECT snapshot FROM {} WHERE memory_id = %s::UUID ORDER BY created_at DESC, id DESC LIMIT 1").format(sql.Identifier(MEMORY_TABLE))
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query, (memory_id,))
            row = cur.fetchone()
        if row is None:
            return None
        return row[0] if isinstance(row[0], dict) else json.loads(row[0])

    @staticmethod
    def _vector(values: list[float]) -> str:
        return "[" + ",".join(f"{value:.9g}" for value in values) + "]"

    def save_incident(self, *, memory_id: str, incident_type: str, text: str, embedding: list[float]) -> None:
        from psycopg import sql
        query = sql.SQL("INSERT INTO {} (memory_id, incident_type, incident_text, embedding) VALUES (%s::UUID, %s, %s, %s::VECTOR)").format(sql.Identifier(INCIDENT_TABLE))
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(query, (memory_id, incident_type, text, self._vector(embedding)))

    def recall_incidents(self, *, memory_id: str, limit: int = 3) -> list[dict[str, Any]]:
        from psycopg import sql
        latest_vector_query = sql.SQL("SELECT embedding::STRING FROM {} WHERE memory_id = %s::UUID ORDER BY created_at DESC, id DESC LIMIT 1").format(sql.Identifier(INCIDENT_TABLE))
        recall_query = sql.SQL("SELECT incident_type, incident_text, embedding <-> %s::VECTOR AS distance FROM {} WHERE memory_id = %s::UUID ORDER BY embedding <-> %s::VECTOR LIMIT %s").format(sql.Identifier(INCIDENT_TABLE))
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(latest_vector_query, (memory_id,))
            vector_row = cur.fetchone()
            if vector_row is None:
                return []
            vector = str(vector_row[0])
            cur.execute(recall_query, (vector, memory_id, vector, limit))
            rows = cur.fetchall()
        return [{"incident_type": row[0], "text": row[1], "distance": float(row[2])} for row in rows]

    def tooling_evidence(self) -> dict[str, Any]:
        from psycopg import sql
        index_query = sql.SQL("SELECT index_name FROM [SHOW INDEXES FROM {}] WHERE index_name = %s LIMIT 1").format(sql.Identifier(INCIDENT_TABLE))
        count_query = sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(MEMORY_TABLE))
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(index_query, (VECTOR_INDEX,))
            vector_index = cur.fetchone()
            cur.execute(count_query)
            memory_count = int(cur.fetchone()[0])
        return {"vector_index": vector_index[0] if vector_index else None, "verified_memory_rows": memory_count}
