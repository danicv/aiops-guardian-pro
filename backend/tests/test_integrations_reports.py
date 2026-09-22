import json
import time

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import repository
from app.api.routes import router
from app.db import Base
from app.integrations.providers import PROVIDERS, validate_configuration
from app.live_telemetry import investigate_live, resolve_prometheus_source
from app.models import Approval, Integration
from app.api import routes
from app.repository import repo
from app.telemetry_reports import telemetry_report

STATE = {'application': 'checkout-api', 'environment': 'prod', 'namespace': 'aiops-guardian'}


@pytest.fixture
def db(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(repository, 'SessionLocal', factory)
    yield factory
    engine.dispose()


@pytest.fixture
def api(db):
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        yield client


def mock_http(monkeypatch, handler):
    original = httpx.Client
    monkeypatch.setattr(httpx, 'Client', lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))


def test_approval_decision_is_single_use(db):
    with db() as session:
        session.add(Approval(id='APR-TEST', investigation_id='INV-TEST', action='rollback_deployment', environment='prod', risk='HIGH'))
        session.commit()

    first = repo.decide_approval('APR-TEST', 'approved', 'sre@example.com', 'approved')
    assert first['status'] == 'approved'
    with pytest.raises(ValueError, match='already been decided'):
        repo.decide_approval('APR-TEST', 'rejected', 'other@example.com', 'rejected')


def test_replayed_approval_returns_conflict(api, db, monkeypatch):
    with db() as session:
        session.add(Approval(id='APR-API', investigation_id='INV-API', action='review_release', environment='prod', risk='HIGH'))
        session.commit()
    monkeypatch.setattr(routes, 'execute_approved_action', lambda approval: {'status': 'executed'})
    payload = {'decided_by': 'sre@example.com', 'comment': 'approved'}
    assert api.post('/api/approvals/APR-API/approve', json=payload).status_code == 200
    response = api.post('/api/approvals/APR-API/approve', json=payload)
    assert response.status_code == 409


def prometheus_response(request, *, healthy=True, gap=False, empty=False):
    query = request.url.params['query']
    if request.url.path.endswith('query_range'):
        start, end, step = [int(float(request.url.params[key])) for key in ('start', 'end', 'step')]
        samples = [[stamp, 'NaN' if gap and stamp == start+step else '2'] for stamp in range(start, end+1, step)]
        if gap:
            samples = samples[1:]
        result_type, result = 'matrix', [] if empty else [{'metric': {}, 'values': samples}]
    elif 'timestamp(' in query:
        result_type, result = 'vector', [{'metric': {'job': 'checkout-api', 'instance': 'checkout:8080'}, 'value': [time.time(), '1' if healthy else '0']}]
    else:
        result_type, result = 'vector', [{'metric': {}, 'value': [time.time(), '1']}]
    return httpx.Response(200, json={'status': 'success', 'data': {'resultType': result_type, 'result': result}})


@pytest.mark.parametrize('url', ['ftp://example.org', 'http://user:password@example.org', 'http://example.org?token=sensitive',
                                  'http://127.0.0.1:9090', 'http://10.0.0.8:9090', 'http://192.168.1.8:9090',
                                  'http://169.254.169.254', 'http://[fe80::1]', 'http://[::ffff:169.254.169.254]',
                                  'http://metadata.google.internal', 'http://2852039166', 'http://0xa9fea9fe',
                                  'http://example.org/#token', 'http://example.org:99999', 'http://exa\\mple.org'])
def test_rejects_unsafe_endpoints(url):
    with pytest.raises(ValueError):
        validate_configuration({'url': url})


@pytest.mark.parametrize('config', [{'url': 'http://prometheus:9090', 'token': 'sensitive'},
                                    {'url': 'http://prometheus:9090', 'extra': {'password': 'sensitive'}},
                                    {'url': 'http://prometheus:9090', 'extra': [{'Authorization': 'sensitive'}]},
                                    {'url': 'http://prometheus:9090', 'bearer_token_env': 'bad name'},
                                    {'url': 'http://prometheus:9090', 'bearer_token_env': 'OPENAI_API_KEY'},
                                    {'url': 'http://prometheus:9090', 'bearer_token_env': 'DATABASE_PASSWORD'}])
def test_raw_credentials_rejected_recursively(api, config):
    response = api.post('/api/integrations', json={'provider': 'prometheus', 'name': 'Team source', 'configuration': config})
    assert response.status_code == 400
    assert 'sensitive' not in response.text
    assert api.get('/api/integrations').json() == []


