from __future__ import annotations

import json
import os
from typing import Any


class BedrockClient:
    def __init__(self, runtime: Any | None = None) -> None:
        if runtime is None:
            import boto3

            runtime = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"))
        self.runtime = runtime
        self.explanation_model_id = os.environ["BEDROCK_EXPLANATION_MODEL_ID"]
        self.embedding_model_id = os.getenv("BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")

    def embed(self, text: str) -> list[float]:
        response = self.runtime.invoke_model(
            modelId=self.embedding_model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({"inputText": text, "dimensions": 1024, "normalize": True}),
        )
        payload = json.loads(response["body"].read())
        embedding = payload.get("embedding")
        if not isinstance(embedding, list) or len(embedding) != 1024:
            raise RuntimeError("Bedrock embedding response did not contain a 1024-dimension vector")
        return [float(value) for value in embedding]

    def explain(self, trusted_result: dict[str, Any]) -> str:
        # The model receives only deterministic classifications needed for explanation.
        # Evidence payloads, hashes, provenance internals, and mutable trusted state stay outside the prompt.
        changes = [
            {"evidence_id": change["evidence_id"], "change": change["change"]}
            for change in trusted_result["changes"]
        ]
        locked = {
            "historical_integrity": trusted_result["historical_integrity"],
            "historical_decision": trusted_result["historical_decision"],
            "current_applicability": trusted_result["current_applicability"],
            "changes": changes,
        }
        prompt = (
            "Explain this deterministic EvidenceBound result briefly. "
            "Do not add evidence or alter classifications, provenance, or decisions. "
            "Historical integrity and current applicability are separate.\n"
            + json.dumps(locked, sort_keys=True, separators=(",", ":"))
        )
        response = self.runtime.converse(
            modelId=self.explanation_model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 48, "temperature": 0.0},
        )
        blocks = response.get("output", {}).get("message", {}).get("content", [])
        text = "".join(block.get("text", "") for block in blocks if isinstance(block, dict)).strip()
        if not text:
            raise RuntimeError("Bedrock explanation was empty")
        return text
