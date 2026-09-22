import importlib.util
from pathlib import Path
from fastapi.testclient import TestClient


def test_checkout_exports_requests_latency_and_bounded_routes(monkeypatch):
    path = Path(__file__).resolve().parents[2] / 'demo/checkout-api/app.py'
    spec = importlib.util.spec_from_file_location('checkout_instrumented', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with TestClient(module.app, raise_server_exceptions=False) as client:
        assert client.get('/checkout').status_code == 200
        monkeypatch.setenv('ENABLE_DEMO_FAULTS', 'false')
        assert client.get('/checkout?fail=true').status_code == 403
        monkeypatch.setenv('ENABLE_DEMO_FAULTS', 'true')
        assert client.get('/checkout?fail=true&delay_ms=1').status_code == 503
        assert client.get('/checkout?delay_ms=1001').status_code == 422
        client.get('/missing/unique-id')
        @module.app.get('/failure')
        def failure():
            raise RuntimeError('test')
        assert client.get('/failure').status_code == 500
        metrics = client.get('/metrics')
        assert metrics.status_code == 200
        assert 'http_server_requests_total{' in metrics.text
        assert 'http_server_duration_seconds_bucket{' in metrics.text
        assert 'status="500"' in metrics.text
        assert 'route="unmatched"' in metrics.text
        assert 'unique-id' not in metrics.text
        assert 'route="/metrics"' not in metrics.text
