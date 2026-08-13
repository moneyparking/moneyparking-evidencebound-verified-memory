"""EvidenceBound Verified Memory core."""

from .diff import compare_evidence
from .integrity import compute_snapshot_hash, verify_snapshot
from .policy import evaluate_applicability

__all__ = ["compare_evidence", "compute_snapshot_hash", "verify_snapshot", "evaluate_applicability"]
