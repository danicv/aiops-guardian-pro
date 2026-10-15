# Engineering & Product Justification

## Product
AIOps Guardian Pro is a decision-support copilot for SREs. It investigates an incident (metrics, logs, Kubernetes state, past incidents), explains a hypothesis with evidence and confidence, and suggests read-only checks. In the submitted configuration, infrastructure changes and approvals are refused; a human performs any authorized change outside Guardian.

## Design decisions and tradeoffs
| Decision | Why | Tradeoff |
|---|---|---|
| LangGraph state machine (collect evidence -> diagnose -> validate -> recommend/refuse) | Each step is inspectable and testable; the "need more evidence" branch and policy refusal are explicit | More structure than plain functions for a small flow |
| Embeddings retrieval with similarity floor, lexical fallback, feedback re-ranking | Paraphrases beat keywords (top-1 4/8 -> 7/8); the floor returns "no precedent" instead of a wrong one; fallback keeps it working if the embedding endpoint is down | Needs an embedding model; one paraphrase still misses (`SYN-QUEUE-002`) |
| Local small LLM (Ollama `qwen2.5:1.5b`) via OpenAI-compatible API | No data leaves the machine, zero cost, same code for hosted models | Weak instruction following, so safety is enforced in code, not prompts |
| Deterministic RCA validation ("unconfirmed", confidence 0 when evidence is only metrics) | Avoids confident-sounding guesses | Fewer definitive answers |
| Feedback adaptation (net votes, clamped to +/-3, x(1+0.15*votes)) | Cheap, auditable learning from users without retraining | Ratings are global, not per user or service |
| Baseline rules-only agent kept for comparison | Shows what the LLM and retrieval add | Extra code to maintain |

## Safety approach
- Policy is plain Python (`backend/app/guardrails.py`), not an LLM. `DECISION_SUPPORT_ONLY=true` blocks all infrastructure mutations and approval execution before they reach MCP; destructive and unknown actions are also denied. The API, remediation service, gateway, and MCP tool process enforce the boundary independently.
- Mutation requests receive a deterministic refusal before the LLM or investigation tools are called; no approval record or action notification is created in this mode.
- Prompt-injection and out-of-scope requests are checked before the LLM (`docs/evidence/safety-enforcement.md`).
- Logs redact messages, exception details, and structured fields. Langfuse receives only a constant content-omission marker, and OpenTelemetry exports operation timing/status without attributes or events.
- Conversation records expire after 30 days of inactivity by default, are cleaned hourly and on access, and can be deleted immediately through `DELETE /api/conversations/{id}`.

## Deployment assumptions
- Demo: local kind cluster (arm64), Postgres, Ollama on the host, Prometheus/Loki/Grafana, Langfuse. Port-forwards expose the UI (30081), backend (30800), Grafana (3002).
- Postgres migrations run manually (`alembic upgrade head`); SQLite auto-creates tables for local use.
- Production would need real SSO/RBAC, a stronger hosted LLM, privacy-preserving trace configuration, secret management and per-service feedback.

## Known limitations
- Demo-mode RCA is scripted; live mode gives honest "unconfirmed" results from metrics alone.
- No feedback button in the UI yet (`POST /api/feedback` only).
- Decision-support mode intentionally disables the existing approval/remediation workflow; users must make any authorized infrastructure change through independently authorized operational tooling.
