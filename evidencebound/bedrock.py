from __future__ import annotations

import json
import os
from typing import Any


class BedrockClient:
    def __init__(self, runtime: Any | None = None) -> None:
        if runtime is None:
            import boto3

            runtime = boto3.client(
                "bedrock-runtime",
                region_name=os.getenv("BEDROCK_REGION", os.getenv("AWS_REGION", "us-east-1")),
            )
        self.runtime = runtime
        self.explanation_model_id = os.getenv(
            "BEDROCK_EXPLANATION_MODEL_ID",
            "amazon.nova-micro-v1:0",
        )

    def explain(self, trusted_result: dict[str, Any]) -> str:
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
        text = "".join(
            block.get("text", "") for block in blocks if isinstance(block, dict)
        ).strip()
        if not text:
            raise RuntimeError("Bedrock explanation was empty")
        return text
