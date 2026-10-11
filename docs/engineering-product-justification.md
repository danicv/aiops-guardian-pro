# Engineering & Product Justification

## Product
AIOps Guardian Pro is a decision-support copilot for SREs. It investigates an incident (metrics, logs, Kubernetes state, past incidents), explains a hypothesis with evidence and confidence, and proposes a next step. A human decides; the agent never changes production on its own.

## Design decisions and tradeoffs
| Decision | Why | Tradeoff |
|---|---|---|
| LangGraph state machine (collect evidence -> diagnose -> validate -> approval) | Each step is inspectable and testable; the "need more evidence" branch and approval pause are explicit | More structure than plain functions for a small flow |
| Embeddings retrieval with similarity floor, lexical fallback, feedback re-ranking | Paraphrases beat keywords (top-1 4/8 -> 7/8); the floor returns "no precedent" instead of a wrong one; fallback keeps it working if the embedding endpoint is down | Needs an embedding model; one paraphrase still misses (`SYN-QUEUE-002`) |
| Local small LLM (Ollama `qwen2.5:1.5b`) via OpenAI-compatible API | No data leaves the machine, zero cost, same code for hosted models | Weak instruction following, so safety is enforced in code, not prompts |
| Deterministic RCA validation ("unconfirmed", confidence 0 when evidence is only metrics) | Avoids confident-sounding guesses | Fewer definitive answers |
| Feedback adaptation (net votes, clamped to +/-3, x(1+0.15*votes)) | Cheap, auditable learning from users without retraining | Ratings are global, not per user or service |
| Baseline rules-only agent kept for comparison | Shows what the LLM and retrieval add | Extra code to maintain |

## Safety approach
- Policy is plain Python (`backend/app/guardrails.py`), not an LLM: read-only tools are allowed, `restart_pod` is low risk, `scale_deployment` and `rollback_deployment` require human approval, destructive actions are blocked, unknown actions are denied by default.
- Recommended actions are only proposals with an approval record; nothing executes until approved by an authorised user.
- Prompt-injection and out-of-scope requests are checked before the LLM (`docs/evidence/safety-enforcement.md`).
- PII and secrets are redacted from logs and audit payloads (`docs/evidence/pii-safe-logging.md`). Limits: pattern-based, so names are not caught, and Langfuse traces are not redacted.
- Every investigation, approval and decision is audited; Langfuse traces the LLM calls.

## Deployment assumptions
- Demo: local kind cluster (arm64), Postgres, Ollama on the host, Prometheus/Loki/Grafana, Langfuse. Port-forwards expose the UI (30081), backend (30800), Grafana (3002).
- Postgres migrations run manually (`alembic upgrade head`); SQLite auto-creates tables for local use.
- Production would need real SSO/RBAC, a stronger hosted LLM, redacted tracing, secret management and per-service feedback.

## Known limitations
- Demo-mode RCA is scripted; live mode gives honest "unconfirmed" results from metrics alone.
- No feedback button in the UI yet (`POST /api/feedback` only).
- The agent proposes approval-gated rollbacks, which goes slightly beyond pure decision support; execution stays human-approved.
