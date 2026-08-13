from __future__ import annotations

from .models import DiffEntry

REVIEW_STATES = frozenset({"CHANGED", "STALE", "MISSING", "REFUTED"})


def evaluate_applicability(
    diffs: tuple[DiffEntry, ...], *, policy_version_t0: str, policy_version_t1: str
) -> str:
    if policy_version_t0 != policy_version_t1:
        return "REVIEW_REQUIRED"
    if any(item.state in REVIEW_STATES for item in diffs):
        return "REVIEW_REQUIRED"
    return "APPLICABLE"
