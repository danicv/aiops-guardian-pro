# Forced demo run
_Generated 2026-10-03 11:33:51_

1. Healthy traffic: 5 baseline orders sent to the store.
2. Fault forced: 40 orders with `fail=true&delay_ms=400` -> HTTP codes [503].
3. Waiting 35s for Prometheus to scrape the new counters.

## Investigation result
- status: `needs_review`
- root cause: Threshold exceeded: HTTP 5xx rate, Error-budget burn. Root cause is unconfirmed; deployment, logs, and traces must be correlated before remediation.
- confidence: 0.0
- recommended action: `collect_evidence` -> guardrail `READ_ONLY`
- evaluation: {"passed": false, "reason": "Causal diagnosis has not been validated."}

### Measured metrics
- Request rate: 0.112 req/s (baseline Traffic volume, status healthy)
- HTTP 5xx rate: 100 % (baseline ≤ 0.2 %, status warning)
- p95 latency: 487 ms (baseline ≤ 500 ms, status healthy)
- Error-budget burn: 500 x (baseline ≤ 1 x, status warning)

4. Open the Guardian UI -> Ask Guardian, or Grafana dashboard `guardian-service-health`, to view the same signals.
