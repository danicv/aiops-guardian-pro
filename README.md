# AIOps Guardian Pro

**Agentic DevOps, Release & Reliability Intelligence Platform**

AIOps Guardian Pro is a full-stack capstone/reference implementation combining release intelligence, pipeline failure analysis, Kubernetes incident investigation, governed remediation, human approvals, email notifications, operational RAG, MCP-based integrations, AI evaluation, and end-to-end observability.

> **Prevent. Resolve. Learn.**

## Included

- React + TypeScript + Vite **NPM frontend**
- FastAPI backend
- LangGraph **Orchestrator Agent**
- Specialized agents: Pipeline, Change, Kubernetes, Monitoring, RAG, History, RCA, Validation, Adaptive, Release Risk, Remediation, Verification
- LangChain / OpenAI-ready integration
- FAISS-ready operational RAG
- PostgreSQL incident/audit memory
- MCP tool server and local HTTP bridge
- Client Integration Hub with pluggable providers
- Guardrails, risk policy, human approvals
- SMTP email notifications and approval links
- DeepEval-ready evaluation layer
- Langflow visual-flow reference
- OpenTelemetry instrumentation and **sidecar Collector** pattern
- Prometheus, Grafana, Loki, Tempo reference stack
- Docker / Docker Compose
- AKS Kubernetes manifests
- Terraform for Azure foundation
- CI/CD workflow examples
- Demo bad-release scenario
- Unit/static tests
- Complete documentation


## End-to-end product architecture

The project includes a presentation-ready enterprise architecture diagram covering the complete product: NPM/React frontend, FastAPI, the LangGraph Orchestrator Agent, specialized agents, guardrails and approvals, MCP/Integration Hub, client tool adapters, RAG/FAISS, PostgreSQL, DeepEval, Langflow, OpenTelemetry sidecars, AKS and Terraform.

![AIOps Guardian Pro end-to-end architecture](docs/diagrams/end-to-end-product-architecture.svg)

For the detailed architecture source and a more connection-heavy engineering view, see [`docs/architecture.md`](docs/architecture.md) and [`docs/diagrams/`](docs/diagrams/).

## Logical architecture

```text
Users / Alerts / Pipeline Events
            |
            v
     React + Vite UI
            |
          FastAPI
            |
╔══════════════════════════════════╗
║ ORCHESTRATOR AGENT - LANGGRAPH  ║
║ intent / plan / state / routing ║
║ retry / pause / resume          ║
╚════════════════╤═════════════════╝
                 |
   +-------------+-------------+
   |             |             |
 Pipeline    Kubernetes    Monitoring
   Agent        Agent         Agent
   |             |             |
 Change         RAG        DB/History
   \             |             /
    +------------+------------+
                 |
          Correlation / RCA
                 |
          Validation Agent
                 |
           Adaptive Agent
                 |
       Risk + Policy Guardrail
          /              \
       ALLOW          APPROVAL
         |                |
         |          Email notification
         |                |
         +---------- Human Approval
                          |
                  Remediation Agent
                          |
                      Action MCP
                          |
                  Verification Agent
                          |
                       DeepEval
                          |
                  PostgreSQL Audit
```

### MCP is the tool plane, not the orchestrator

```text
Specialized Agents -> MCP Client -> MCP Servers -> Client Systems
                                  |-> Kubernetes / AKS
                                  |-> CI/CD
                                  |-> Metrics / Logs / Traces
                                  |-> PostgreSQL / history
                                  |-> Notifications
                                  |-> Governed actions
```

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Open:
- Frontend: http://localhost:3000
- Backend Swagger: http://localhost:8000/docs
- MCP bridge: http://localhost:8001/docs
- Mailpit: http://localhost:8025
- Grafana: http://localhost:3001 (`admin` / `guardian`)
- Prometheus: http://localhost:9090
- Langflow: http://localhost:7860

The repository runs in deterministic **demo mode** without an OpenAI key. Add an OpenAI key to replace demo reasoning with live LLM-backed agent prompts.

## NPM frontend

```bash
cd frontend
npm install
npm run dev
```

Production build:

```bash
npm run build
```

## Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
PYTHONPATH=backend uvicorn app.main:app --reload --port 8000
```

## Primary demo

The demo changes `checkout-api` memory from `1Gi` to `128Mi`. Guardian correlates the deployment, OOMKilled events, restarts, 5xx, latency, runbook guidance, and a similar historical incident. It generates RCA, recommends rollback, triggers the production approval guardrail, sends an approval notification, and preserves the audit trail.

See `demo/README.md`.

## Client integrations

Clients connect through the **Integration Hub** using MCP, REST APIs, webhooks, or native adapters. Reference adapters include GitHub, Azure DevOps, GitLab, ServiceNow, Prometheus, and generic webhooks.

See `docs/client-integration.md`.

## Azure / AKS

Terraform under `infra/terraform` provisions the Azure foundation. Kubernetes manifests under `k8s/` demonstrate the requested **OpenTelemetry Collector sidecar**.

See `docs/deployment-azure.md`.

## Google Cloud Run

The GitHub Actions workflow under `.github/workflows/deploy-gcp.yml` builds the frontend, backend, and MCP bridge, publishes their images to Artifact Registry, and deploys them to Cloud Run using keyless Workload Identity Federation.

See `docs/deployment-gcp.md` for the one-time Google Cloud and GitHub setup.

## Production hardening

This is a capstone/reference implementation. Before client production use, add organization-specific Entra token validation, signed single-use approval links, HA managed PostgreSQL, private endpoints/WAF, secret rotation, production-grade MCP authorization, full integration OAuth flows, security testing, and model/prompt governance.
