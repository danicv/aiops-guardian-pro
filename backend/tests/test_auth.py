import base64
import hashlib
import hmac
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import auth
from app.api import routes
from app.config import settings


def token(secret, subject, roles, exp=None):
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": subject, "roles": roles}
    if exp is not None:
        payload["exp"] = exp
    encode = lambda value: base64.urlsafe_b64encode(json.dumps(value, separators=(",", ":")).encode()).rstrip(b"=").decode()
    encoded_header = encode(header)
    encoded_payload = encode(payload)
    signing_input = f"{encoded_header}.{encoded_payload}"
    signature = base64.urlsafe_b64encode(hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()).rstrip(b"=").decode()
    return f"{signing_input}.{signature}"


def client(monkeypatch):
    monkeypatch.setattr(settings, "auth_required", True)
    monkeypatch.setattr(settings, "auth_secret", "test-secret")
    app = FastAPI()
    app.include_router(routes.router)
    return TestClient(app)


def test_auth_requires_token_for_protected_route(monkeypatch):
    response = client(monkeypatch).get("/api/pipelines")
    assert response.status_code == 401


def test_viewer_can_read_but_cannot_approve(monkeypatch):
    http = client(monkeypatch)
    headers = {"Authorization": f"Bearer {token('test-secret', 'viewer-1', ['viewer'])}"}
    assert http.get("/api/pipelines", headers=headers).status_code == 200
    assert http.post("/api/approvals/APR-1/approve", headers=headers, json={"decided_by": "sre@example.com"}).status_code == 403


def test_approver_can_approve(monkeypatch):
    http = client(monkeypatch)
    monkeypatch.setattr(routes.repo, "decide_approval", lambda *args: {"id": "APR-1", "action": "review_release", "environment": "prod", "status": "approved"})
    monkeypatch.setattr(routes, "execute_approved_action", lambda approval: {"status": "executed"})
    headers = {"Authorization": f"Bearer {token('test-secret', 'approver-1', ['approver'])}"}
    response = http.post("/api/approvals/APR-1/approve", headers=headers, json={"decided_by": "sre@example.com"})
    assert response.status_code == 200
    assert response.json()["execution"]["status"] == "executed"
