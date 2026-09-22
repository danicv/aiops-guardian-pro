"""Read-only, scoped Prometheus investigations. Never substitute simulated evidence."""
import json
import math
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import httpx
from .config import settings
from .integrations.providers import PROVIDERS, read_json, telemetry_client
from .repository import repo

MAX_SCRAPE_AGE = 120
REQUEST_METRIC = 'http_server_requests_total'
LATENCY_METRIC = 'http_server_duration_seconds_bucket'


def scope_labels(state):
    return ','.join(f'{key}={json.dumps(state[value])}' for key, value in
                    [('service', 'application'), ('environment', 'environment'), ('namespace', 'namespace')])


def metric_specs(state):
    labels = scope_labels(state)
    total = f'sum(rate(http_server_requests_total{{{labels}}}[5m]))'
    errors = f'(sum(rate(http_server_requests_total{{{labels},status=~"5.."}}[5m])) or (0 * {total}))'
    ratio = f'({errors} / {total})'
    return [
        ('Request rate', total, 'req/s', None),
        ('HTTP 5xx rate', f'100 * {ratio}', '%', (1-settings.availability_slo)*100),
        ('p95 latency', f'histogram_quantile(0.95, sum by (le) (rate(http_server_duration_seconds_bucket{{{labels}}}[5m]))) * 1000', 'ms', settings.latency_threshold_ms),
        ('Error-budget burn', f'{ratio} / {1-settings.availability_slo!r}', 'x', 1),
    ]


def scrape_health_query(state, metric_name):
    series = f'{metric_name}{{{scope_labels(state)}}}'
    # Keep failed/disappeared targets in the result while their old samples can
    # still contribute to a five-minute rate. Instant-query result timestamps
    # are evaluation times, so freshness must use timestamp(raw_series).
    targets = f'count by (job, instance) (count_over_time({series}[5m]))'
    fresh_series = f'(min by (job, instance) (timestamp({series})) > bool (time() - {MAX_SCRAPE_AGE}))'
    target_up = '(min by (job, instance) (up) == bool 1)'
    fresh_up = f'(min by (job, instance) (timestamp(up)) > bool (time() - {MAX_SCRAPE_AGE}))'
    return (f'({fresh_series} * on (job, instance) {target_up} '
            f'* on (job, instance) {fresh_up}) '
            f'or on (job, instance) (0 * {targets})')


def query_vector(client, query, now):
    data = read_json(client, '/api/v1/query', {'query': query, 'time': now, 'timeout': '4s'})
    if data['resultType'] != 'vector':
        raise ValueError('Expected a Prometheus vector')
    return data['result']


def read_scrape_health(client, state, metric_name, now):
    query = scrape_health_query(state, metric_name)
    result = {'query': query, 'healthy': False, 'observed_targets': 0}
    try:
        targets = query_vector(client, query, now)
        result['observed_targets'] = len(targets)
        result['healthy'] = bool(targets) and all(
            target['metric'].get('job') and target['metric'].get('instance')
            and float(target['value'][1]) == 1
            and abs(now - float(target['value'][0])) <= MAX_SCRAPE_AGE
            for target in targets)
    except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError):
        pass
    return result


def unknown_metric(spec):
    name, query, unit, threshold = spec
    return dict(name=name, query=query, unit=unit, value='Unavailable', numeric_value=None,
                  baseline=f'≤ {threshold:g} {unit}' if threshold is not None else 'Traffic volume',
                  status='unknown', source='prometheus', window='5m', observed_at=None)


def read_metric(client, spec, now):
    name, query, unit, threshold = spec
    metric = unknown_metric(spec)
    try:
        vector = query_vector(client, query, now)
        if len(vector) != 1:
            raise ValueError('No unique series; check scrape targets, labels, and recent traffic')
        stamp, raw = vector[0]['value']
        value = float(raw)
        if not math.isfinite(value) or value < 0 or abs(now-float(stamp)) > MAX_SCRAPE_AGE:
            raise ValueError('Missing, stale, or non-finite sample; generate traffic and check scrapes')
        metric.update(value=f'{value:.3g} {unit}', numeric_value=value,
                      status='warning' if threshold is not None and value > threshold else 'healthy',
                      observed_at=datetime.fromtimestamp(float(stamp), timezone.utc).isoformat())
    except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError):
        metric['error'] = 'Telemetry unavailable. Check Prometheus connectivity, scrape health, metric labels, and traffic.'
    return metric


def resolve_prometheus_source():
    active = repo.get_active_integration('prometheus')
    if active:
        return {'provider': 'prometheus', 'name': active['name'], 'integration_id': active['id']}, active['configuration']
    return {'provider': 'prometheus', 'name': 'Backend default Prometheus'}, {'url': settings.prometheus_url}


