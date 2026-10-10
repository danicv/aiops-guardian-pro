# Forced demo script

A repeatable, ~5 minute demo that *forces* an incident instead of waiting for one.

## Prerequisites
`make local-build local-deploy`, then port-forwards: backend `30800`, frontend `30081`, store `18081`, Grafana `3002`. Ollama running for the chat answers.

## Automated version
```bash
python scripts/capstone_evidence.py demo     # writes docs/evidence/forced-demo-run.md
```

## Manual walk-through
| Step | Action | Expected |
|---|---|---|
| 1 Baseline | Open the store (http://localhost:18081), place an order | Order confirmed; Grafana "Orders" increments |
| 2 Force the fault | `for i in $(seq 40); do curl -s -XPOST 'localhost:18081/api/orders?fail=true&delay_ms=400' -H 'Content-Type: application/json' -d '{"items":[{"sku":"TRAIL-BOTTLE","quantity":1}]}'; done` | HTTP 503; Grafana 5xx and burn rate rise |
| 3 Detect | UI -> Ask Guardian: "Why is checkout-api failing in production?" (live mode) | Threshold exceeded: 5xx rate, error-budget burn, with the PromQL used |
| 4 Honesty check | Read the root cause | "Unconfirmed", confidence 0, `collect_evidence`: metrics alone do not prove a cause |
| 5 Retrieval | Switch to Demo mode, run the OOM scenario | Top precedent `SYN-K8S-001` (memory reduction -> OOMKilled) with matched terms |
| 6 Guardrail | Look at the recommended action | `rollback_deployment` -> `REQUIRE_APPROVAL`, risk HIGH, action not executed |
| 7 Human approval | Approvals page | Card shows hypothesis, metrics, evidence, link to the investigation; Approve/Reject |
| 8 Trace | Open Langfuse (http://localhost:3000) | Full LLM/agent trace of the run |

## Evidence produced by the demo
`docs/evidence/`: `forced-demo-run.md`, `proof-retrieval-tools-memory-adaptation.md`, `safety-enforcement.md`, `prompt-comparison.md`.
