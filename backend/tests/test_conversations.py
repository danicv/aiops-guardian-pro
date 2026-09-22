import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import router
from app import conversations
from app.config import settings
from app.db import Base
from app.models import Approval, Conversation


@pytest.fixture
def session(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(conversations, 'SessionLocal', factory)
    monkeypatch.setattr(settings, 'openai_api_key', '')
    snapshots = []
    def snapshot(scope, question):
        snapshots.append((dict(scope), question))
        return {'telemetry_mode': scope['telemetry_mode'], 'root_cause': 'Root cause unconfirmed.',
                'sre_metrics': [], 'evidence': [], 'snapshot_at': str(len(snapshots))}
    monkeypatch.setattr(conversations, 'collect_snapshot', snapshot)
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        yield client, factory, snapshots
    engine.dispose()


def begin(client):
    response = client.post('/api/conversations', json={'message': 'Checkout latency increased after a deploy.'})
    assert response.status_code == 200, response.text
    return response.json()


def test_persisted_context_followup_and_no_actions(session):
    client, factory, snapshots = session
    initial = begin(client)
    assert initial['revision'] == 1
    assert initial['messages'][-1]['question']
    response = client.post(f"/api/conversations/{initial['id']}/messages", json={
        'message': 'It started at 14:00 UTC.', 'expected_revision': 1})
    assert response.status_code == 200, response.text
    current = response.json()
    assert current['revision'] == 2
    assert len(current['messages']) == 4
    assert '14:00' in current['context']['onset']
    assert current['context']['original_problem'] == initial['messages'][0]['content']
    assert len(snapshots) == 1
    assert client.get(f"/api/conversations/{initial['id']}").json() == current
    assert client.get('/api/conversations').json()[0]['id'] == initial['id']
    with factory() as db:
        assert db.scalars(select(Approval)).all() == []


def test_refresh_retains_pending_context_and_scope(session):
    client, _, snapshots = session
    initial = begin(client)
    response = client.post(f"/api/conversations/{initial['id']}/messages", json={
        'message': 'Refresh the current telemetry and reassess.', 'expected_revision': 1, 'refresh_metrics': True})
    assert response.status_code == 200
    current = response.json()
    assert len(snapshots) == 2
    assert snapshots[0][0] == snapshots[1][0]
    assert current['result']['snapshot_at'] == '2'
    assert current['context']['pending_question'] == initial['context']['pending_question']
    assert not current['context'].get('onset')
    assert '_refresh_metrics' not in current['context']


def test_stale_revision_rejected_before_generation(session, monkeypatch):
    client, _, _ = session
    initial = begin(client)
    monkeypatch.setattr(conversations, 'build_reply', lambda *args: pytest.fail('must not generate stale reply'))
    response = client.post(f"/api/conversations/{initial['id']}/messages", json={
        'message': 'A follow-up', 'expected_revision': 2})
    assert response.status_code == 409
    assert client.get(f"/api/conversations/{initial['id']}").json()['revision'] == 1


def test_concurrent_turn_cannot_overwrite_newer_reply(session, monkeypatch):
    client, factory, _ = session
    initial = begin(client)
    original = conversations.build_reply
    def competing_reply(*args):
        reply = original(*args)
        with factory() as db:
            db.execute(update(Conversation).where(Conversation.id == initial['id']).values(revision=2))
            db.commit()
        return reply
    monkeypatch.setattr(conversations, 'build_reply', competing_reply)
    response = client.post(f"/api/conversations/{initial['id']}/messages", json={
        'message': '14:00 UTC', 'expected_revision': 1})
    assert response.status_code == 409
    stored = client.get(f"/api/conversations/{initial['id']}").json()
    assert stored['revision'] == 2
    assert len(stored['messages']) == 2


@pytest.mark.parametrize('message', ['', '   ', 'x'*4001])
def test_invalid_message_rejected(session, message):
    client, _, _ = session
    assert client.post('/api/conversations', json={'message': message}).status_code == 422


def test_missing_conversation_and_turn_limit(session):
    client, factory, _ = session
    assert client.get('/api/conversations/not-found').status_code == 404
    initial = begin(client)
    with factory() as db:
        db.execute(update(Conversation).where(Conversation.id == initial['id']).values(messages=initial['messages']*30))
        db.commit()
    response = client.post(f"/api/conversations/{initial['id']}/messages", json={
        'message': 'Another turn', 'expected_revision': 1})
    assert response.status_code == 422
