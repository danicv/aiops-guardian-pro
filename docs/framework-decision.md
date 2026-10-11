# Framework usage and justification

| Concern | Choice | Why | Alternative considered |
|---|---|---|---|
| Agent orchestration | **LangGraph** (`orchestrator.py`) | The flow is a small state machine with a conditional edge (validation -> approval, or collect more evidence). Explicit nodes make every step inspectable and testable | Plain functions: fine for a linear flow, but the adaptive branch and approval pause are clearer as a graph |
| LLM access | **LangChain `ChatOpenAI`** pointed at any OpenAI-compatible URL | Same code for Ollama (local, no key) and hosted providers; structured output for chat replies | Direct HTTP client: less code, but loses callbacks used for Langfuse tracing |
| Retrieval | Embeddings (any OpenAI-compatible endpoint; local Ollama `nomic-embed-text`) with a similarity floor, lexical scoring as fallback and default, feedback re-ranking | Paraphrases defeat keywords (4/8 vs 7/8 top-1); the floor lets it return "no precedent" instead of an irrelevant case; lexical fallback keeps the system working when the endpoint is down | FAISS (needs OpenAI key; unnecessary for 34 cases, numpy cosine suffices) |
| Safety policy | **No framework**: plain Python (`guardrails.py`) | Policy must be auditable and unit-testable; an LLM or framework must not be able to alter it | LLM-based guard: rejected, see `docs/evidence/prompt-comparison.md` |
| Evaluation | Deterministic checks (`evaluation.py`) + labelled retrieval test + prompt comparison harness | See `docs/evaluation-report.md` | DeepEval is a dependency but its LLM-judge metrics need a strong judge model; a 1.5B local model is not a reliable judge |
| Observability | OpenTelemetry sidecar, Prometheus, Loki, Grafana, Langfuse | Standard stack; Langfuse for LLM traces | |
