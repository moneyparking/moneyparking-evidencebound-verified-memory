from __future__ import annotations

from evidencebound.models import EvidenceItem, Snapshot


def t0_snapshot() -> Snapshot:
    return Snapshot(
        decision_status="VERIFIED", decision_reason="Evidence met bounded policy at T0.",
        policy_version="policy-1", model_version="deterministic-core-1",
        source_ref="signalreview:fixture:judge-demo",
        evidence=(
            EvidenceItem("unchanged", "Team identity", "Alpha FC", "official://fixture", "official", "2026-08-13T09:00:00Z"),
            EvidenceItem("changed", "Availability score", 0.82, "official://availability", "official", "2026-08-13T09:00:00Z"),
            EvidenceItem("stale", "Weather snapshot", "clear", "official://weather", "official", "2026-08-13T09:00:00Z", "2026-08-13T10:00:00Z"),
        ),
    )


def t1_evidence() -> tuple[EvidenceItem, ...]:
    return (
        EvidenceItem("unchanged", "Team identity", "Alpha FC", "official://fixture", "official", "2026-08-13T09:00:00Z"),
        EvidenceItem("changed", "Availability score", 0.61, "official://availability", "official", "2026-08-13T12:00:00Z"),
        EvidenceItem("stale", "Weather snapshot", "clear", "official://weather", "official", "2026-08-13T09:00:00Z", "2026-08-13T10:00:00Z"),
        EvidenceItem("new", "Late team bulletin", "player unavailable", "official://bulletin", "official", "2026-08-13T12:00:00Z"),
    )