def read_scoped_logs(state, now):
    active = repo.get_active_integration('loki')
    if not active:
        return [], []
    entries = []
    query = '{' + scope_labels(state) + '}'
    try:
        data = PROVIDERS['loki'].execute('query_range', {'query': query, 'start': now-900, 'end': now}, active['configuration'])
        if data['resultType'] != 'streams' or not isinstance(data['result'], list):
            raise ValueError()
        for stream in data['result'][:50]:
            labels = stream['stream']
            if any(labels.get(label) != state[key] for label, key in
                   [('service', 'application'), ('environment', 'environment'), ('namespace', 'namespace')]):
                raise ValueError()
            for stamp, line, *_ in stream['values'][:50]:
                stamp = int(stamp)/1_000_000_000
                if not now-900 <= stamp <= now or not isinstance(line, str):
                    continue
                entries.append({'timestamp': datetime.fromtimestamp(stamp, timezone.utc).isoformat(),
                                'line': line[:2000], 'labels': {k: str(labels[k])[:256] for k in
                                ('service', 'environment', 'namespace', 'level', 'severity', 'trace_id') if k in labels}})
        return sorted(entries, key=lambda item: item['timestamp'], reverse=True)[:50], []
    except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError, OverflowError):
        return [], ['Loki logs unavailable. Check connection, read permissions, and service/environment/namespace labels.']


def investigate_live(state, resolved_source=None):
    now = time.time()
    source, config = resolved_source or resolve_prometheus_source()
    try:
        with telemetry_client(config) as client:
            with ThreadPoolExecutor(max_workers=6) as pool:
                metric_jobs = [pool.submit(read_metric, client, spec, now) for spec in metric_specs(state)]
                health_jobs = {name: pool.submit(read_scrape_health, client, state, name, now)
                               for name in (REQUEST_METRIC, LATENCY_METRIC)}
                metrics = [job.result() for job in metric_jobs]
                health = {name: job.result() for name, job in health_jobs.items()}
    except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError):
        metrics = [unknown_metric(spec) for spec in metric_specs(state)]
        health = {name: {'query': scrape_health_query(state, name), 'healthy': False, 'observed_targets': 0}
                  for name in (REQUEST_METRIC, LATENCY_METRIC)}
    for metric in metrics:
        scrape = health[LATENCY_METRIC if metric['name'] == 'p95 latency' else REQUEST_METRIC]
        metric['scrape_health'] = scrape
        if not scrape['healthy']:
            metric.update(value='Unavailable', numeric_value=None, status='unknown', observed_at=None,
                          error='Scrape health is unknown or incomplete. Every recently observed target must be UP with fresh metric samples; check Prometheus targets and instrumentation.')
    available = [m for m in metrics if m['numeric_value'] is not None]
    unhealthy = [m['name'] for m in available if m['status'] == 'warning']
    missing = len(available) != len(metrics)
    log_entries, source_errors = read_scoped_logs(state, now)
    if missing:
        source_errors.insert(0, 'Some Prometheus metrics are unavailable or have incomplete scrape health. Check target health, labels, and recent traffic.')
    summary = ('Threshold exceeded: ' + ', '.join(unhealthy) + '.' if unhealthy else
               'No configured threshold exceeded in available metrics.')
    if not available:
        summary = 'No live telemetry available for the selected service, environment, and namespace.'
    summary += ' Root cause is unconfirmed; deployment, logs, and traces must be correlated before remediation.'
    steps = [
        {'step': 'Collect', 'instruction': 'Run the displayed PromQL checks. Verify the matching target is UP and has at least two scrapes and application traffic.', 'owner': 'on-call SRE'},
        {'step': 'Analyze', 'instruction': 'Correlate the measured error and latency window with deployment timestamps, error logs, and failing traces. Inspect pod events and resource limits before proposing a rollback.', 'owner': 'service owner'},
        {'step': 'Verify', 'instruction': f'After an approved fix, observe at least 15 minutes with 5xx below {(1-settings.availability_slo)*100:g}%, p95 below {settings.latency_threshold_ms:g} ms, and burn below 1x. Missing telemetry is not recovery.', 'owner': 'on-call SRE'},
    ]
    return dict(sre_metrics=metrics, root_cause=summary, confidence_score=0.0,
                telemetry_source=source, log_entries=log_entries, source_errors=source_errors,
                telemetry_notice=f'Live Prometheus queries · 5-minute window · availability SLO {settings.availability_slo:.3%}. Missing or unhealthy scrapes remain unknown. Scrape checks cover targets observed within this window. Burn uses 5xx only; it does not measure network failures.',
                recommended_action='collect_evidence', recommended_target=state['application'],
                status='insufficient_data' if missing else 'needs_review',
                guardrail={'decision': 'READ_ONLY', 'reason': 'Telemetry alone does not establish a causal remediation.', 'approval_required': False},
                action_plan=steps,
                instrumentation=[{'name': 'Request metrics', 'instruction': 'The checkout-api exports counters and duration histograms at /metrics. Deploy the provided Compose observability profile and verify the checkout-api scrape target.', 'example': 'docker compose --profile observability up -d --build checkout-api prometheus backend'},
                                 {'name': 'Other services', 'instruction': 'Export the same metric names with service, environment, namespace, route, method and status labels. Use route templates, never request IDs or raw URLs. Add each target to prometheus.yml.', 'example': 'observability/README.md'}],
                evidence=[{'source': 'prometheus', 'signal': m['name'], 'value': m['numeric_value'], 'query': m['query'], 'observed_at': m['observed_at']} for m in available]
                         + [{'source': 'loki', 'signal': 'Scoped log entry', 'value': entry['line'], 'observed_at': entry['timestamp']} for entry in log_entries],
                agent_trace=[{'agent': 'live-monitoring', 'summary': summary, 'data': {'available_metrics': len(available)}}],
                evaluation={'passed': False, 'reason': 'Causal diagnosis has not been validated.'})
