from copy import deepcopy

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
    assert reopened["fresh_session"] is True
    assert reopened["session_a_id"] != reopened["session_b_id"]
    assert reopened["historical_integrity"] == "VERIFIED"
    assert reopened["historical_decision"] == "VERIFIED"
    assert reopened["current_applicability"] == REVIEW_REQUIRED


def test_modified_history_fails_closed():
    repo = Repo()
    service = EvidenceBoundService(repo, Model())
    saved = service.save_t0()
    repo.s["evidence"][0]["value"] = "modified"
    reopened = service.reopen_t1(saved["memory_id"])
    assert reopened["historical_integrity"] == FAIL_CLOSED
    assert reopened["current_applicability"] == FAIL_CLOSED
    assert "bedrock_explanation" not in reopened
