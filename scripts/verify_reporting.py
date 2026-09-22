"""Validate local connectors/reports and save chart evidence for the Word use case.
Run after run_reporting_scenario.py --publish-demo-logs. Uses local demo endpoints.
"""
import json
from pathlib import Path
import httpx

with httpx.Client(base_url='http://localhost:30800', timeout=40) as client:
    catalog = client.get('/api/integrations/providers')
    catalog.raise_for_status()
    available = {p['provider'] for p in catalog.json() if p.get('status') == 'available'}
    assert {'prometheus', 'loki'} <= available
    for provider, url in [('prometheus', 'http://guardian-prometheus:9090'), ('loki', 'http://guardian-loki:3100')]:
        payload = {'provider': provider, 'name': f'Local {provider} reporting demo', 'configuration': {'url': url}, 'enabled': True}
        test = client.post('/api/integrations/test', json=payload)
        test.raise_for_status()
        assert test.json()['ok'], test.json()
        stored = client.get('/api/integrations')
        stored.raise_for_status()
        existing = next((i for i in stored.json() if i['name'] == payload['name']), None)
        if existing:
            integration_id = existing['id']
        else:
            saved = client.post('/api/integrations', json=payload)
            saved.raise_for_status()
            integration_id = saved.json()['id']
        activated = client.post(f'/api/integrations/{integration_id}/activate')
        activated.raise_for_status()
        print(f'{provider}: connectivity and activation passed')
    response = client.get('/api/reports/telemetry', params={'application':'checkout-api','environment':'prod','namespace':'aiops-guardian','window_minutes':15})
    response.raise_for_status()
    report = response.json()
    assert len(report['series']) == 4
    assert any(p['value'] is not None for series in report['series'] for p in series['points'])
    assert report['log_entries'], report.get('source_errors')
    assert any('local-synthetic-traffic' in entry['line'] for entry in report['log_entries'])
    path = Path('docs/deliverables/reporting-evidence.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2))
    for series in report['series']:
        observed = [p['value'] for p in series['points'] if p['value'] is not None]
        print(series['name'], 'points=', len(observed), 'peak=', max(observed) if observed else 'unknown', series['unit'])
    print('Scoped logs:', len(report['log_entries']))
    print('Report evidence saved:', path)
    missing = client.get('/api/reports/telemetry', params={'application':'checkout-api','environment':'prod','namespace':'absent-demo-namespace','window_minutes':15})
    missing.raise_for_status()
    assert all(m['status']=='unknown' for m in missing.json()['summary'])
    assert not missing.json()['log_entries']
    invalid = client.get('/api/reports/telemetry', params={'window_minutes':100000})
    assert invalid.status_code == 422
    print('Live report, log correlation, absent-scope and query-bound checks passed.')
