from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal

DecisionStatus = Literal["VERIFIED", "BLOCKED"]
IntegrityStatus = Literal["VERIFIED", "FAIL_CLOSED"]
ApplicabilityStatus = Literal["APPLICABLE", "REVIEW_REQUIRED"]
DiffState = Literal["UNCHANGED", "NEW", "CHANGED", "STALE", "MISSING", "REFUTED"]


@dataclass(frozen=True)
class EvidenceItem:
    evidence_key: str
    claim: str
    value: Any
    source_uri: str
    source_class: str
    observed_at: str
    valid_until: str | None = None
    expected: bool = True
    provenance_valid: bool = True
    refutes_evidence_hash: str | None = None

    def canonical_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Snapshot:
    decision_status: DecisionStatus
    decision_reason: str
    policy_version: str
    model_version: str
    evidence: tuple[EvidenceItem, ...]
    source_ref: str
    canonicalization_version: str = "eb-c14n-v1"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "canonicalization_version": self.canonicalization_version,
            "decision_reason": self.decision_reason,
            "decision_status": self.decision_status,
            "evidence": [item.canonical_dict() for item in sorted(self.evidence, key=lambda x: x.evidence_key)],
            "model_version": self.model_version,
            "policy_version": self.policy_version,
            "source_ref": self.source_ref,
        }


@dataclass(frozen=True)
class DiffEntry:
    evidence_key: str
    state: DiffState
    previous_hash: str | None
    current_hash: str | None
    reason: str


@dataclass(frozen=True)
class ReopenResult:
    memory_id: str
    historical_integrity: IntegrityStatus
    current_applicability: ApplicabilityStatus
    diffs: tuple[DiffEntry, ...]
    policy_version_t0: str
    policy_version_t1: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
