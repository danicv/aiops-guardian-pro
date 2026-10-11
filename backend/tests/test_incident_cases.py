import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import incident_cases
from app import orchestrator
from app.api.routes import router
from app.config import settings
from app.db import Base


@pytest.fixture
def corpus(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(incident_cases, 'SessionLocal', factory)
    monkeypatch.setattr(settings, 'demo_data_enabled', True)
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        yield client
    engine.dispose()


def test_seed_is_idempotent_and_reports_category_mix(corpus):
    first = corpus.post('/api/demo/cases/seed', json={'confirm_synthetic': True})
    second = corpus.post('/api/demo/cases/seed', json={'confirm_synthetic': True})
    assert first.status_code == 200
    assert first.json()['inserted'] == len(incident_cases.DEMO_INCIDENT_CASES)
    assert second.json()['inserted'] == 0
    library = corpus.get('/api/demo/cases').json()
    assert library['count'] == len(incident_cases.DEMO_INCIDENT_CASES)
    assert library['synthetic_count'] == library['count']
    assert len(library['categories']) >= 8


def test_search_returns_relevant_cases_and_labels_synthetic(corpus):
    corpus.post('/api/demo/cases/seed', json={'confirm_synthetic': True})
    matches = incident_cases.search_incident_cases('database connection pool exhausted timeout')
    assert matches
    assert matches[0]['case_id'] == 'SYN-APP-001'
    assert matches[0]['synthetic'] is True
    assert 'remediation' in matches[0] and 'verification' in matches[0]


def test_seed_endpoint_is_disabled_by_default(monkeypatch):
    monkeypatch.setattr(settings, 'demo_data_enabled', False)
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        response = client.post('/api/demo/cases/seed', json={'confirm_synthetic': True})
    assert response.status_code == 404


def test_investigation_enrichment_accepts_numeric_evidence(monkeypatch):
    class Graph:
        def invoke(self, state, config):
            return {"evidence": [{"signal": "restarts", "value": 9}], "status": "awaiting_approval"}

    case = {"case_id": "SYN-K8S-001", "title": "Memory limit reduction caused OOMs", "synthetic": True}
    monkeypatch.setattr(orchestrator, "graph", Graph())
    monkeypatch.setattr(orchestrator, "retrieve_cases", lambda *args, **kwargs: [case])
    monkeypatch.setattr(orchestrator, "create_langfuse_callback", lambda: None)

    result = orchestrator.run_investigation({
        "telemetry_mode": "demo", "investigation_id": "INV-NUMERIC-EVIDENCE",
        "query": "checkout pod restarts after memory change", "application": "checkout-api",
        "environment": "prod", "namespace": "default",
    })

    assert result["similar_incidents"] == [case]
    assert any(item["signal"] == "similar_case" for item in result["evidence"])
