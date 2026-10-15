from dataclasses import dataclass
from .config import settings
import re

REFUSAL = "Guardian is in decision-support mode. I cannot modify infrastructure or business data, approve changes, send notifications, or provide instructions to make infrastructure changes. No action was executed. Ask your incident lead to review the evidence and perform any authorized change outside Guardian."

def mutation_requested(text):
    # This is a conversational refusal aid, not the execution security boundary.
    action = r"(?:roll\s*back|rollback|restart|scale|delete|drop|deploy|terminate|reboot|execute|approve|send|modify|update|insert|truncate|patch|resize|cordon|drain)"
    noun = r"(?:roll\s*back|rollback|restart|scale(?:\s+up|\s+down)?|deployment|delete|deletion)"
    patterns = (
        rf"(?:^|[.!?;,]\s*)(?:please\s+)?(?:(?:do|perform|apply|run|execute|initiate|trigger|carry out)\s+)?(?:the\s+|a\s+)?{action}\b",
        rf"\b(?:can|could|would|will|do)\s+you\s+(?:please\s+)?(?:(?:do|perform|apply|run|execute|initiate|trigger|carry out)\s+)?(?:the\s+|a\s+)?{action}\b",
        rf"\b(?:should|could|would|can)\s+(?:i|we|you)\s+(?:please\s+)?(?:(?:do|perform|apply|run|execute)\s+)?(?:the\s+|a\s+)?{action}\b",
        rf"\b(?:i\s+)?(?:want|need|expect|request|ask)\s+you\s+to\s+(?:please\s+)?(?:the\s+|a\s+)?{action}\b",
        rf"\b(?:i\s+)?(?:want|need|request)\s+(?:a|the)\s+(?:deployment\s+)?{noun}\b",
        rf"\b(?:recommend|recommendation|suggest|suggestion|advise)\b.{{0,60}}\b(?:{action}|{noun})\b",
        rf"\bhow\s+(?:do|can|should|would)\s+(?:i|we|you)\b.{{0,60}}\b(?:{action}|{noun})\b",
        rf"\bwhat\s+(?:command|steps|way)\b.{{0,60}}\b(?:{action}|{noun})\b",
        rf"\b(?:show|tell|give)\s+(?:me\s+)?(?:how|steps|commands?)\b.{{0,60}}\b(?:{action}|{noun})\b",
        rf"\b(?:provide|give|show|tell)\s+(?:me\s+)?(?:the\s+)?commands?\s+to\s+(?:{action}|{noun})\b",
        rf"\bprovide\s+(?:me\s+)?commands?\s+to\s+(?:{action}|{noun})\b",
    )
    return any(re.search(pattern, text, re.I) for pattern in patterns)

def require_operational_actions():
    if settings.decision_support_only:
        raise PermissionError(REFUSAL)

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
    if settings.decision_support_only:
        return GuardrailDecision("BLOCK", "READ_ONLY", REFUSAL, False)
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
