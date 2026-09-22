import time
from unittest.mock import Mock

import httpx
import pytest
from app.live_telemetry import LATENCY_METRIC, metric_specs, read_metric, read_scrape_health
from app.orchestrator import run_investigation

STATE = {'application': 'checkout-api', 'environment': 'prod', 'namespace': 'default'}


@pytest.fixture(autouse=True)
def no_configured_integrations(monkeypatch):
    from app.repository import repo
    monkeypatch.setattr(repo, 'get_active_integration', lambda provider: None)


def client_for(result, **extra):
    return httpx.Client(base_url='http://prometheus', transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json={'status': 'success', 'data': {'resultType': 'vector', 'result': result}, **extra})))


def target_sample(value='1', instance='checkout:8080'):
    return {'metric': {'job': 'checkout-api', 'instance': instance}, 'value': [time.time(), value]}


def mock_live_prometheus(monkeypatch, request_targets=None, latency_targets=None):
    from app import live_telemetry
    original_client = httpx.Client
    def response(request):
        query = request.url.params['query']
        if 'timestamp(' in query:
            samples = latency_targets if LATENCY_METRIC in query else request_targets
            samples = [target_sample()] if samples is None else samples
        else:
            samples = [{'value': [time.time(), '0']}]
        return httpx.Response(200, json={'status': 'success', 'data': {'resultType': 'vector', 'result': samples}})
    transport = httpx.MockTransport(response)
    monkeypatch.setattr(live_telemetry.httpx, 'Client', lambda **kw: original_client(transport=transport, **kw))


def test_value_and_scope():
    spec = metric_specs({**STATE, 'application': 'api"} or vector(1)'})[1]
    assert 'service="api\\"} or vector(1)"' in spec[1]
    assert 'environment="prod",namespace="default"' in spec[1]
    now = time.time()
    with client_for([{'value': [now, '6.8']}]) as client:
        metric = read_metric(client, spec, now)
    assert metric['numeric_value'] == 6.8
    assert metric['status'] == 'warning'


@pytest.mark.parametrize('result', [[], [{'value': [0, '2']}], [{'value': [time.time(), 'NaN']}], [{'value': [time.time(), '+Inf']}], [{'value': [time.time(), '-1']}], [{'value': [time.time(), '1']}, {'value': [time.time(), '2']}]])
def test_unavailable_never_becomes_healthy(result):
    with client_for(result) as client:
        metric = read_metric(client, metric_specs(STATE)[0], time.time())
    assert metric['status'] == 'unknown'
    assert metric['numeric_value'] is None


def test_timeout():
    client = Mock()
    client.get.side_effect = httpx.ReadTimeout('timeout')
    assert read_metric(client, metric_specs(STATE)[0], time.time())['status'] == 'unknown'


def test_live_flow_has_no_demo_or_side_effects(monkeypatch):
    from app import orchestrator
    mock_live_prometheus(monkeypatch)
    graph = Mock(side_effect=AssertionError('demo must not run'))
    monkeypatch.setattr(orchestrator.graph, 'invoke', graph)
    result = run_investigation({**STATE, 'query': 'Investigate failures'})
    assert result['telemetry_mode'] == 'live'
    assert result['status'] == 'needs_review'
    assert len(result['sre_metrics']) == 4
    assert 'approval_id' not in result
    assert result['confidence_score'] == 0
    assert all(e['source'] == 'prometheus' for e in result['evidence'])


@pytest.mark.parametrize('targets', [
    [],
    [target_sample('0')],
    [target_sample(), target_sample('0', 'failed-replica:8080')],
    [{'value': [time.time(), '1'], 'metric': {}}],
])
def test_failed_or_missing_scrapes_override_fresh_healthy_rates(monkeypatch, targets):
    mock_live_prometheus(monkeypatch, request_targets=targets)
    result = run_investigation({**STATE, 'query': 'Investigate failures'})
    assert result['status'] == 'insufficient_data'
    request_metrics = [m for m in result['sre_metrics'] if m['name'] != 'p95 latency']
    assert all(m['status'] == 'unknown' and m['numeric_value'] is None for m in request_metrics)
    assert [item['signal'] for item in result['evidence']] == ['p95 latency']


def test_missing_histogram_scrapes_do_not_hide_request_metrics(monkeypatch):
    mock_live_prometheus(monkeypatch, latency_targets=[])
    result = run_investigation({**STATE, 'query': 'Investigate failures'})
    assert result['status'] == 'insufficient_data'
    assert result['sre_metrics'][2]['status'] == 'unknown'
    assert len(result['evidence']) == 3


def test_partial_scrape_query_cannot_establish_health():
    with client_for([target_sample()], warnings=['partial response']) as client:
        assert not read_scrape_health(client, STATE, LATENCY_METRIC, time.time())['healthy']


def test_partial_prometheus_result_is_unknown():
    with client_for([{'value': [time.time(), '0']}], warnings=['partial response']) as client:
        assert read_metric(client, metric_specs(STATE)[0], time.time())['status'] == 'unknown'


def test_live_outage_does_not_fabricate_evidence(monkeypatch):
    from app import live_telemetry
    original_client = httpx.Client
    transport = httpx.MockTransport(lambda request: httpx.Response(503))
    monkeypatch.setattr(live_telemetry.httpx, 'Client', lambda **kw: original_client(transport=transport, **kw))
    result = run_investigation({**STATE, 'query': 'Investigate failures'})
    assert result['status'] == 'insufficient_data'
    assert result['evidence'] == []
    assert all(m['status'] == 'unknown' for m in result['sre_metrics'])
    assert 'approval_id' not in result
