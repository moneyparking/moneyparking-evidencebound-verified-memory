from __future__ import annotations

from collections.abc import Iterable

INCIDENT_DIMENSIONS = (
    "changed", "stale", "missing", "refuted", "policy_drift",
    "integrity_failure", "provenance_failure", "source_unavailable",
)


def incident_signature(tags: Iterable[str]) -> list[float]:
    """Deterministic domain vector for verification-incident similarity recall."""
    present = set(tags)
    return [1.0 if tag in present else 0.0 for tag in INCIDENT_DIMENSIONS]
