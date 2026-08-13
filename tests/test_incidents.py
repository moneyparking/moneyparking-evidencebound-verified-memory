from evidencebound.incidents import incident_signature


def test_incident_signature_is_stable_and_domain_bound() -> None:
    assert incident_signature(["changed", "stale"]) == [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
