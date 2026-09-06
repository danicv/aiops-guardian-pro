# AIOps Guardian Pro — One-Page End-to-End Architecture

![AIOps Guardian Pro end-to-end architecture](diagrams/end-to-end-product-architecture.svg)

## Responsibility boundaries

- **LangGraph Orchestrator Agent** owns intent, plan, shared state, agent selection, retries, pause/resume and completion.
- **Specialized agents** reason within DevOps domains such as pipeline, Kubernetes, observability, change, RAG and history.
- **MCP** is the governed tool/integration plane and does not orchestrate agents.
- **Guardrails and approvals** deterministically govern operational actions.
- **Integration Hub** lets clients connect CI/CD, ITSM, observability, runtime and collaboration tools through MCP, REST, webhooks or native adapters.
- **PostgreSQL + FAISS** provide structured operational memory and semantic knowledge.
- **OpenTelemetry sidecars** observe the backend, agent runtime, MCP calls, guardrails, approvals and remediation.
- **AKS + Terraform** provide the container runtime and repeatable Azure infrastructure.

## Closed-loop product flow

```text
Code / Pipeline / Alert
        -> Orchestrator
        -> Specialized investigation agents
        -> Evidence correlation / RCA
        -> Validation / adaptive routing
        -> Release risk / remediation recommendation
        -> Guardrail policy
        -> Human approval when required
        -> Action MCP
        -> Verification
        -> Audit / DeepEval / PostgreSQL
        -> Future release-risk learning
```
