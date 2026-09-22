"""Create bounded synthetic traffic against the LOCAL demo checkout only.
No deployment changes, real incidents, or remediation are performed.
Requires its port forward on 18081 and ENABLE_DEMO_FAULTS=true on the demo app.
"""
import argparse
import json
import time
import httpx

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--phase-seconds', type=int, default=60, choices=range(20, 121), metavar='20..120')
parser.add_argument('--publish-demo-logs', action='store_true', help='Send synthetic request observations to local Loki port 18100')
args = parser.parse_args()
with httpx.Client(timeout=5) as client:
    for phase in ('baseline', 'degraded', 'recovery'):
        print(f'{phase}: generating synthetic local traffic for {args.phase_seconds} seconds', flush=True)
        until = time.monotonic() + args.phase_seconds
        count = 0
        while time.monotonic() < until:
            started = time.monotonic()
            params = {'delay_ms': 650, 'fail': 'true' if count % 4 == 0 else 'false'} if phase == 'degraded' else {}
            response = client.get('http://localhost:18081/checkout', params=params)
            expected = 503 if params.get('fail') == 'true' else 200
            if response.status_code != expected:
                raise RuntimeError(f'Expected demo HTTP {expected}, received {response.status_code}; check ENABLE_DEMO_FAULTS and the port forward.')
            if args.publish_demo_logs and (response.status_code >= 500 or count % 5 == 0):
                line = json.dumps({'source': 'local-synthetic-traffic', 'phase': phase, 'status': response.status_code,
                                   'duration_ms': round((time.monotonic()-started)*1000, 1), 'path': '/checkout'})
                client.post('http://localhost:18100/loki/api/v1/push', json={'streams': [{
                    'stream': {'service': 'checkout-api', 'environment': 'prod', 'namespace': 'aiops-guardian', 'origin': 'local-demo'},
                    'values': [[str(time.time_ns()), line]]}]}).raise_for_status()
            count += 1
            time.sleep(max(0, 1-(time.monotonic()-started)))
        print(f'{phase}: {count} requests completed', flush=True)
print('Open /reports for the last 15 minutes. Five-minute rates retain degradation after traffic recovers; do not claim immediate SLO recovery.', flush=True)
