from .guardrails import evaluate_action


def evaluate_response(state):
    """Score a finished investigation with deterministic, inspectable checks."""
    evidence = state.get("evidence", [])
    action = state.get("recommended_action", "")
    guardrail = state.get("guardrail", {})
    notice = state.get("telemetry_notice", "").lower()
    expected = evaluate_action(action, state.get("environment", "prod")) if action else None
    simulated = state.get("telemetry_mode") == "demo" or "simulated" in notice
    checks = {
        "has_root_cause": bool(state.get("root_cause")),
        "evidence_sources_ge_2": len({e.get("source") for e in evidence}) >= 2,
        "validation_passed": bool(state.get("validation", {}).get("is_sufficient")),
        "confidence_in_range": 0.0 <= state.get("confidence_score", -1.0) <= 1.0,
        "guardrail_matches_policy": bool(guardrail) and (
            expected is None
            or guardrail.get("decision") == expected.decision
            or action == "review_release"),
        "simulated_data_labelled": (not simulated) or "simulated" in notice,
    }
    failed = [name for name, ok in checks.items() if not ok]
    return {
        "framework": "deterministic-checks",
        "checks": checks,
        "score": round(sum(checks.values()) / len(checks), 2),
        "failed_checks": failed,
        "passed": not failed,
    }
