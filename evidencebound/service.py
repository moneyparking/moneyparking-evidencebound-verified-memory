from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4

from .core import FAIL_CLOSED, TRUSTED_DECISION_VERIFIED, build_snapshot, current_applicability, diff_evidence, verify_snapshot
from .demo import demo_evidence

POLICY_VERSION = "evidencebound-policy-1"
PROOF_VERSION = "evidencebound-proof-1"


class Repository(Protocol):
    def save_snapshot(self, snapshot: dict[str, Any]) -> None: ...
    def load_latest(self, memory_id: str) -> dict[str, Any] | None: ...
    def save_incident(self, *, memory_id: str, incident_type: str, text: str, embedding: list[float]) -> None: ...
    def recall_incidents(self, *, memory_id: str, embedding: list[float], limit: int = 3) -> list[dict[str, Any]]: ...
    def tooling_evidence(self) -> dict[str, Any]: ...


class Explainer(Protocol):
    def embed(self, text: str) -> list[float]: ...
    def explain(self, trusted_result: dict[str, Any]) -> str: ...


class EvidenceBoundService:
    def __init__(self, repository: Repository, bedrock: Explainer) -> None:
        self.repository = repository
        self.bedrock = bedrock

    def save_t0(self) -> dict[str, Any]:
        evidence, _, _ = demo_evidence()
        memory_id, session_id = str(uuid4()), str(uuid4())
        snapshot = build_snapshot(memory_id=memory_id, session_id=session_id, decision_state=TRUSTED_DECISION_VERIFIED, evidence=evidence, policy_version=POLICY_VERSION, proof_version=PROOF_VERSION, created_at=datetime.now(timezone.utc))
        self.repository.save_snapshot(snapshot)
        incident_text = f"T0 decision VERIFIED under {POLICY_VERSION}; evidence hash {snapshot['evidence_hash']}."
        self.repository.save_incident(memory_id=memory_id, incident_type="verified_decision", text=incident_text, embedding=self.bedrock.embed(incident_text))
        return {"memory_id": memory_id, "session_a_id": session_id, "historical_decision": snapshot["decision_state"], "record_hash": snapshot["record_hash"], "evidence_hash": snapshot["evidence_hash"], "session_a_ended": True}

    def reopen_t1(self, memory_id: str) -> dict[str, Any]:
        session_b_id = str(uuid4())
        snapshot = self.repository.load_latest(memory_id)
        if snapshot is None:
            return {"memory_id": memory_id, "session_b_id": session_b_id, "historical_integrity": FAIL_CLOSED, "current_applicability": FAIL_CLOSED, "reason": "historical_memory_missing"}
        integrity = verify_snapshot(snapshot, expected_policy_version=POLICY_VERSION, expected_proof_version=PROOF_VERSION)
        if integrity["state"] == FAIL_CLOSED:
            return {"memory_id": memory_id, "session_b_id": session_b_id, "historical_integrity": FAIL_CLOSED, "historical_decision": snapshot.get("decision_state"), "current_applicability": FAIL_CLOSED, "reason": integrity["reason"]}
        historical_base = datetime.fromisoformat(snapshot["evidence"][0]["observed_at"].replace("Z", "+00:00"))
        _, current, evaluated_at = demo_evidence(historical_base)
        changes = diff_evidence(snapshot["evidence"], current, evaluated_at=evaluated_at)
        result = {
            "memory_id": memory_id,
            "session_a_id": snapshot["session_id"],
            "session_b_id": session_b_id,
            "fresh_session": session_b_id != snapshot["session_id"],
            "historical_integrity": integrity["state"],
            "historical_decision": snapshot["decision_state"],
            "current_applicability": current_applicability(integrity["state"], changes),
            "changes": changes,
            "recalled_incidents": self.repository.recall_incidents(memory_id=memory_id, embedding=self.bedrock.embed("Prior verification decision and integrity evidence for this review"), limit=3),
            "record_hash": snapshot["record_hash"],
            "evidence_hash": snapshot["evidence_hash"],
            "tooling": self.repository.tooling_evidence(),
        }
        result["bedrock_explanation"] = self.bedrock.explain(result)
        return result
