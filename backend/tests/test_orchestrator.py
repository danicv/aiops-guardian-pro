from app.orchestrator import run_investigation

def test_runtime_flow():
    r=run_investigation({"investigation_id":"INV-TEST","query":"Why is checkout-api failing after today's deployment?","application":"checkout-api","environment":"prod","namespace":"default"})
    assert r["confidence_score"]>=0.75
    assert r["guardrail"]["approval_required"] is True
