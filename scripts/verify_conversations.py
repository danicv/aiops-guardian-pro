"""Validate the deployed conversation flow without infrastructure mutations.
Creates one saved local conversation; requires the documented UI/API forwards.
"""
import re
import httpx

UI = 'http://localhost:30081'
API = 'http://localhost:30800'
with httpx.Client(timeout=40) as client:
    page = client.get(f'{UI}/ask')
    page.raise_for_status()
    asset = re.search(r'src="([^"]+\.js)"', page.text).group(1)
    bundle = client.get(UI + asset)
    bundle.raise_for_status()
    assert '/api/conversations' in bundle.text
    before = client.get(f'{API}/api/approvals')
    before.raise_for_status()
    approvals = {a['id'] for a in before.json()}
    response = client.post(f'{API}/api/conversations', json={
        'message': 'Checkout latency increased after a deployment. Help me narrow the cause.',
        'application': 'checkout-api', 'environment': 'prod', 'namespace': 'aiops-guardian', 'telemetry_mode': 'live'})
    response.raise_for_status()
    chat = response.json()
    identity = chat['id']
    assert chat['messages'][-1]['question']
    print('Conversation:', identity)
    print('Assistant mode:', chat['messages'][-1]['assistant_mode'])
    initial_snapshot = chat['result']['snapshot_at']
    for reply in ('It began at 14:00 UTC.', 'We changed the connection pool from 50 to 10.', 'Only checkout requests are affected.'):
        response = client.post(f'{API}/api/conversations/{identity}/messages', json={
            'message': reply, 'expected_revision': chat['revision']})
        response.raise_for_status()
        chat = response.json()
    assert chat['revision'] == 4
    assert len(chat['messages']) == 8
    assert chat['result']['snapshot_at'] == initial_snapshot
    restored = client.get(f'{API}/api/conversations/{identity}')
    restored.raise_for_status()
    assert restored.json() == chat
    stale = client.post(f'{API}/api/conversations/{identity}/messages', json={
        'message': 'Old tab reply', 'expected_revision': 1})
    assert stale.status_code == 409
    refresh = client.post(f'{API}/api/conversations/{identity}/messages', json={
        'message': 'Refresh the current telemetry and reassess.', 'expected_revision': chat['revision'], 'refresh_metrics': True})
    refresh.raise_for_status()
    updated = refresh.json()
    assert updated['result']['snapshot_at'] != initial_snapshot
    assert updated['context']['original_problem'] == chat['context']['original_problem']
    assert len(updated['messages']) == 10
    assert {a['id'] for a in client.get(f'{API}/api/approvals').json()} == approvals
    assert any(c['id'] == identity for c in client.get(f'{API}/api/conversations').json())
    print('Initial clarification, three replies, persistence, conflict protection, and metrics refresh passed.')
    print('No approvals created; infrastructure actions were not invoked.')
