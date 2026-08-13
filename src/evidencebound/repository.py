from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

import psycopg

from .canonical import CANONICALIZATION_VERSION
from .incidents import incident_signature
from .integrity import compute_snapshot_hash
from .models import EvidenceItem, Snapshot


def _connection_string() -> str:
    value = os.environ.get("COCKROACH_DATABASE_URL")
    if not value:
        raise RuntimeError("COCKROACH_DATABASE_URL is required")
    return value


def connect() -> psycopg.Connection[Any]:
    return psycopg.connect(_connection_string(), application_name="evidencebound-verified-memory")


def apply_migrations(conn: psycopg.Connection[Any], migration_dir: str | Path = "migrations") -> None:
    for path in sorted(Path(migration_dir).glob("*.sql")):
        with conn.cursor() as cur:
            cur.execute(path.read_text(encoding="utf-8"))
        conn.commit()


def save_snapshot(snapshot: Snapshot) -> str:
    memory_id = str(uuid.uuid4())
    snapshot_id = str(uuid.uuid4())
    integrity_hash = compute_snapshot_hash(snapshot)
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO verified_memories
            (id, source_ref, decision_status, decision_reason, policy_version, model_version,
             canonicalization_version, snapshot_payload, integrity_hash)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s::JSONB,%s)""",
            (memory_id, snapshot.source_ref, snapshot.decision_status, snapshot.decision_reason,
             snapshot.policy_version, snapshot.model_version, CANONICALIZATION_VERSION,
             json.dumps(snapshot.canonical_dict(), ensure_ascii=False), integrity_hash),
        )
        cur.execute(
            "INSERT INTO decision_snapshots (id, memory_id, snapshot_payload, integrity_hash) VALUES (%s,%s,%s::JSONB,%s)",
            (snapshot_id, memory_id, json.dumps(snapshot.canonical_dict(), ensure_ascii=False), integrity_hash),
        )
        for ordinal, item in enumerate(sorted(snapshot.evidence, key=lambda x: x.evidence_key)):
            cur.execute(
                "INSERT INTO evidence_items (id, memory_id, snapshot_id, ordinal, evidence_key, item_payload) VALUES (%s,%s,%s,%s,%s,%s::JSONB)",
                (str(uuid.uuid4()), memory_id, snapshot_id, ordinal, item.evidence_key,
                 json.dumps(item.canonical_dict(), ensure_ascii=False)),
            )
        cur.execute(
            "INSERT INTO verification_events (id, memory_id, event_type, trusted_state, details) VALUES (%s,%s,'T0_SAVED','VERIFIED',%s::JSONB)",
            (str(uuid.uuid4()), memory_id, json.dumps({"integrity_hash": integrity_hash})),
        )
        conn.commit()
    return memory_id


def _item_from_payload(payload: dict[str, Any]) -> EvidenceItem:
    return EvidenceItem(**payload)


def load_snapshot(memory_id: str) -> tuple[Snapshot, str]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT snapshot_payload, integrity_hash FROM verified_memories WHERE id = %s", (memory_id,))
        row = cur.fetchone()
    if row is None:
        raise KeyError(f"memory not found: {memory_id}")
    payload = json.loads(row[0]) if isinstance(row[0], str) else row[0]
    snapshot = Snapshot(
        decision_status=payload["decision_status"], decision_reason=payload["decision_reason"],
        policy_version=payload["policy_version"], model_version=payload["model_version"],
        evidence=tuple(_item_from_payload(item) for item in payload["evidence"]),
        source_ref=payload["source_ref"], canonicalization_version=payload["canonicalization_version"],
    )
    return snapshot, row[1]


def append_event(memory_id: str, event_type: str, trusted_state: str, details: dict[str, Any]) -> None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO verification_events (id, memory_id, event_type, trusted_state, details) VALUES (%s,%s,%s,%s,%s::JSONB)",
            (str(uuid.uuid4()), memory_id, event_type, trusted_state, json.dumps(details)),
        )
        conn.commit()


def record_incident(memory_id: str, kind: str, summary: str, tags: list[str]) -> str:
    incident_id = str(uuid.uuid4())
    vector = "[" + ",".join(str(v) for v in incident_signature(tags)) + "]"
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO verification_incidents (id, memory_id, kind, summary, tags, signature) VALUES (%s,%s,%s,%s,%s::JSONB,%s::VECTOR)",
            (incident_id, memory_id, kind, summary, json.dumps(tags), vector),
        )
        conn.commit()
    return incident_id


def similar_incidents(tags: list[str], limit: int = 5) -> list[dict[str, Any]]:
    vector = "[" + ",".join(str(v) for v in incident_signature(tags)) + "]"
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, memory_id, kind, summary, tags, signature <-> %s::VECTOR AS distance FROM verification_incidents ORDER BY signature <-> %s::VECTOR LIMIT %s",
            (vector, vector, limit),
        )
        rows = cur.fetchall()
    return [{"id": str(r[0]), "memory_id": str(r[1]), "kind": r[2], "summary": r[3], "tags": r[4], "distance": float(r[5])} for r in rows]
