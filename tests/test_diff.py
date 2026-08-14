from datetime import datetime, timezone
from evidencebound.core import INTEGRITY_VERIFIED, REVIEW_REQUIRED, current_applicability, diff_evidence
from evidencebound.demo import demo_evidence


def test_demo_diff_and_applicability():
    t0, t1, at = demo_evidence(datetime(2026, 8, 13, tzinfo=timezone.utc))
    changes = diff_evidence(t0, t1, evaluated_at=at)
    assert {row["change"] for row in changes} == {"UNCHANGED", "CHANGED", "STALE", "NEW"}
    assert current_applicability(INTEGRITY_VERIFIED, changes) == REVIEW_REQUIRED
