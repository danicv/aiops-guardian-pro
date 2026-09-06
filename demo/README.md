# Capstone demo — unsafe memory release

## Story
`checkout-api:v1.9.0` is healthy with a 1Gi memory limit. A developer proposes/deploys `v2.0.0`, reducing the limit to 128Mi.

### 1. Prevent
Release Risk Agent detects a severe reduction, missing load-test evidence, and a similar historical incident. Risk: **HIGH**.

### 2. Detect and investigate
For the demo, allow the release to proceed. Simulated signals:
- OOMKilled
- pod restarts
- HTTP 5xx: 0.2% -> 6.8%
- p95 latency: 180ms -> 690ms

### 3. RCA
The Orchestrator invokes Kubernetes, Monitoring, Change, RAG and History agents and correlates evidence.

Expected RCA: the new memory limit is below application demand and causes OOMKilled/restart/error symptoms.

### 4. Guardrail
Recommended action: rollback `v2.0.0 -> v1.9.0`. Environment: production. Risk: HIGH. Result: **REQUIRE_APPROVAL**.

### 5. Notification and approval
An approval record is created and email is sent through Mailpit. Open http://localhost:8025, then use the React `Approvals` page.

### 6. Remediation and verification
The reference implementation exposes Action MCP and a verification node. A production implementation resumes the LangGraph checkpoint after approval and executes the action through the protected Action MCP.

### 7. Learn
Investigation, evidence, approval and outcomes are stored in PostgreSQL for future release-risk analysis.
