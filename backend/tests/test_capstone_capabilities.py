import logging
import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import embeddings, feedback, incident_cases
from app.config import settings
from app.db import Base
from app.redaction import install_log_redaction, redact

QUERY = "checkout-api pods keep restarting and are OOMKilled after the memory limit was lowered"


@pytest.fixture
def seeded(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(incident_cases, 'SessionLocal', factory)
    monkeypatch.setattr(feedback, 'SessionLocal', factory)
    incident_cases.seed_demo_cases()
    yield
    engine.dispose()


def fake_embed(monkeypatch, vectors_by_keyword):
    """Deterministic embeddings: one axis per concept keyword, so similarity is predictable offline."""
    axes = list(vectors_by_keyword)

    def embed(texts):
        return [np.array([1.0 if any(word in text.casefold() for word in vectors_by_keyword[a]) else 0.0 for a in axes]
                         + [0.01]) for text in texts]
    monkeypatch.setattr(embeddings, 'embed', embed)
    monkeypatch.setattr(settings, 'embedding_base_url', 'http://embeddings.test')
    monkeypatch.setattr(settings, 'embedding_model', 'fake')


def test_redaction_removes_pii_and_secrets():
    text = ("user jane.doe@example.com from 10.1.2.3 called +1 415 555 0134 with card 4111 1111 1111 1111 "
            "password=hunter2 Authorization: Bearer abcdefghijklmnop")
    clean = redact(text)
    for leaked in ("jane.doe", "10.1.2.3", "415 555", "4111", "hunter2", "abcdefghijklmnop"):
        assert leaked not in clean
    assert redact({"note": ["a@b.io"], "n": 5}) == {"note": ["[REDACTED_EMAIL]"], "n": 5}


def test_log_records_are_redacted(caplog):
    install_log_redaction()
    with caplog.at_level(logging.WARNING):
        logging.getLogger("guardian.test").warning("failed for %s", "bob@example.com")
    assert "bob@example.com" not in caplog.text and "[CONTENT OMITTED FOR PRIVACY]" in caplog.text


def test_semantic_retrieval_matches_paraphrase_that_lexical_misses(seeded, monkeypatch):
    paraphrase = "containers get killed for exceeding their RAM allowance"
    assert not [c for c in incident_cases.search_incident_cases(paraphrase) if c["case_id"] == "SYN-K8S-001"]
    fake_embed(monkeypatch, {"oom": ["oomkilled", "ram allowance", "memory limit"]})
    top = incident_cases.retrieve_cases(paraphrase, limit=3)
    assert top[0]["case_id"] == "SYN-K8S-001" and top[0]["retrieval_method"] == "embedding"


def test_unrelated_query_returns_no_precedent(seeded, monkeypatch):
    fake_embed(monkeypatch, {"oom": ["oomkilled"], "ui": ["button colour"]})
    assert incident_cases.retrieve_cases("the login button colour is wrong", limit=3) == []


def test_embedding_outage_falls_back_to_lexical(seeded, monkeypatch):
    monkeypatch.setattr(settings, 'embedding_base_url', 'http://embeddings.test')
    monkeypatch.setattr(settings, 'embedding_model', 'fake')

    def broken(texts):
        raise ConnectionError("down")
    monkeypatch.setattr(embeddings, 'embed', broken)
    top = incident_cases.retrieve_cases(QUERY, limit=3)
    assert top and top[0]["retrieval_method"] == "lexical"


def test_feedback_changes_ranking_and_is_bounded(seeded):
    before = incident_cases.retrieve_cases(QUERY, limit=3)
    first, runner_up = before[0]["case_id"], before[1]["case_id"]
    for _ in range(10):
        feedback.record_feedback(first, helpful=False)
    assert feedback.case_adjustments()[first] == -feedback.MAX_NET
    after = incident_cases.retrieve_cases(QUERY, limit=3)
    assert after[0]["case_id"] != first or after[0]["retrieval_score"] < before[0]["retrieval_score"]
    assert next(c for c in after if c["case_id"] == first)["feedback_net"] == -feedback.MAX_NET


def test_feedback_rejects_unknown_case(seeded):
    with pytest.raises(LookupError):
        feedback.record_feedback("NOPE-1", helpful=True)
