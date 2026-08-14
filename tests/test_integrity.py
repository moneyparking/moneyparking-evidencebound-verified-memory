from copy import deepcopy
from evidencebound.core import FAIL_CLOSED, INTEGRITY_VERIFIED, build_snapshot, verify_snapshot
from evidencebound.demo import demo_evidence


def test_integrity_versions_and_modified_payload():
    t0, _, _ = demo_evidence()
    snapshot = build_snapshot(memory_id="m", session_id="s", decision_state="VERIFIED", evidence=t0, policy_version="p1", proof_version="v1", created_at="2026-08-13T12:00:00Z")
    assert verify_snapshot(snapshot, expected_policy_version="p1", expected_proof_version="v1")["state"] == INTEGRITY_VERIFIED
    assert verify_snapshot(snapshot, expected_policy_version="p2")["state"] == FAIL_CLOSED
    modified = deepcopy(snapshot)
    modified["evidence"][0]["value"] = "modified"
    assert verify_snapshot(modified)["state"] == FAIL_CLOSED
