from typing import Any, Literal
from pydantic import BaseModel, Field, EmailStr

EnvironmentName = Literal["dev", "test", "stage", "prod"]

class InvestigationRequest(BaseModel):
    query: str
    application: str = "checkout-api"
    environment: EnvironmentName = "prod"
    namespace: str = "default"

class ReleaseRiskRequest(BaseModel):
    application: str
    environment: EnvironmentName
    version: str
    previous_version: str | None = None
    changes: dict[str, Any] = Field(default_factory=dict)

class ApprovalDecision(BaseModel):
    decided_by: EmailStr
    comment: str = ""

class IntegrationCreate(BaseModel):
    provider: str
    name: str
    configuration: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True

class NotificationRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
