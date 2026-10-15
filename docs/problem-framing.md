# Problem framing

## Who has the problem
An on-call SRE at 2am, paged for a production service. Time goes into gathering signals (metrics, deploys, logs, past incidents), not into deciding. Generic chat assistants make it worse: they sound confident without evidence and, if given tools, can take unsafe actions.

## Problem statement
Reduce time-to-diagnosis for production incidents **without** letting an AI system change production on its own authority or present guesses as facts.

## What Guardian does (and deliberately does not do)
| Does | Does not |
|---|---|
| Queries live Prometheus/Loki for the scoped service and reports only what was measured | Treat missing data as healthy, or infer a cause from metrics alone |
| Retrieves similar past incidents and runbooks as *precedents*, labelled synthetic | Present a precedent's cause as confirmed for the current incident |
| Explains risk and suggests read-only checks | Execute or approve infrastructure changes |
| Deterministically refuses mutation requests in decision-support mode | Create approval requests or send action notifications |
| Labels simulated/demo data as simulated | Mix demo and live evidence |

## Success criteria
1. When a fault is injected, Guardian detects it from live metrics within one scrape window.
2. With thin evidence it answers "unconfirmed" and asks for the next check, instead of guessing (confidence 0, `collect_evidence`).
3. In the submitted decision-support configuration, every infrastructure mutation is refused before tool invocation; prohibited and unknown actions remain `BLOCK`.
4. Retrieval puts the correct precedent first for labelled scenarios (`backend/tests/test_retrieval_quality.py`).
5. Every answer is traceable: agent trace, evidence list, PromQL used, Langfuse trace.

## Non-goals
Autonomous remediation, replacing the incident commander, learning policy at runtime, multi-cluster orchestration.

## Key design decisions
- **Safety is deterministic, not prompt-based.** The policy (`backend/app/guardrails.py`) is plain code. Prompts are a second layer; see `docs/evidence/prompt-comparison.md` for why that matters with a small local model.
- **Privacy is fail-closed for telemetry.** Langfuse payloads are omitted and OpenTelemetry exports contain operation timing/status only; logs redact messages, exceptions, and structured fields.
- **Local first.** kind + Ollama (`qwen2.5:1.5b`) so the full loop runs with no API key; any OpenAI-compatible endpoint can replace it.
- **Honest uncertainty.** Live mode returns `insufficient_data` / `needs_review` rather than a fabricated RCA.

## Known limitations
- The demo-mode RCA (`RCAAgent`) is a scripted scenario (OOM after memory reduction); only live mode reasons from measured data.
- The 1.5B local model is weak at following refusal instructions (measured, see prompt comparison).
- Retrieval is keyword-based by default. Embedding retrieval (`EMBEDDING_BASE_URL` + `EMBEDDING_MODEL`, e.g. Ollama `nomic-embed-text`) is opt-in; it reached 7/8 vs 4/8 top-1 on paraphrased queries (`docs/evidence/embedding-retrieval.md`) but the corpus is still 34 synthetic cases.
- Feedback ratings are global per case, not per user or service, and have no UI yet (`POST /api/feedback`).
- Conversation retention is 30 days since last activity by default, with hourly/on-access cleanup and an immediate delete endpoint.
- Pattern-based redaction alone cannot identify every name or free-form identifier; traces therefore omit arbitrary content rather than relying only on patterns.
