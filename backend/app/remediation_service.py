from .mcp_client import mcp_gateway
from .repository import repo

def execute_approved_action(approval):
    action=approval["action"]
    if action=="rollback_deployment":
        outcome=mcp_gateway.rollback("default","checkout-api","v1.9.0")
    elif action=="review_release":
        outcome={"status":"approved-for-promotion-review","action":action}
    else:
        outcome={"status":"no-op","action":action}
    repo.audit("remediation.executed",approval.get("decided_by","approver"),approval["id"],outcome)
    return outcome