def test_catalog_marks_only_real_connectors_available(api):
    catalog = api.get('/api/integrations/providers').json()
    assert {p['provider'] for p in catalog if p['status'] == 'available'} == {'prometheus', 'loki'}
    assert all('category' in p and 'configuration_example' in p for p in catalog)
    response = api.post('/api/integrations/test', json={'provider': 'github', 'name': 'GitHub', 'configuration': {'repo': 'org/repo'}})
    assert response.json()['ok'] is False
    assert api.post('/api/integrations', json={'provider': 'github', 'name': 'GitHub'}).status_code == 400
    with pytest.raises(NotImplementedError):
        PROVIDERS['github'].execute('get_commit', {}, {})


def test_prometheus_test_queries_both_apis_and_resolves_env_secret(monkeypatch):
    monkeypatch.setenv('GUARDIAN_INTEGRATION_PROMETHEUS_TOKEN', 'very-private-token')
    paths = []
    def handle(request):
        paths.append(request.url.path)
        assert request.headers['Authorization'] == 'Bearer very-private-token'
        assert 'very-private-token' not in str(request.url)
        return prometheus_response(request)
    mock_http(monkeypatch, handle)
    result = PROVIDERS['prometheus'].test_connection({'url': 'http://metrics.internal:9090', 'bearer_token_env': 'GUARDIAN_INTEGRATION_PROMETHEUS_TOKEN'})
    assert result['ok'] is True
    assert paths == ['/api/v1/query', '/api/v1/query_range']
    assert 'very-private-token' not in json.dumps(result)


def test_connection_failure_and_redirect_never_echo_backend_response(monkeypatch):
    requests = []
    def handle(request):
        requests.append(request)
        return httpx.Response(302, headers={'Location': 'http://169.254.169.254/?secret=private'}, text='private-secret')
    mock_http(monkeypatch, handle)
    result = PROVIDERS['prometheus'].test_connection({'url': 'http://metrics.internal'})
    assert result['ok'] is False
    assert 'private' not in json.dumps(result)
    assert len(requests) == 1


def test_missing_environment_secret_is_sanitized(monkeypatch):
    monkeypatch.delenv('GUARDIAN_INTEGRATION_MISSING_TOKEN', raising=False)
    mock_http(monkeypatch, lambda request: pytest.fail('must not send a request without configured auth'))
    result = PROVIDERS['loki'].test_connection({'url': 'http://logs.internal', 'bearer_token_env': 'GUARDIAN_INTEGRATION_MISSING_TOKEN'})
    assert result['ok'] is False
    assert 'GUARDIAN_INTEGRATION_MISSING_TOKEN' not in json.dumps(result)


def test_save_activate_switch_and_disabled_preserve_previous_selection(api):
    def add(name, enabled=True):
        return api.post('/api/integrations', json={'provider': 'prometheus', 'name': name, 'enabled': enabled,
                        'configuration': {'url': f'http://{name}:9090', 'bearer_token_env': 'GUARDIAN_INTEGRATION_PROMETHEUS_TOKEN', 'use_for_investigations': True}}).json()['id']
    first, second, disabled = add('first'), add('second'), add('disabled', False)
    assert all(not x['configuration']['use_for_investigations'] for x in api.get('/api/integrations').json())
    assert api.post(f'/api/integrations/{first}/activate').status_code == 200
    assert api.post(f'/api/integrations/{second}/activate').status_code == 200
    assert api.post(f'/api/integrations/{disabled}/activate').status_code == 400
    assert api.post('/api/integrations/missing/activate').status_code == 404
    selected = [x for x in api.get('/api/integrations').json() if x['configuration']['use_for_investigations']]
    assert [x['id'] for x in selected] == [second]
    assert selected[0]['configuration']['bearer_token_env'] == 'GUARDIAN_INTEGRATION_PROMETHEUS_TOKEN'
    source, config = resolve_prometheus_source()
    assert source['integration_id'] == second and config['url'] == 'http://second:9090'


def test_legacy_config_is_not_exposed(api, db):
    with db() as session:
        session.add(Integration(id='legacy', provider='prometheus', name='Legacy', configuration={'url': 'http://user:private@host', 'nested': {'secret': 'private'}}))
        session.commit()
    assert api.get('/api/integrations').json()[0]['configuration'] == {}
    response = api.post('/api/integrations/legacy/activate')
    assert response.status_code == 400 and 'private' not in response.text


