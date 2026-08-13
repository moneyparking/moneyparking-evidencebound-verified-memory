from __future__ import annotations

import json
import os
from typing import Any


class BedrockClient:
    def __init__(self, session: Any | None = None, http: Any | None = None) -> None:
        import boto3
        import urllib3

        self.session = session or boto3.Session()
        self.http = http or urllib3.PoolManager()
        self.region = os.getenv("BEDROCK_REGION", os.getenv("AWS_REGION", "us-east-1"))
        self.explanation_model_id = os.getenv(
            "BEDROCK_EXPLANATION_MODEL_ID",
            "amazon.nova-micro-v1:0",
        )

    def explain(self, trusted_result: dict[str, Any]) -> str:
        import urllib3
        from botocore.auth import SigV4Auth
        from botocore.awsrequest import AWSRequest

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
        body = json.dumps(
            {
                "model": self.explanation_model_id,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 48,
                "temperature": 0.0,
            },
            separators=(",", ":"),
        ).encode("utf-8")
        url = f"https://bedrock-mantle.{self.region}.api.aws/v1/chat/completions"
        credentials = self.session.get_credentials()
        if credentials is None:
            raise RuntimeError("AWS credentials unavailable for Bedrock Mantle")
        request = AWSRequest(
            method="POST",
            url=url,
            data=body,
            headers={"Content-Type": "application/json"},
        )
        SigV4Auth(credentials.get_frozen_credentials(), "bedrock-mantle", self.region).add_auth(request)
        response = self.http.request(
            "POST",
            url,
            body=body,
            headers=dict(request.headers),
            timeout=urllib3.Timeout(total=20.0),
            retries=False,
        )
        if response.status != 200:
            raise RuntimeError(f"Bedrock Mantle request failed with HTTP {response.status}")
        payload = json.loads(response.data.decode("utf-8"))
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("Bedrock Mantle response had no choices")
        message = choices[0].get("message", {})
        text = message.get("content") if isinstance(message, dict) else None
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("Bedrock Mantle explanation was empty")
        return text.strip()
