from copy import deepcopy
import json

import pytest

from app import conversation_engine as engine


SCOPE = {"application": "checkout-api", "namespace": "aiops-guardian", "environment": "prod", "telemetry_mode": "live"}
SNAPSHOT = {
    "telemetry_mode": "live", "snapshot_at": "2026-09-21T14:00:00Z",
    "sre_metrics": [
        {"name": "p95 latency", "value": "690 ms", "numeric_value": 690, "status": "warning", "query": 'latency{service="checkout-api"}'},
        {"name": "HTTP 5xx rate", "value": "Unavailable", "numeric_value": None, "status": "unknown"},
    ],
    "root_cause": "Root cause unconfirmed.",
}


@pytest.fixture(autouse=True)
def no_external_calls(monkeypatch):
    monkeypatch.setattr(engine.settings, "openai_api_key", "")
    monkeypatch.setattr(engine, "ChatOpenAI", lambda **kwargs: pytest.fail("Unexpected model call"))


def send(message, context=None, messages=None, result=None):
    return engine.build_reply([*(messages or []), {"role": "user", "content": message}],
                              context or {}, result if result is not None else SNAPSHOT, SCOPE)


def complete_context(**extra):
    return {"original_problem": "Checkout is slow", "symptom": "Checkout is slow", "onset": "14:00 UTC",
            "recent_change": "a deploy", "impact": "payment route", **extra}


def model_answer(**updates):
    return {"content": "Compare the reported onset against the measured latency; causality remains unconfirmed.",
            "question": "Which routes have slow spans?", "question_key": "follow_up",
            "context_updates": {key: None for key in engine.REPORT_FIELDS}, **updates}


def fake_model(monkeypatch, answer):
    captured = {}

    class Model:
        def __init__(self, **kwargs):
            captured["configuration"] = kwargs

        def with_structured_output(self, schema, **kwargs):
            captured["schema"] = schema
            captured["structured"] = kwargs
            return self

        def invoke(self, messages):
            captured["messages"] = messages
            if isinstance(answer, Exception):
                raise answer
            return answer

    monkeypatch.setattr(engine.settings, "openai_api_key", "test-secret-never-sent")
    monkeypatch.setattr(engine, "ChatOpenAI", Model)
    return captured


def test_guided_dialogue_collects_and_uses_answers_without_losing_problem():
    first = send("Checkout latency is high")
    assert first["assistant_mode"] == "guided"
    assert "no language model" in first["notice"]
    assert first["context"]["pending_question"] == "onset"

    onset = send("14:00 UTC", first["context"])
    assert onset["context"]["onset"] == "14:00 UTC"
    assert onset["context"]["pending_question"] == "recent_change"
    assert "14:00 UTC" in onset["content"]

    changed = send("Reduced the memory limit", onset["context"])
    assert changed["context"]["pending_question"] == "impact"
    assert "termination reasons" in changed["content"]

    impact = send("All payment requests", changed["context"])
    assert impact["context"]["original_problem"] == "Checkout latency is high"
    assert impact["context"]["recent_change"] == "Reduced the memory limit"
    assert "All payment requests" in impact["content"]
    assert "not independently verified" in impact["content"]


def test_unknown_answers_are_retained_and_not_requested_again():
    answer = send("Checkout is failing")
    for text in ("I don't know, what next?", "unknown", "not sure"):
        answer = send(text, answer["context"])
    assert answer["context"]["onset"] == "I don't know, what next?"
    assert answer["context"]["recent_change"] == "unknown"
    assert answer["context"]["impact"] == "not sure"
    assert answer["context"]["pending_question"] not in engine.REPORT_FIELDS


def test_side_question_is_answered_without_becoming_incident_onset():
    first = send("Checkout latency increased")
    answer = send("What does burn mean?", first["context"])
    assert "allowed failure ratio" in answer["content"]
    assert not answer["context"].get("onset")
    assert answer["context"]["pending_question"] == "onset"
    assert answer["question"] == first["question"]


def test_refresh_updates_evidence_without_consuming_pending_answer():
    first = send("Checkout is slow")
    updated = deepcopy(SNAPSHOT)
    updated["sre_metrics"][0]["value"] = "420 ms"
    answer = send("Refresh the current telemetry and reassess.",
                  {**first["context"], "_refresh_metrics": True}, result=updated)
    assert "420 ms" in answer["content"]
    assert not answer["context"].get("onset")
    assert answer["question"] == first["question"]
    assert "_refresh_metrics" not in answer["context"]


def test_explicit_correction_does_not_answer_a_different_pending_question():
    context = complete_context(pending_question="impact")
    answer = send("Correction: onset was 15:00 UTC", context)
    assert answer["context"]["onset"] == "Correction: onset was 15:00 UTC"
    assert answer["context"]["impact"] == "payment route"
    assert answer["context"]["pending_question"] == "impact"


def test_freeform_check_result_is_retained_without_question_loop():
    first = send("Show memory checks", complete_context())
    question = first["question"]
    assert "termination" in question
    next_reply = send("The termination reason is OOMKilled at 14:02", first["context"])
    assert next_reply["context"]["follow_up_answers"] == [
        {"question": question, "answer": "The termination reason is OOMKilled at 14:02"}]
    assert "unverified" in next_reply["content"]
    assert next_reply["question"] != question


