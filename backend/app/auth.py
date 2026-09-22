import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    subject: str
    roles: frozenset[str]


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _payload(credentials: HTTPAuthorizationCredentials) -> dict:
    if credentials.scheme.lower() != "bearer":
        raise ValueError("Bearer authentication is required.")
    parts = credentials.credentials.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid bearer token.")
    header_raw, payload_raw, signature = parts
    header = json.loads(_decode(header_raw))
    payload = json.loads(_decode(payload_raw))
    if header.get("alg") != "HS256" or header.get("typ") != "JWT":
        raise ValueError("Unsupported bearer token.")
    expected = hmac.new(settings.auth_secret.encode(), f"{header_raw}.{payload_raw}".encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _decode(signature)):
        raise ValueError("Invalid bearer token.")
    if not isinstance(payload.get("sub"), str) or not payload["sub"]:
        raise ValueError("Bearer token subject is required.")
    if payload.get("exp") is not None and (not isinstance(payload["exp"], (int, float)) or payload["exp"] <= time.time()):
        raise ValueError("Bearer token has expired.")
    roles = payload.get("roles", [])
    if isinstance(roles, str):
        roles = [roles]
    if not isinstance(roles, list) or not all(isinstance(role, str) for role in roles):
        raise ValueError("Bearer token roles are invalid.")
    return {"subject": payload["sub"], "roles": frozenset(roles)}


def current_principal(credentials: HTTPAuthorizationCredentials | None = Security(bearer)) -> Principal:
    if credentials is None:
        if not settings.auth_required:
            return Principal("local-demo", frozenset({"viewer", "approver", "admin"}))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = _payload(credentials)
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token.", headers={"WWW-Authenticate": "Bearer"}) from None
    return Principal(payload["subject"], payload["roles"])


def require_role(role: str):
    def dependency(principal: Principal = Depends(current_principal)) -> Principal:
        if role not in principal.roles and "admin" not in principal.roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Role required: {role}.")
        return principal
    return dependency


viewer = Depends(require_role("viewer"))
approver = Depends(require_role("approver"))