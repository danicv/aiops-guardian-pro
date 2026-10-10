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
| Proposes an action and passes it through deterministic guardrails | Execute anything; the LLM has no tool that mutates the cluster |
| Holds risky actions for a named human approval with full context | Auto-approve production changes |
| Labels simulated/demo data as simulated | Mix demo and live evidence |

## Success criteria
1. When a fault is injected, Guardian detects it from live metrics within one scrape window.
2. With thin evidence it answers "unconfirmed" and asks for the next check, instead of guessing (confidence 0, `collect_evidence`).
3. Every state-changing action in production is `REQUIRE_APPROVAL`; prohibited and unknown actions are `BLOCK`.
4. Retrieval puts the correct precedent first for labelled scenarios (`backend/tests/test_retrieval_quality.py`).
5. Every answer is traceable: agent trace, evidence list, PromQL used, Langfuse trace.

## Non-goals
Autonomous remediation, replacing the incident commander, learning policy at runtime, multi-cluster orchestration.

## Key design decisions
- **Safety is deterministic, not prompt-based.** The policy (`backend/app/guardrails.py`) is plain code. Prompts are a second layer; see `docs/evidence/prompt-comparison.md` for why that matters with a small local model.
- **Local first.** kind + Ollama (`qwen2.5:1.5b`) so the full loop runs with no API key; any OpenAI-compatible endpoint can replace it.
- **Honest uncertainty.** Live mode returns `insufficient_data` / `needs_review` rather than a fabricated RCA.

## Known limitations
- The demo-mode RCA (`RCAAgent`) is a scripted scenario (OOM after memory reduction); only live mode reasons from measured data.
- The 1.5B local model is weak at following refusal instructions (measured, see prompt comparison).
- Retrieval is keyword-based over a 34-case synthetic corpus, not embeddings.
