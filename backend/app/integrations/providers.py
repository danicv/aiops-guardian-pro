"""Read-only telemetry adapters. Credentials remain in the backend environment."""
import ipaddress
import json
import math
import os
import re
import time
from urllib.parse import urlsplit

import httpx
from .base import IntegrationProvider

ENV_NAME = re.compile(r'^GUARDIAN_INTEGRATION_[A-Z0-9_]{1,80}_TOKEN$')
MAX_RESPONSE_BYTES = 2_000_000
SAFE_CONFIG_KEYS = {'url', 'bearer_token_env', 'use_for_investigations'}


def reject_credentials(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key != 'bearer_token_env' and any(word in key.lower() for word in
                    ('token', 'password', 'secret', 'authorization', 'credential', 'api_key', 'apikey')):
                raise ValueError('Raw credentials are not accepted. Use a backend bearer_token_env reference.')
            reject_credentials(item)
    elif isinstance(value, list):
        for item in value:
            reject_credentials(item)


def validate_configuration(config):
    if not isinstance(config, dict):
        raise ValueError('Configuration must be an object.')
    reject_credentials(config)
    if set(config) - SAFE_CONFIG_KEYS:
        raise ValueError('Supported configuration fields: url, bearer_token_env, use_for_investigations.')
    url = config.get('url')
    if not isinstance(url, str) or len(url) > 2048 or any(c.isspace() or ord(c) < 32 for c in url) or '\\' in url:
        raise ValueError('Use a valid HTTP or HTTPS base URL without credentials or query parameters.')
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or '').lower().rstrip('.')
        port = parsed.port
        if (parsed.scheme not in ('http', 'https') or not host or parsed.username is not None
                or parsed.password is not None or parsed.query or parsed.fragment or '%' in host):
            raise ValueError()
        if port is not None and not 1 <= port <= 65535:
            raise ValueError()
        if host in {'metadata.google.internal', 'metadata.azure.internal', 'instance-data'} or host.endswith('.metadata.google.internal'):
            raise ValueError()
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            if re.fullmatch(r'[0-9.]+', host) or host.startswith('0x'):
                raise ValueError()
        else:
            address = getattr(address, 'ipv4_mapped', None) or address
            if (address.is_private or address.is_loopback or address.is_link_local
                    or address.is_unspecified or address.is_multicast or address.is_reserved):
                raise ValueError()
    except (ValueError, TypeError):
        raise ValueError('Use an HTTP or HTTPS base URL without credentials, query parameters, or metadata addresses.') from None
    env_name = config.get('bearer_token_env')
    if env_name is not None and (not isinstance(env_name, str) or not ENV_NAME.fullmatch(env_name)):
        raise ValueError('bearer_token_env must use a dedicated GUARDIAN_INTEGRATION_<NAME>_TOKEN environment variable.')
    if 'use_for_investigations' in config and not isinstance(config['use_for_investigations'], bool):
        raise ValueError('use_for_investigations must be a boolean.')
    return {**config, 'url': url.rstrip('/')}


def telemetry_client(config):
    config = validate_configuration(config)
    headers = {}
    if config.get('bearer_token_env'):
        token = os.environ.get(config['bearer_token_env'], '')
        if not token or '\n' in token or '\r' in token:
            raise ValueError('The configured backend credential is unavailable.')
        headers['Authorization'] = f'Bearer {token}'
    return httpx.Client(base_url=config['url'], headers=headers, timeout=5.0,
                        follow_redirects=False, trust_env=False)


def read_json(client, path, params):
    with client.stream('GET', path, params=params) as response:
        response.raise_for_status()
        body = bytearray()
        for chunk in response.iter_bytes():
            body.extend(chunk)
            if len(body) > MAX_RESPONSE_BYTES:
                raise ValueError('Telemetry response exceeded the limit.')
        result = json.loads(body)
    if not isinstance(result, dict) or result.get('status') != 'success' or result.get('warnings'):
        raise ValueError('Telemetry service returned an unsuccessful or partial response.')
    return result['data']


