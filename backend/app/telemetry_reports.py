"""Bounded live time series for reporting; absent samples remain explicit gaps."""
import math
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import httpx
from .integrations.providers import read_json, telemetry_client
from .live_telemetry import investigate_live, metric_specs, resolve_prometheus_source


def read_series(client, spec, metric, start, end, step):
    name, query, unit, _ = spec
    timestamps = list(range(start, end+1, step))
    series = {'name': name, 'unit': unit, 'status': 'unknown',
              'points': [{'timestamp': stamp, 'value': None} for stamp in timestamps]}
    # Existing scrape-health gates also protect graphs from apparently healthy stale rates.
    if not metric.get('scrape_health', {}).get('healthy'):
        return series, f'{name}: current scrape health is incomplete; trend withheld.'
    try:
        data = read_json(client, '/api/v1/query_range',
                         {'query': query, 'start': start, 'end': end, 'step': step, 'timeout': '4s'})
        if data['resultType'] != 'matrix' or len(data['result']) != 1:
            raise ValueError()
        values = data['result'][0]['values']
        if len(values) > len(timestamps):
            raise ValueError()
        samples = {}
        for stamp, raw in values:
            stamp, value = float(stamp), float(raw)
            if not math.isfinite(stamp) or stamp not in timestamps or stamp in samples:
                raise ValueError()
            samples[stamp] = value if math.isfinite(value) and value >= 0 else None
        series['points'] = [{'timestamp': stamp, 'value': samples.get(stamp)} for stamp in timestamps]
        present = [point for point in series['points'] if point['value'] is not None]
        series['status'] = ('available' if len(present) == len(timestamps) else 'partial') if present else 'unknown'
        error = None if series['status'] == 'available' else f'{name}: some time samples are unavailable; chart gaps are unknown.'
        return series, error
    except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError):
        return series, f'{name}: time-series query unavailable. Check Prometheus access and metric labels.'


def telemetry_report(state, window_minutes=30):
    if window_minutes not in (15, 30, 60):
        raise ValueError('Report window must be 15, 30, or 60 minutes.')
    resolved_source = resolve_prometheus_source()
    snapshot = investigate_live(state, resolved_source=resolved_source)
    source, config = resolved_source
    step = 60 if window_minutes == 60 else 30
    end = int(time.time())//step*step
    start = end-window_minutes*60
    errors = list(snapshot.get('source_errors', []))
    try:
        with telemetry_client(config) as client, ThreadPoolExecutor(max_workers=4) as pool:
            jobs = [pool.submit(read_series, client, spec, metric, start, end, step)
                    for spec, metric in zip(metric_specs(state), snapshot['sre_metrics'])]
            outcomes = [job.result() for job in jobs]
    except (httpx.HTTPError, ValueError, TypeError):
        outcomes = [(dict(name=spec[0], unit=spec[2], status='unknown',
                         points=[{'timestamp': stamp, 'value': None} for stamp in range(start, end+1, step)]),
                     'Prometheus connection is unavailable. Check endpoint and backend credentials.') for spec in metric_specs(state)]
    for _, error in outcomes:
        if error and error not in errors:
            errors.append(error)
    return {'scope': {key: state[key] for key in ('application', 'environment', 'namespace')},
            'window_minutes': window_minutes, 'generated_at': datetime.now(timezone.utc).isoformat(),
            'source': source, 'summary': snapshot['sre_metrics'], 'series': [item for item, _ in outcomes],
            'log_entries': snapshot.get('log_entries', []), 'source_errors': errors, 'snapshot': snapshot}
