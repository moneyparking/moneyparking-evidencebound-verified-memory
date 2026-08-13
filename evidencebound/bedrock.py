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
            "amazon.titan-text-premier-v1:0",
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
        response = self.runtime.invoke_model(
            modelId=self.explanation_model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(
                {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": 48,
                        "temperature": 0.0,
                    },
                },
                separators=(",", ":"),
            ),
        )
        payload = json.loads(response["body"].read())
        results = payload.get("results")
        if not isinstance(results, list) or not results:
            raise RuntimeError("Bedrock Titan Text response had no results")
        text = results[0].get("outputText") if isinstance(results[0], dict) else None
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("Bedrock Titan Text explanation was empty")
        return text.strip()