class TelemetryProvider(IntegrationProvider):
    status = 'available'

    def __init__(self, name, category, description, example):
        self.provider_name, self.category, self.description = name, category, description
        self.configuration_example = example

    def capabilities(self):
        return ['query', 'query_range'] if self.provider_name == 'prometheus' else ['query_range']

    def execute(self, operation, params, config):
        if operation not in self.capabilities():
            raise ValueError('Unsupported read-only operation.')
        params = dict(params)
        query = params.get('query')
        if not isinstance(query, str) or not query or len(query) > 8192:
            raise ValueError('A bounded query is required.')
        if operation == 'query_range':
            start, end = float(params['start']), float(params['end'])
            if not all(math.isfinite(v) for v in (start, end)) or end < start or end-start > 3600:
                raise ValueError('Query windows must be at most one hour.')
        if self.provider_name == 'prometheus':
            params = {k: v for k, v in params.items() if k in {'query', 'time', 'start', 'end', 'step'}}
            params['timeout'] = '4s'
            if operation == 'query_range' and (not math.isfinite(float(params.get('step', 0))) or float(params.get('step', 0)) < 15):
                raise ValueError('Range resolution must be at least 15 seconds.')
            path = f'/api/v1/{operation}'
        else:
            params = {k: v for k, v in params.items() if k in {'query', 'start', 'end'}}
            params.update(start=str(int(start*1_000_000_000)), end=str(int(end*1_000_000_000)), limit=50, direction='backward')
            path = '/loki/api/v1/query_range'
        with telemetry_client(config) as client:
            return read_json(client, path, params)

    def test_connection(self, config):
        try:
            now = time.time()
            if self.provider_name == 'prometheus':
                data = self.execute('query', {'query': 'vector(1)', 'time': now}, config)
                if data.get('resultType') != 'vector' or len(data.get('result', [])) != 1:
                    raise ValueError()
                data = self.execute('query_range', {'query': 'vector(1)', 'start': now-30, 'end': now, 'step': 30}, config)
                if data.get('resultType') != 'matrix' or len(data.get('result', [])) != 1:
                    raise ValueError()
            else:
                data = self.execute('query_range', {'query': '{service=~".+"}', 'start': now-60, 'end': now}, config)
                if data.get('resultType') != 'streams' or not isinstance(data.get('result'), list):
                    raise ValueError()
            return {'ok': True, 'provider': self.provider_name, 'message': 'Read-only API connection succeeded. Matching application telemetry is checked during investigations.'}
        except (httpx.HTTPError, ValueError, KeyError, TypeError, OverflowError, AttributeError):
            return {'ok': False, 'provider': self.provider_name, 'message': 'Connection failed. Check the endpoint, backend credential reference, network access, and read permissions.'}


class PlannedProvider(IntegrationProvider):
    status = 'planned'
    configuration_example = {}

    def __init__(self, name, caps, category, description):
        self.provider_name, self._caps = name, caps
        self.category, self.description = category, description

    def test_connection(self, config):
        return {'ok': False, 'provider': self.provider_name, 'message': 'This connector is planned; live access is not implemented.'}

    def capabilities(self):
        return self._caps

    def execute(self, operation, params, config):
        raise NotImplementedError('This connector is planned; live access is not implemented.')


PROVIDERS = {
    'prometheus': TelemetryProvider('prometheus', 'Metrics', 'Live scoped metrics, scrape health, and time-series reports.', {'url': 'http://prometheus:9090'}),
    'loki': TelemetryProvider('loki', 'Logs', 'Read recent logs scoped by service, environment, and namespace.', {'url': 'http://loki:3100'}),
    'github': PlannedProvider('github', ['get_commit', 'get_pull_request', 'get_workflow_run', 'compare_releases'], 'Changes', 'Planned: deployment and source changes.'),
    'azure-devops': PlannedProvider('azure-devops', ['get_pipeline', 'get_build_logs', 'get_test_results', 'get_release'], 'CI/CD', 'Planned: pipeline and release evidence.'),
    'gitlab': PlannedProvider('gitlab', ['get_pipeline', 'get_job_log', 'compare_commits'], 'CI/CD', 'Planned: job failures and commit comparisons.'),
    'servicenow': PlannedProvider('servicenow', ['get_incident'], 'Incidents', 'Planned: incident history and context.'),
    'webhook': PlannedProvider('webhook', [], 'Events', 'Planned: operational event ingestion.'),
}
