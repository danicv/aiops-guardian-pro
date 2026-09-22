# Observability

AIOps Guardian observes both ordinary application traffic and the AI control plane.

Recommended spans:

```text
incident.request
agent.orchestrator
agent.pipeline
agent.kubernetes
agent.monitoring
agent.rag
faiss.search
agent.rca
agent.validation
agent.adaptive
mcp.tool_call
guardrail.evaluate
approval.request
notification.send
remediation.execute
verification.execute
deepeval.evaluate
```

## Sidecar topology

```text
Application / Agent / MCP container
          |
      OTLP localhost
          |
OpenTelemetry Collector sidecar
          |
Central OTel Gateway
   |        |       |
Prometheus Loki   Tempo
       \     |     /
          Grafana
```

## Live SRE investigations

Ask Guardian defaults to **Live Prometheus**. The simulator and the explicit
**Simulated demo** option retain sample incidents. Live investigations only read
telemetry: they never manufacture deployment evidence, send approval mail, execute
remediation, or claim that a root cause has been confirmed.

The checkout service now exports `/metrics`: request counters and duration
histograms in seconds, with bounded route templates and service/environment/namespace
labels. Health probes and scrapes are excluded. Exceptions count as HTTP 500.
Run one Uvicorn worker per container (the provided Dockerfile does this).

From the repository root, with your existing `.env` configured:

```sh
docker compose --profile observability up -d --build checkout-api prometheus backend
curl http://localhost:8080/checkout
curl http://localhost:8080/metrics
```

Generate traffic for at least two scrape intervals (15 seconds each); several
minutes gives a more useful five-minute rate:

```sh
for i in $(seq 1 120); do curl -fsS http://localhost:8080/checkout >/dev/null; sleep 1; done
```

Check the checkout-api target at `http://localhost:9090/targets`, then investigate
application `checkout-api`, environment `prod`, namespace `default` in the UI.
Request rate, 5xx percentage, p95 latency, and error-budget burn include their
actual PromQL and evaluation timestamp. Zero traffic makes error ratio/latency
undefined; this displays as unknown, not healthy. HTTP/API failures, partial
responses, non-finite values and missing series also remain unknown.

Backend settings:

- `PROMETHEUS_URL`: reachable Prometheus base URL; Compose sets `http://prometheus:9090`.
- `AVAILABILITY_SLO`: fraction between zero and one, default `0.998`.
- `LATENCY_THRESHOLD_MS`: positive p95 threshold, default `500`.

Burn = observed 5xx fraction / (1 − availability SLO). This is a short-window
indicator, not remaining monthly budget, and does not capture network failures.
Queries aggregate all replicas matching the three scope labels. No recording
rules are required. Metrics alone cannot identify a causal deployment change.

For another application, export `http_server_requests_total` and
`http_server_duration_seconds_bucket` with the same labels, and add its scrape
target in `observability/prometheus/prometheus.yml`. Configure the backend URL to
use an existing Kubernetes Prometheus deployment when running the backend in a
cluster. This Compose installation does not install Kubernetes node exporters,
kube-state-metrics, tracing, or modify external applications.

API callers may set `telemetry_mode` to `live` (default) or `demo` on
`POST /api/investigations`. Live results return `needs_review` or
`insufficient_data`; they never imply successful remediation.

References: [Prometheus query API](https://prometheus.io/docs/prometheus/latest/querying/api/)
and [Python histogram instrumentation](https://prometheus.github.io/client_python/instrumenting/histogram/).

### Standalone local validation (no `.env` required)

```sh
docker compose -p guardian-telemetry -f observability/compose.yml up -d --build
for i in $(seq 1 120); do curl -fsS http://localhost:18080/checkout >/dev/null; sleep 1; done
```

This binds only to loopback: checkout on `18080`, Prometheus on `19090`.
For a backend running on the host, set `PROMETHEUS_URL=http://localhost:19090`.
A backend inside Docker or Kubernetes needs an address reachable from that
container; its `localhost` refers to itself. Inspect targets at
`http://localhost:19090/targets`. Stop this isolated stack with:

```sh
docker compose -p guardian-telemetry -f observability/compose.yml down
```

Live metric families also require fresh raw samples and a fresh `up=1` for every
`job,instance` target observed in the five-minute window. Samples older than 120
seconds or failed targets make that family unknown, even if an old rate is still
calculable. Removed targets remain incomplete until the window expires. Targets
that have never exported scoped metrics require a separate inventory check.
