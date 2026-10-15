from .mcp_client import mcp_gateway
from .repository import repo
from .guardrails import require_operational_actions, evaluate_action

def execute_approved_action(approval):
    require_operational_actions()
    action=approval["action"]
    if approval.get("status") != "approved" or evaluate_action(action, approval.get("environment", "prod")).decision == "BLOCK":
        raise PermissionError("Action is not approved or is prohibited by policy.")
    if action=="rollback_deployment":
        outcome=mcp_gateway.rollback("default","checkout-api","v1.9.0")
    elif action=="review_release":
        outcome={"status":"approved-for-promotion-review","action":action}
    else:
        outcome={"status":"no-op","action":action}
    repo.audit("remediation.executed",approval.get("decided_by","approver"),approval["id"],outcome)
    return outcome