def test_inputs_and_unknown_context_fields_are_preserved():
    context = complete_context(extra_state={"owner": "sre"}, pending_question="impact")
    saved = deepcopy(context)
    result = deepcopy(SNAPSHOT)
    answer = send("payment and basket", context, result=result)
    assert context == saved
    assert result == SNAPSHOT
    assert answer["context"]["extra_state"] == {"owner": "sre"}


def test_demo_and_unavailable_metrics_are_not_presented_as_live_or_healthy():
    demo = send("What happened?", result={"telemetry_mode": "demo", "sre_metrics": SNAPSHOT["sre_metrics"]})
    assert "Simulated demo snapshot" in demo["content"]
    assert "Current live snapshot" not in demo["content"]
    assert "Unknown: HTTP 5xx rate" in demo["content"]
    missing = send("What happened?", result={"sre_metrics": []})
    assert "no usable metric values" in missing["content"]
    assert "healthy" not in missing["content"].lower()


def test_query_request_uses_supplied_scoped_query():
    answer = send("Show the PromQL queries", complete_context())
    assert 'latency{service="checkout-api"}' in answer["content"]


def test_llm_receives_conversation_questions_scope_and_snapshot(monkeypatch):
    captured = fake_model(monkeypatch, model_answer())
    question = "When did the issue start?"
    history = [{"role": "user", "content": "Checkout is slow"},
               {"role": "assistant", "content": "Investigating.", "question": question}]
    answer = send("14:00 UTC", {"original_problem": "Checkout is slow", "pending_question": "onset"}, history)
    assert answer["assistant_mode"] == "llm"
    assert answer["notice"] is None
    assert captured["configuration"]["timeout"] == 12.0
    assert captured["configuration"]["max_retries"] == 0
    assert captured["configuration"]["model"] == engine.settings.openai_model
    assert captured["structured"] == {"method": "json_schema", "strict": True}
    assert captured["schema"] is engine.ConversationReply
    assert question in captured["messages"][-2]["content"]
    data = json.loads(captured["messages"][1]["content"].split("\n", 1)[1])
    assert data["scope"] == SCOPE
    assert data["snapshot"]["snapshot_at"] == SNAPSHOT["snapshot_at"]
    assert data["context"]["onset"] == "14:00 UTC"
    assert "test-secret-never-sent" not in json.dumps(captured["messages"])


def test_llm_cannot_invent_reports_or_drop_existing_context(monkeypatch):
    response = model_answer(context_updates={"symptom": None, "onset": "invented timestamp",
                                             "recent_change": "new deploy", "impact": None})
    fake_model(monkeypatch, response)
    context = {"original_problem": "Checkout is slow", "impact": "one route", "custom": "retained"}
    answer = send("I suspect a new deploy", context)
    assert not answer["context"].get("onset")
    assert answer["context"]["recent_change"] == "new deploy"
    assert answer["context"]["impact"] == "one route"
    assert answer["context"]["custom"] == "retained"
    assert answer["context"]["original_problem"] == "Checkout is slow"


def test_llm_correction_must_be_grounded_and_explicit(monkeypatch):
    response = model_answer(context_updates={"symptom": None, "onset": "15:00 UTC", "recent_change": None, "impact": None})
    fake_model(monkeypatch, response)
    answer = send("Correction: it started at 15:00 UTC", complete_context())
    assert answer["context"]["onset"] == "15:00 UTC"
    uncorrected = send("The deployment finished at 15:00 UTC", complete_context())
    assert uncorrected["context"]["onset"] == "14:00 UTC"


@pytest.mark.parametrize("response", [TimeoutError("provider timeout"), {"content": "malformed"},
                                     model_answer(content="")])
def test_provider_failure_or_invalid_output_falls_back_with_context(monkeypatch, response):
    fake_model(monkeypatch, response)
    answer = send("14:00 UTC", {"original_problem": "Checkout is slow", "pending_question": "onset"})
    assert answer["assistant_mode"] == "guided"
    assert "unavailable" in answer["notice"]
    assert answer["context"]["onset"] == "14:00 UTC"
    assert answer["context"]["pending_question"] == "recent_change"


def test_llm_does_not_repeat_answered_unknown_question(monkeypatch):
    fake_model(monkeypatch, model_answer(question="When did it start?", question_key="onset"))
    answer = send("unknown", {"original_problem": "Checkout is slow", "pending_question": "onset"})
    assert answer["context"]["onset"] == "unknown"
    assert answer["question"] is None


def test_llm_side_question_retains_pending_report(monkeypatch):
    fake_model(monkeypatch, model_answer(question=None, question_key=None))
    answer = send("Explain the burn rate", {"original_problem": "Checkout is slow", "pending_question": "onset"})
    assert not answer["context"].get("onset")
    assert answer["context"]["pending_question"] == "onset"
    assert answer["question"] == engine.QUESTIONS["onset"]
