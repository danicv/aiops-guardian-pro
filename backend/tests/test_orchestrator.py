from app.orchestrator import run_investigation

def test_runtime_flow(monkeypatch):
    from app.orchestrator import notifications, repo
    monkeypatch.setattr(repo, "create_approval", lambda *args: "APR-TEST")
    monkeypatch.setattr(notifications, "send_approval_request", lambda *args: {"status": "suppressed"})
    r=run_investigation({"telemetry_mode":"demo","investigation_id":"INV-TEST","query":"Why is checkout-api failing after today's deployment?","application":"checkout-api","environment":"prod","namespace":"default"})
    assert r["confidence_score"]>=0.75
    assert r["guardrail"]["approval_required"] is True

    assert len(r["sre_metrics"]) == 4
    assert [step["step"] for step in r["action_plan"]] == ["Contain", "Remediate", "Verify"]
    assert len(r["instrumentation"]) == 3
    assert "simulated" in r["telemetry_notice"]
    assert r["sre_metrics"][0]["query"].startswith("100 * ")


def test_release_risk_preserves_explicit_demo_mode(monkeypatch):
    from app.api import routes
    from app.schemas import ReleaseRiskRequest
    monkeypatch.setattr(routes, 'investigate', lambda request: request.model_dump())
    request = ReleaseRiskRequest(application='checkout-api', environment='prod', version='v2', changes={'memory': '128Mi'})
    result = routes.release_risk(request)
    assert result['telemetry_mode'] == 'demo'
    assert 'v2' in result['query']
    assert '128Mi' in result['query']
