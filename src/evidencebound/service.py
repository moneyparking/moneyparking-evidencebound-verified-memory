from __future__ import annotations

from datetime import UTC, datetime

from .diff import compare_evidence
from .integrity import verify_snapshot
from .models import EvidenceItem, ReopenResult
from .policy import evaluate_applicability
from .repository import append_event, load_snapshot, record_incident


def reopen_memory(
    memory_id: str,
    current_evidence: tuple[EvidenceItem, ...],
    *,
    policy_version_t1: str,
    now: datetime | None = None,
) -> ReopenResult:
    snapshot, stored_hash = load_snapshot(memory_id)
    integrity = verify_snapshot(snapshot, stored_hash)
    if integrity != "VERIFIED":
        append_event(memory_id, "T1_REOPEN", "FAIL_CLOSED", {"reason": "historical integrity mismatch"})
        return ReopenResult(memory_id, "FAIL_CLOSED", "REVIEW_REQUIRED", (), snapshot.policy_version, policy_version_t1)
    diffs = compare_evidence(snapshot.evidence, current_evidence, now=now or datetime.now(UTC))
    applicability = evaluate_applicability(diffs, policy_version_t0=snapshot.policy_version, policy_version_t1=policy_version_t1)
    append_event(memory_id, "T1_REOPEN", applicability, {"historical_integrity": integrity, "diffs": [d.__dict__ for d in diffs]})
    material_tags = [d.state.lower() for d in diffs if d.state in {"CHANGED", "STALE", "MISSING", "REFUTED"}]
    if material_tags:
        record_incident(memory_id, "APPLICABILITY_REVIEW", "T1 evidence requires decision review", material_tags)
    return ReopenResult(memory_id, "VERIFIED", applicability, diffs, snapshot.policy_version, policy_version_t1)
