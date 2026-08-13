from evidencebound.core import CHANGE_CHANGED, CHANGE_REFUTED, diff_evidence
from evidencebound.demo import demo_evidence


def test_changed_is_not_refuted():
    before, current, at = demo_evidence()
    changes = diff_evidence(before, current, evaluated_at=at)
    state = next(row["change"] for row in changes if row["evidence_id"] == "availability-status")
    assert state == CHANGE_CHANGED
    assert state != CHANGE_REFUTED
