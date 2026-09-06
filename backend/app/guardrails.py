from dataclasses import dataclass
from .config import settings

@dataclass
class GuardrailDecision:
    decision: str
    risk: str
    reason: str
    approval_required: bool

READ_ONLY = {"get_pods", "get_events", "get_logs", "get_metrics", "get_pipeline", "get_incident_history"}
LOW_RISK = {"restart_pod"}
MEDIUM_RISK = {"scale_deployment"}
HIGH_RISK = {"rollback_deployment"}
PROHIBITED = {"delete_namespace", "delete_cluster", "drop_database"}

def evaluate_action(action, environment):
    if action in PROHIBITED:
        return GuardrailDecision("BLOCK", "PROHIBITED", "Action is prohibited by platform policy.", False)
    if action in READ_ONLY:
        return GuardrailDecision("ALLOW", "READ_ONLY", "Read-only diagnostic operation.", False)
    if action in HIGH_RISK:
        return GuardrailDecision("REQUIRE_APPROVAL", "HIGH", "High-risk rollback requires human approval.", True)
    if action in MEDIUM_RISK:
        return GuardrailDecision("REQUIRE_APPROVAL", "MEDIUM", "Medium-risk operational change.", True)
    if action in LOW_RISK:
        if environment == "prod" and settings.production_approval_required:
            return GuardrailDecision("REQUIRE_APPROVAL", "LOW", "Production changes require approval.", True)
        if settings.auto_execute_low_risk:
            return GuardrailDecision("ALLOW", "LOW", "Low-risk auto-execution enabled.", False)
        return GuardrailDecision("REQUIRE_APPROVAL", "LOW", "Automatic changes are disabled.", True)
    return GuardrailDecision("BLOCK", "UNKNOWN", "Unknown action is denied by default.", False)

def validate_rca(confidence, evidence_count):
    if confidence < settings.min_rca_confidence:
        return False, f"Confidence {confidence:.2f} is below threshold {settings.min_rca_confidence:.2f}."
    if evidence_count < 2:
        return False, "At least two independent evidence signals are required."
    return True, "Evidence and confidence satisfy policy."
