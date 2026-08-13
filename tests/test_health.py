import json

from evidencebound.handler import lambda_handler


def test_health_endpoint():
    event = {"rawPath": "/health", "requestContext": {"http": {"method": "GET"}}}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    assert json.loads(response["body"])["status"] == "ok"
