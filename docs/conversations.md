# Ask Guardian conversations

Ask Guardian now keeps an investigation as a conversation. Describe the problem,
answer its clarifying question, or ask a follow-up. Guardian retains the original
problem and your reported context rather than starting over each turn.

The page distinguishes:

- **Your reports**: symptoms, onset, recent changes, and impact supplied in chat.
- **Observed evidence**: the scoped Prometheus snapshot and its collection time.
- **Advice**: checks and hypotheses; a reported deployment is not proof of cause.

Select the service, environment, namespace, and live/demo mode before starting.
The scope stays fixed for that conversation. Start a new conversation to inspect
a different scope. Saved conversations remain in PostgreSQL and can be reopened.
The active conversation is remembered in the browser across reloads.

Each reply may ask one question to resolve an important uncertainty. If you do
not know an answer, say so; the assistant can proceed while preserving that gap.
Use **Refresh metrics** to collect a new snapshot. Ordinary replies use the
existing snapshot and do not silently change its evidence.

## Guided and LLM modes

Without `OPENAI_API_KEY`, the assistant identifies common symptoms, asks guided
questions, and refines conditional SRE checks from the context provided. This is
labelled **Guided assistant**; it is not a general-purpose language model.

When the backend has `OPENAI_API_KEY` and `OPENAI_MODEL` configured, replies use
the configured model with structured output. It receives the conversation,
reported context, scoped evidence, and instructions to separate observations
from hypotheses. A provider failure falls back to guided advice with a visible
notice. The model key belongs in backend configuration or a Kubernetes Secret,
never in frontend code. No key is created or supplied by this feature.

Conversations never execute infrastructure commands, grant approvals, or send
notifications. Demo conversations use explicitly labelled sample evidence and
also bypass the demo action/approval graph.

## API

- `POST /api/conversations`: `message`, `application`, `environment`, `namespace`,
  `telemetry_mode` (`live` or `demo`). Returns the initial assistant reply and snapshot.
- `GET /api/conversations`: up to 50 recent saved conversations.
- `GET /api/conversations/{id}`: complete conversation, context, and current snapshot.
- `POST /api/conversations/{id}/messages`: `message`, `expected_revision`, and
  optional `refresh_metrics`. Returns the new complete conversation.

Revisions start at one and increment per exchange. A stale or concurrent write
returns HTTP 409; reload before retrying. Messages are limited to 4,000 characters
and a conversation to 30 exchanges to bound retained model context.
The existing one-shot `/api/investigations` and simulator endpoints remain available.

The new `conversations` table is additive and created by the existing database
startup initialization. Existing investigation records are unchanged.

## Enabling the model in the local cluster

The backend accepts an optional Kubernetes Secret named `guardian-llm` containing
`OPENAI_API_KEY` and optionally `OPENAI_MODEL`. Create it from a private environment
file outside the repository, then restart the backend:

```sh
kubectl --context kind-guardian-local -n aiops-guardian create secret generic guardian-llm --from-env-file=/path/to/private/guardian-llm.env
kubectl --context kind-guardian-local -n aiops-guardian rollout restart deployment/guardian-backend
```

The UI labels each reply with the mode actually used, including fallback when a
provider call fails. Guided mode remains available when the optional Secret is absent.

To validate the deployed chat API and saved history through the local port forwards:

```sh
python scripts/verify_conversations.py
```
