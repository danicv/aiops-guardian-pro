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