def test_report_scopes_queries_retains_gaps_and_snapshot(api, monkeypatch):
    seen = []
    def handle(request):
        seen.append(request)
        return prometheus_response(request, gap=True)
    mock_http(monkeypatch, handle)
    response = api.get('/api/reports/telemetry', params={**STATE, 'window_minutes': 15})
    assert response.status_code == 200
    body = response.json()
    assert body['scope'] == STATE and body['window_minutes'] == 15
    assert len(body['series']) == len(body['summary']) == 4
    assert all(s['status'] == 'partial' for s in body['series'])
    assert body['series'][0]['points'][0]['value'] is None
    assert body['series'][0]['points'][1]['value'] is None
    assert body['series'][0]['points'][2]['value'] == 2
    assert body['source_errors']
    assert body['log_entries'] == []
    assert all('service="checkout-api",environment="prod",namespace="aiops-guardian"' in req.url.params['query'] for req in seen)
    assert body['snapshot']['guardrail']['decision'] == 'READ_ONLY'


def test_report_health_gate_withholds_healthy_looking_trends(db, monkeypatch):
    requests = []
    def handle(request):
        requests.append(request)
        return prometheus_response(request, healthy=False)
    mock_http(monkeypatch, handle)
    body = telemetry_report(STATE)
    assert all(s['status'] == 'unknown' and all(p['value'] is None for p in s['points']) for s in body['series'])
    assert not any(req.url.path.endswith('query_range') for req in requests)
    assert body['snapshot']['evidence'] == []


def test_report_missing_ranges_remain_unknown(db, monkeypatch):
    mock_http(monkeypatch, lambda request: prometheus_response(request, empty=True))
    body = telemetry_report(STATE, 60)
    assert all(s['status'] == 'unknown' for s in body['series'])
    assert all(len(s['points']) == 61 for s in body['series'])
    assert 'NaN' not in json.dumps(body, allow_nan=False)


def test_report_rejects_unbounded_windows_before_queries(api, monkeypatch):
    mock_http(monkeypatch, lambda request: pytest.fail('no external request expected'))
    assert api.get('/api/reports/telemetry', params={'window_minutes': 999}).status_code == 422
    assert api.get('/api/reports/telemetry', params={'application': 'x'*129}).status_code == 422


def test_active_prometheus_used_by_live_investigation(db, monkeypatch):
    integration_id = repo.add_integration('prometheus', 'Selected metrics', {'url': 'http://selected.metrics:9090'}, True)
    repo.activate_integration(integration_id)
    def handle(request):
        assert request.url.host == 'selected.metrics'
        return prometheus_response(request)
    mock_http(monkeypatch, handle)
    result = investigate_live(STATE)
    assert result['telemetry_source']['integration_id'] == integration_id
    assert result['sre_metrics'][0]['numeric_value'] == 1


def test_loki_scoped_bounded_logs_enter_evidence(db, monkeypatch):
    integration_id = repo.add_integration('loki', 'Service logs', {'url': 'http://logs.internal'}, True)
    repo.activate_integration(integration_id)
    def handle(request):
        if request.url.host != 'logs.internal':
            return prometheus_response(request)
        assert request.url.path == '/loki/api/v1/query_range'
        assert request.url.params['query'] == '{service="checkout-api",environment="prod",namespace="aiops-guardian"}'
        assert request.url.params['limit'] == '50'
        assert int(request.url.params['end'])-int(request.url.params['start']) <= 901*10**9
        return httpx.Response(200, json={'status': 'success', 'data': {'resultType': 'streams', 'result': [
            {'stream': {'service': 'checkout-api', 'environment': 'prod', 'namespace': 'aiops-guardian', 'level': 'error'},
             'values': [[str(int((time.time()-1)*10**9)), 'Upstream timeout']]}]}})
    mock_http(monkeypatch, handle)
    result = investigate_live(STATE)
    assert result['log_entries'][0]['line'] == 'Upstream timeout'
    assert any(e['source'] == 'loki' for e in result['evidence'])
    assert result['confidence_score'] == 0
    assert 'approval_id' not in result


def test_loki_failure_is_explicit_and_metrics_remain_available(db, monkeypatch):
    integration_id = repo.add_integration('loki', 'Logs', {'url': 'http://logs.internal'}, True)
    repo.activate_integration(integration_id)
    mock_http(monkeypatch, lambda request: httpx.Response(503, text='sensitive backend error')
              if request.url.host == 'logs.internal' else prometheus_response(request))
    result = investigate_live(STATE)
    assert result['log_entries'] == [] and result['source_errors']
    assert all(metric['numeric_value'] is not None for metric in result['sre_metrics'])
    assert 'sensitive' not in json.dumps(result)
