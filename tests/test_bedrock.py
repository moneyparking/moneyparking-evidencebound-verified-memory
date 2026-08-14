from copy import deepcopy

from evidencebound.bedrock import BedrockClient


class Runtime:
    def __init__(self):
        self.kwargs = None

    def converse(self, **kwargs):
        self.kwargs = kwargs
        return {"output": {"message": {"content": [{"text": "Bounded explanation."}]}}}


def test_bedrock_receives_only_trusted_classifications_and_cannot_mutate_state(monkeypatch):
    monkeypatch.setenv("BEDROCK_EXPLANATION_MODEL_ID", "amazon.nova-micro-v1:0")
    runtime = Runtime()
    client = BedrockClient(runtime=runtime)
    trusted = {
        "historical_integrity": "VERIFIED",
        "historical_decision": "VERIFIED",
        "current_applicability": "REVIEW_REQUIRED",
        "changes": [
            {
                "evidence_id": "availability",
                "change": "CHANGED",
                "historical_hash": "SECRET_HISTORICAL_HASH",
                "current_hash": "SECRET_CURRENT_HASH",
            }
        ],
    }
    before = deepcopy(trusted)

    explanation = client.explain(trusted)

    assert explanation == "Bounded explanation."
    assert trusted == before
    assert runtime.kwargs is not None
    prompt = runtime.kwargs["messages"][0]["content"][0]["text"]
    assert "SECRET_HISTORICAL_HASH" not in prompt
    assert "SECRET_CURRENT_HASH" not in prompt
    assert '"change":"CHANGED"' in prompt
    assert '"evidence_id":"availability"' in prompt
    assert runtime.kwargs["inferenceConfig"] == {"maxTokens": 48, "temperature": 0.0}
