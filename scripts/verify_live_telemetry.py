"""Smoke test against observability/compose.yml, using actual HTTP traffic."""
import os
from pathlib import Path
import sys
import time

os.environ.setdefault('PROMETHEUS_URL', 'http://localhost:19090')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
import httpx
from app.live_telemetry import investigate_live

with httpx.Client(timeout=5) as client:
    for _ in range(40):
        client.get('http://localhost:18080/checkout').raise_for_status()
        time.sleep(1)
result = investigate_live({'application': 'checkout-api', 'environment': 'prod', 'namespace': 'default'})
for metric in result['sre_metrics']:
    print(f"{metric['name']}: {metric['value']} ({metric['status']})")
assert all(m['numeric_value'] is not None for m in result['sre_metrics']), result
assert result['sre_metrics'][0]['numeric_value'] > 0
assert result['sre_metrics'][1]['numeric_value'] == 0
assert result['status'] == 'needs_review'
print('Live instrumentation → Prometheus → investigation smoke test passed.')
