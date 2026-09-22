from typing import Any, Literal
from pydantic import BaseModel, Field, EmailStr

EnvironmentName = Literal["dev", "test", "stage", "prod"]

class InvestigationRequest(BaseModel):
    telemetry_mode: Literal["live", "demo"] = "live"
    query: str
    application: str = "checkout-api"
    environment: EnvironmentName = "prod"
    namespace: str = "default"

class DemoSimulationRequest(BaseModel):
    count: int = Field(default=1, ge=1, le=10)
    application: str = "checkout-api"
    environment: EnvironmentName = "prod"
    scenario: Literal["oom-release", "latency-spike", "pipeline-failure"] = "oom-release"

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

class ConversationCreate(BaseModel):
    model_config = {"str_strip_whitespace": True}
    application: str = Field(default="checkout-api", min_length=1, max_length=128)
    environment: EnvironmentName = "prod"
    namespace: str = Field(default="aiops-guardian", min_length=1, max_length=128)
    telemetry_mode: Literal["live", "demo"] = "live"
    message: str = Field(min_length=1, max_length=4000)


class ConversationMessage(BaseModel):
    model_config = {"str_strip_whitespace": True}
    message: str = Field(min_length=1, max_length=4000)
    expected_revision: int = Field(ge=1)
    refresh_metrics: bool = False
