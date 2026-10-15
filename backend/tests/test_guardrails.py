from app.guardrails import evaluate_action, validate_rca

def test_prod_rollback_requires_approval(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "decision_support_only", False)
    d=evaluate_action("rollback_deployment","prod"); assert d.approval_required and d.risk=="HIGH"
def test_prohibited_blocked(): assert evaluate_action("delete_cluster","prod").decision=="BLOCK"
def test_validation(): assert validate_rca(0.95,5)[0]

def test_unknown_action_denied_by_default():
    assert evaluate_action("format_disk", "prod").decision == "BLOCK"

def test_evaluation_is_derived_from_state_not_constant():
    from app.evaluation import evaluate_response
    weak = evaluate_response({"environment": "prod"})
    strong = evaluate_response({
        "environment": "prod", "root_cause": "x", "confidence_score": 0.9,
        "evidence": [{"source": "a"}, {"source": "b"}], "validation": {"is_sufficient": True},
        "recommended_action": "rollback_deployment",
        "guardrail": {"decision": evaluate_action("rollback_deployment", "prod").decision}})
    assert not weak["passed"] and strong["passed"] and weak["score"] < strong["score"]
