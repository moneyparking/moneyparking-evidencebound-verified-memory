from copy import deepcopy

import pytest

from evidencebound.core import FAIL_CLOSED, REVIEW_REQUIRED
from evidencebound.repository import VECTOR_INDEX
from evidencebound.service import EvidenceBoundService


class Repo:
    def save_snapshot(self, snapshot):
        self.s = deepcopy(snapshot)

    def load_latest(self, memory_id):
        return deepcopy(self.s)

    def save_incident(self, **kwargs):
        pass

    def recall_incidents(self, **kwargs):
        return [{"text": "stored"}]

    def tooling_evidence(self):
        return {"vector_index": VECTOR_INDEX, "verified_memory_rows": 1}


class Model:
    def embed(self, text):
        return [0.0] * 1024

    def explain(self, result):
        return "Explanation only."


def test_fresh_session_and_separate_applicability():
    repo = Repo()
    service = EvidenceBoundService(repo, Model())
    saved = service.save_t0()
    reopened = service.reopen_t1(saved["memory_id"])
    assert saved["memory_layer"]["backend"] == "CockroachDB Cloud"
    assert saved["memory_layer"]["write_confirmed"] is True
    assert saved["memory_layer"]["readback_confirmed"] is True
    assert reopened["fresh_session"] is True
    assert reopened["session_a_id"] != reopened["session_b_id"]
    assert reopened["memory_layer"]["historical_read_confirmed"] is True
    assert reopened["memory_layer"]["record_hash_reverified"] is True
    assert reopened["memory_layer"]["vector_index"] == VECTOR_INDEX
    assert reopened["memory_layer"]["recalled_incident_count"] == 1
    assert reopened["historical_integrity"] == "VERIFIED"
    assert reopened["historical_decision"] == "VERIFIED"
    assert reopened["current_applicability"] == REVIEW_REQUIRED


def test_save_fails_closed_when_persistence_readback_does_not_match():
    class MismatchRepo(Repo):
        def load_latest(self, memory_id):
            stored = super().load_latest(memory_id)
            stored["record_hash"] = "mismatch"
            return stored

    service = EvidenceBoundService(MismatchRepo(), Model())
    with pytest.raises(RuntimeError, match="cockroach_persistence_verification_failed"):
        service.save_t0()


def test_modified_history_fails_closed():
    repo = Repo()
    service = EvidenceBoundService(repo, Model())
    saved = service.save_t0()
    repo.s["evidence"][0]["value"] = "modified"
    reopened = service.reopen_t1(saved["memory_id"])
    assert reopened["historical_integrity"] == FAIL_CLOSED
    assert reopened["current_applicability"] == FAIL_CLOSED
    assert reopened["memory_layer"]["historical_read_confirmed"] is True
    assert reopened["memory_layer"]["record_hash_reverified"] is False
    assert "bedrock_explanation" not in reopened
