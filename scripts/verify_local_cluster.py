"""Validate the local deployment through the same URLs used by the browser.
Requires frontend/backend/checkout port forwards documented in k8s/README.md.
Creates two live, read-only investigations in the local database.
"""
import re
import time
import httpx

UI = 'http://localhost:30081'
API = 'http://localhost:30800'
with httpx.Client(timeout=30) as client:
    page = client.get(f'{UI}/ask')
    page.raise_for_status()
    asset = re.search(r'src="([^"]+\.js)"', page.text).group(1)
    bundle = client.get(UI + asset)
    bundle.raise_for_status()
    assert 'Live Prometheus' in bundle.text
    assert API in bundle.text
    preflight = client.options(f'{API}/api/investigations', headers={
        'Origin': UI, 'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type'})
    preflight.raise_for_status()
    assert preflight.headers['access-control-allow-origin'] == UI
    for _ in range(35):
        client.get('http://localhost:18081/checkout').raise_for_status()
        time.sleep(1)
    payload = {'query': 'Check live checkout service health', 'application': 'checkout-api',
               'environment': 'prod', 'namespace': 'aiops-guardian', 'telemetry_mode': 'live'}
    response = client.post(f'{API}/api/investigations', json=payload, headers={'Origin': UI})
    response.raise_for_status()
    body = response.json()
    result = body['result']
    assert result['telemetry_mode'] == 'live'
    assert result['status'] == 'needs_review', result
    assert 'approval_id' not in result
    assert all(m['numeric_value'] is not None and m['scrape_health']['healthy'] for m in result['sre_metrics']), result
    assert result['sre_metrics'][0]['numeric_value'] > 0
    print('Live investigation:', body['investigation_id'])
    for metric in result['sre_metrics']:
        print(f"{metric['name']}: {metric['value']} ({metric['status']})")
    stored = client.get(f"{API}/api/investigations/{body['investigation_id']}")
    stored.raise_for_status()
    missing = client.post(f'{API}/api/investigations', json={**payload, 'namespace': 'missing-validation-namespace'})
    missing.raise_for_status()
    assert missing.json()['result']['status'] == 'insufficient_data'
    assert missing.json()['result']['evidence'] == []
print('Page bundle, CORS, real metrics, persistence, and missing-data checks passed.')
