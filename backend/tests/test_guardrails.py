from app.guardrails import evaluate_action, validate_rca

def test_prod_rollback_requires_approval():
    d=evaluate_action("rollback_deployment","prod"); assert d.approval_required and d.risk=="HIGH"
def test_prohibited_blocked(): assert evaluate_action("delete_cluster","prod").decision=="BLOCK"
def test_validation(): assert validate_rca(0.95,5)[0]
