from datetime import UTC, datetime

from evidencebound.diff import compare_evidence
from evidencebound.integrity import compute_snapshot_hash, evidence_hash, verify_snapshot
from evidencebound.models import EvidenceItem, Snapshot
from evidencebound.policy import evaluate_applicability


def item(key: str, value: object, **kwargs: object) -> EvidenceItem:
    return EvidenceItem(key, key, value, "official://source", "official", "2026-08-13T09:00:00Z", **kwargs)


def snapshot(evidence: tuple[EvidenceItem, ...], policy: str = "p1") -> Snapshot:
    return Snapshot("VERIFIED", "bounded decision", policy, "m1", evidence, "ref")


def test_tamper_fails_closed() -> None:
    original = snapshot((item("a", 1),))
    stored_hash = compute_snapshot_hash(original)
    tampered = snapshot((item("a", 2),))
    assert verify_snapshot(original, stored_hash) == "VERIFIED"
    assert verify_snapshot(tampered, stored_hash) == "FAIL_CLOSED"


def test_changed_hash_is_not_refuted() -> None:
    diff = compare_evidence((item("a", 1),), (item("a", 2),))
    assert diff[0].state == "CHANGED"
    assert diff[0].state != "REFUTED"


def test_refuted_requires_explicit_valid_contradiction() -> None:
    old = item("a", 1)
    new = item("a", 2, refutes_evidence_hash=evidence_hash(old), provenance_valid=True)
    assert compare_evidence((old,), (new,))[0].state == "REFUTED"


def test_integrity_verified_applicability_review_required() -> None:
    old = snapshot((item("a", 1),))
    diffs = compare_evidence(old.evidence, (item("a", 2),))
    assert verify_snapshot(old, compute_snapshot_hash(old)) == "VERIFIED"
    assert evaluate_applicability(diffs, policy_version_t0="p1", policy_version_t1="p1") == "REVIEW_REQUIRED"


def test_policy_version_drift_requires_review() -> None:
    same = (item("a", 1),)
    assert evaluate_applicability(compare_evidence(same, same), policy_version_t0="p1", policy_version_t1="p2") == "REVIEW_REQUIRED"


def test_canonical_diff_states() -> None:
    now = datetime(2026, 8, 13, 13, tzinfo=UTC)
    old = (item("same", 1), item("changed", 1), item("stale", 1, valid_until="2026-08-13T10:00:00Z"))
    new = (item("same", 1), item("changed", 2), item("stale", 1, valid_until="2026-08-13T10:00:00Z"), item("new", 4))
    assert {x.state for x in compare_evidence(old, new, now=now)} == {"UNCHANGED", "CHANGED", "STALE", "NEW"}


def test_missing_is_explicit() -> None:
    assert compare_evidence((item("required", 1),), ())[0].state == "MISSING"
