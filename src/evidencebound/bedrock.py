from __future__ import annotations

import hashlib
import os
from typing import Any

from .canonical import canonical_json

SYSTEM_RULES = """You are the EvidenceBound explanation layer. Explain deterministic verified-memory results only. Never alter historical_integrity, current_applicability, diff states, provenance, or confidence. Never invent evidence. If data is missing, say it is missing."""


def _client():
    import boto3
    return boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))


def explain(result: dict[str, Any]) -> dict[str, Any]:
    model_id = os.environ.get("BEDROCK_EXPLANATION_MODEL_ID")
    if not model_id:
        raise RuntimeError("BEDROCK_EXPLANATION_MODEL_ID is required")
    trusted = canonical_json(result)
    request = {
        "messages": [{"role": "user", "content": [{"text": f"Explain this trusted result without changing it:\n{trusted}"}]}],
        "system": [{"text": SYSTEM_RULES}],
        "inferenceConfig": {"maxTokens": 500, "temperature": 0.0},
    }
    response = _client().converse(modelId=model_id, **request)
    text = response["output"]["message"]["content"][0]["text"]
    return {"model_id": model_id, "request_sha256": hashlib.sha256(trusted.encode()).hexdigest(), "explanation": text, "trusted_state": result}
