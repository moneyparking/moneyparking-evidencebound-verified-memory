from __future__ import annotations

import hashlib
import math
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4

from .core import (
    FAIL_CLOSED,
    TRUSTED_DECISION_VERIFIED,
    build_snapshot,
    current_applicability,
    diff_evidence,
    verify_snapshot,
)
from .demo import demo_evidence

POLICY_VERSION = "evidencebound-policy-1"
PROOF_VERSION = "evidencebound-proof-1"
VECTOR_DIMENSIONS = 1024
MEMORY_TABLE = "evidencebound_verified_memories"
INCIDENT_TABLE = "evidencebound_verification_incidents"


class Repository(Protocol):
    def save_snapshot(self, snapshot: dict[str, Any]) -> None: ...
    def load_latest(self, memory_id: str) -> dict[str, Any] | None: ...
    def save_incident(
        self,
        *,
        memory_id: str,
        incident_type: str,
        text: str,
        embedding: list[float],
    ) -> None: ...
    def recall_incidents(self, *, memory_id: str, limit: int = 3) -> list[dict[str, Any]]: ...
    def tooling_evidence(self) -> dict[str, Any]: ...


class Explainer(Protocol):
    def explain(self, trusted_result: dict[str, Any]) -> str: ...


def incident_vector(text: str) -> list[float]:
    """Build a deterministic 1024-d verification-incident signature."""
    vector = [0.0] * VECTOR_DIMENSIONS
    tokens = text.casefold().split()
    if not tokens:
        return vector
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        slot = int.from_bytes(digest[:2], "big") % VECTOR_DIMENSIONS
        vector[slot] += 1.0 if digest[2] & 1 else -1.0
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return vector
    return [value / norm for value in vector]


class EvidenceBoundService:
    def __init__(self, repository: Repository, bedrock: Explainer) -> None:
        self.repository = repository
        self.bedrock = bedrock

    def save_t0(self) -> dict[str, Any]:
        evidence, _, _ = demo_evidence()
        memory_id, session_id = str(uuid4()), str(uuid4())
        snapshot = build_snapshot(
            memory_id=memory_id,
            session_id=session_id,
            decision_state=TRUSTED_DECISION_VERIFIED,
            evidence=evidence,
            policy_version=POLICY_VERSION,
            proof_version=PROOF_VERSION,
            created_at=datetime.now(timezone.utc),
        )
        incident_text = (
            f"T0 decision VERIFIED under {POLICY_VERSION}; "
            f"evidence hash {snapshot['evidence_hash']}."
        )
        self.repository.save_snapshot(snapshot)
        self.repository.save_incident(
            memory_id=memory_id,
            incident_type="verified_decision",
            text=incident_text,
            embedding=incident_vector(incident_text),
        )

        # The public Save path does not report success until the just-written T0
        # can be read back through the repository boundary with the same proof hash.
        persisted = self.repository.load_latest(memory_id)
        if persisted is None or persisted.get("record_hash") != snapshot["record_hash"]:
            raise RuntimeError("cockroach_persistence_verification_failed")
        tooling = self.repository.tooling_evidence()

        return {
            "memory_id": memory_id,
            "session_a_id": session_id,
            "historical_decision": snapshot["decision_state"],
            "record_hash": snapshot["record_hash"],
            "evidence_hash": snapshot["evidence_hash"],
            "session_a_ended": True,
            "memory_layer": {
                "backend": "CockroachDB Cloud",
                "memory_table": MEMORY_TABLE,
                "incident_table": INCIDENT_TABLE,
                "write_confirmed": True,
                "readback_confirmed": True,
                "vector_index": tooling.get("vector_index"),
                "verified_memory_rows": tooling.get("verified_memory_rows"),
            },
        }

    def reopen_t1(self, memory_id: str) -> dict[str, Any]:
        session_b_id = str(uuid4())
        snapshot = self.repository.load_latest(memory_id)
        if snapshot is None:
            return {
                "memory_id": memory_id,
                "session_b_id": session_b_id,
                "historical_integrity": FAIL_CLOSED,
                "current_applicability": FAIL_CLOSED,
                "reason": "historical_memory_missing",
                "memory_layer": {
                    "backend": "CockroachDB Cloud",
                    "memory_table": MEMORY_TABLE,
                    "historical_read_confirmed": False,
                },
            }
        integrity = verify_snapshot(
            snapshot,
            expected_policy_version=POLICY_VERSION,
            expected_proof_version=PROOF_VERSION,
        )
        if integrity["state"] == FAIL_CLOSED:
            return {
                "memory_id": memory_id,
                "session_b_id": session_b_id,
                "historical_integrity": FAIL_CLOSED,
                "historical_decision": snapshot.get("decision_state"),
                "current_applicability": FAIL_CLOSED,
                "reason": integrity["reason"],
                "memory_layer": {
                    "backend": "CockroachDB Cloud",
                    "memory_table": MEMORY_TABLE,
                    "historical_read_confirmed": True,
                    "record_hash_reverified": False,
                },
            }
        historical_base = datetime.fromisoformat(
            snapshot["evidence"][0]["observed_at"].replace("Z", "+00:00")
        )
        _, current, evaluated_at = demo_evidence(historical_base)
        changes = diff_evidence(snapshot["evidence"], current, evaluated_at=evaluated_at)
        recalled_incidents = self.repository.recall_incidents(memory_id=memory_id, limit=3)
        tooling = self.repository.tooling_evidence()
        result = {
            "memory_id": memory_id,
            "session_a_id": snapshot["session_id"],
            "session_b_id": session_b_id,
            "fresh_session": session_b_id != snapshot["session_id"],
            "historical_integrity": integrity["state"],
            "historical_decision": snapshot["decision_state"],
            "current_applicability": current_applicability(integrity["state"], changes),
            "changes": changes,
            "recalled_incidents": recalled_incidents,
            "record_hash": snapshot["record_hash"],
            "evidence_hash": snapshot["evidence_hash"],
            "tooling": tooling,
            "memory_layer": {
                "backend": "CockroachDB Cloud",
                "memory_table": MEMORY_TABLE,
                "incident_table": INCIDENT_TABLE,
                "historical_read_confirmed": True,
                "record_hash_reverified": True,
                "vector_index": tooling.get("vector_index"),
                "recalled_incident_count": len(recalled_incidents),
                "verified_memory_rows": tooling.get("verified_memory_rows"),
            },
        }
        result["bedrock_explanation"] = self.bedrock.explain(result)
        return result
