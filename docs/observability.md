# AI and platform observability

Monitor both ordinary application health and the agentic control plane.

## Platform metrics
- API request count/latency/errors
- pod health and saturation
- database connections/latency
- notification delivery

## Agentic metrics
- model latency/failures/token usage
- agent selection and routing decisions
- MCP tool latency/success
- retry count
- confidence scores
- guardrail decisions
- approval wait time
- remediation outcomes
- verification outcomes
- DeepEval scores

## OTel sidecar topology

```text
Core Pod
  |-- application/agent/MCP container
  |-- OpenTelemetry Collector sidecar
             |
             v
       Central OTel Gateway
        |       |       |
     Prom    Loki    Tempo
        \       |      /
             Grafana
```
