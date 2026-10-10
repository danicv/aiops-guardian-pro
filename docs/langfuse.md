# Self-hosted Langfuse

Guardian can export LangGraph and LangChain conversation traces to a self-hosted Langfuse project. OpenTelemetry remains enabled independently for infrastructure traces and the configured OTLP collector.

## What is traced

- Demo-mode LangGraph investigation runs, including graph/node callbacks
- LLM-backed Ask Guardian conversation turns and model generations
- Application, environment, namespace, investigation ID, and telemetry mode as trace metadata where available

Live telemetry investigation/report queries remain read-only Prometheus/Loki operations. They are not model generations; OpenTelemetry remains the trace source for those service spans.

## Requirements

1. Run Langfuse using the official self-hosted deployment instructions for your platform. Keep it on a private network reachable by Guardian.
2. Create a Langfuse organization/project and obtain that project's public and secret keys.
3. Provide the Langfuse server base URL, for example `http://langfuse.example.internal:3000`.
4. Configure these backend environment variables:

```text
LANGFUSE_ENABLED=true
LANGFUSE_HOST=http://langfuse.example.internal
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

Use the server base URL shown by your Langfuse deployment; do not append an API or OTLP path.

Tracing is off by default. If the flag is off, or any setting is missing, the application continues without Langfuse. Initialization and flush errors are logged and do not fail investigations.

## Local kind

From the repository root, run `make langfuse-up`. It clones the official Langfuse repository into ignored `.local/langfuse/`, starts its Compose stack and a local Ollama service, pulls `qwen2.5:1.5b`, creates the `guardian-langfuse` Kubernetes Secret, and rebuilds Guardian with a header link to `http://localhost:3000`. The generated Langfuse login and project keys are stored in `.local/langfuse/access.txt` with owner-only file permissions. Guardian conversations use the local Ollama model without a provider API key; traces are sent to Langfuse. Model weights persist in a Compose volume. Langfuse UI, MinIO, and Ollama ports are bound to localhost; the kind backend reaches the services through `host.docker.internal`.

Stop the stack without deleting its data with:

```bash
docker compose --project-name guardian-langfuse \
	--env-file .local/langfuse/langfuse.env \
	-f .local/langfuse/source/docker-compose.yml \
	-f scripts/langfuse.local.compose.yaml down
```

For a Langfuse instance running as another Kubernetes service, set `LANGFUSE_HOST` to its cluster DNS address, such as `http://langfuse.observability.svc:3000`.

## Docker Compose

Put the four settings in the local `.env` file (which is ignored by Git), with a host reachable from the backend container. When Langfuse is another service in the same Compose project, use its service name rather than `localhost`.

## Data handling

Langfuse callbacks capture model inputs and outputs, which may contain user questions, operational context, and evidence summaries. Before enabling it for real incidents:

- restrict Langfuse network access and project membership;
- set retention and backup policies appropriate to your incident data;
- avoid sending secrets or regulated data in prompts;
- define redaction/retention requirements with your security team;
- use TLS for remote Langfuse endpoints.
