import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import incident_cases
from app.db import Base

# (query as built by HistoryAgent: user text + evidence signals, expected best case)
LABELLED = [
    ("Simulate checkout-api OOMKilled after production release with reduced memory limit "
     "pod restarts 5xx p95 latency memory limit 1Gi to 128Mi", "SYN-K8S-001"),
    ("checkout-api p95 latency rose requests waited for database connections timeouts", "SYN-APP-001"),
    ("checkout-api latency rises after cache rollout, database reads surge, request rate steady", "SYN-APP-005"),
    ("checkout-api 500s isolated to new flow after feature flag enablement", "SYN-APP-007"),
    ("checkout-api 5xx rises, dependency responds 401, failure begins at token expiry", "SYN-APP-009"),
]


@pytest.fixture
def seeded(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    monkeypatch.setattr(incident_cases, 'SessionLocal', sessionmaker(bind=engine))
    incident_cases.seed_demo_cases()
    yield
    engine.dispose()


def test_retrieval_top1_accuracy(seeded):
    hits = {}
    for query, expected in LABELLED:
        top = incident_cases.search_incident_cases(query, limit=3)
        hits[expected] = top[0]["case_id"] if top else None
    wrong = {exp: got for exp, got in hits.items() if exp != got}
    assert len(wrong) <= 1, f"top-1 misses (expected -> got): {wrong}"


def test_distinctive_symptom_outranks_generic_service_terms(seeded):
    top = incident_cases.search_incident_cases(LABELLED[0][0], limit=3)
    assert top[0]["case_id"] == "SYN-K8S-001"


def test_agents_rank_the_oom_precedent_first_in_the_demo_scenario(seeded):
    from app.agents.diagnostic import KubernetesAgent, MonitoringAgent, ChangeAgent, RAGAgent, HistoryAgent
    state = {"query": "Simulate checkout-api OOMKilled incidents after a production release with a reduced memory limit.",
             "evidence": []}
    for agent in (KubernetesAgent(), MonitoringAgent(), ChangeAgent()):
        state["evidence"] += agent.run(state).evidence
    for agent in (RAGAgent(), HistoryAgent()):
        result = agent.run(state)
        ids = [c["case_id"] for c in result.data["similar_incidents"]]
        print(agent.name, ids, [c["retrieval_score"] for c in result.data["similar_incidents"]])
        state["evidence"] += result.evidence
        assert ids[0] == "SYN-K8S-001", (agent.name, ids)
