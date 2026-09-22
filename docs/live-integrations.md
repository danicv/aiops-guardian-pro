# Live integrations and graphical reporting

Guardian reads your monitoring systems rather than replacing their collectors.
Instrument applications, collect metrics/logs, and connect the existing query
endpoints to Guardian. Every source must identify the same service, environment,
and namespace so findings can be compared meaningfully.

## Working adapters

Prometheus provides request rate, HTTP 5xx percentage, p95 latency, and SLO burn.
Loki provides recent scoped logs when an active log integration is configured.
Other catalog providers are planned adapters and do not establish connections.
Supported metrics must use the names exported by `demo/checkout-api/app.py`;
compatibility with a monitoring API does not automatically map arbitrary metrics.

At `http://localhost:30081/integrations`, choose an available provider, enter its
backend-reachable URL, test the connection, save, then activate it for investigations.
Only one saved integration per provider is active at a time. When no Prometheus
integration is active, the backend uses `PROMETHEUS_URL`. No Loki integration means
logs are not collected. Ordinary chat replies retain their existing snapshot;
refresh telemetry or start a conversation to query a newly selected source.

The local Kubernetes service URLs are:

- Prometheus: `http://guardian-prometheus:9090`
- Loki: `http://guardian-loki:3100`

Authenticated endpoints accept a dedicated backend environment variable reference
for the bearer token, not the token itself. Use the validation format shown in the
Integration Hub. Store actual credentials in a backend Kubernetes Secret, never
in saved configuration JSON or frontend code. TLS verification stays enabled and
authenticated requests do not follow redirects.

## Reports

Open `http://localhost:30081/reports`, select `checkout-api`, `prod`, and
`aiops-guardian`, then choose a 15, 30, or 60 minute window. The page shows four
metric trends, current status, query provenance, and available log evidence.
Missing data produces gaps or unknown states, not invented zeroes or healthy status.
An error-budget burn value is a short-window rate, not remaining monthly budget.

## Reproducible local scenario

The local overlay includes ephemeral Prometheus and Loki stores. It also enables
bounded fault controls on the demo checkout service. These controls are disabled
by default in the application and are not an instruction to inject failures into
real workloads. Keep these forwards running in separate terminals:

```sh
kubectl --context kind-guardian-local -n aiops-guardian port-forward service/checkout-api 18081:8080
kubectl --context kind-guardian-local -n aiops-guardian port-forward service/guardian-loki 18100:3100
```

Run the scenario from the repository root with an environment containing httpx:

```sh
python scripts/run_reporting_scenario.py --publish-demo-logs
```

This sends one request per second during three 60-second phases: baseline,
increased latency with periodic HTTP 503 responses, and normal traffic again.
Loki receives clearly labelled synthetic request observations. It is a local
instrumentation and reporting demonstration, not evidence of an actual release
failure. A production installation needs an application log collector such as an
OpenTelemetry pipeline or a compatible Loki collector; the script is not one.

View Reports during and after the run. Then ask Guardian to investigate the slow
checkout requests, answer its clarifying questions, and refresh the evidence.
The five-minute metric window will still include errors after normal traffic
returns. Do not interpret the start of the recovery phase as verified SLO recovery.

## Extending coverage

Implement each provider against a read-only operation contract; validate real
connectivity, scope and time bounds; normalize evidence with its source and
collection time; add partial-response and unavailable-data tests. Add trace,
Kubernetes event, deployment/change, runbook and incident-history adapters before
claiming cross-source causal diagnosis. Vendor-specific authentication, permissions,
query languages and metric mapping must be implemented and tested per adapter.

Before an organization-wide deployment, add authenticated access and per-team
source permissions, audit integration changes, and define retention/redaction of
logs and model inputs. These local demo settings are not a production security model.

References: [Prometheus query API](https://prometheus.io/docs/prometheus/latest/querying/api/)
and [Loki HTTP API](https://grafana.com/docs/loki/latest/reference/loki-http-api/).
