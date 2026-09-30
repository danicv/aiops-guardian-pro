# AIOps Guardian Pro User Guide

This guide is for people using the Guardian web app. It explains how to inspect service health, investigate an incident, practice with simulated scenarios, and review proposed actions.

## Open Guardian

For the local kind deployment, open <http://localhost:30081>. The app header can link to the Sample Store, Grafana service-health dashboard, Prometheus UI, and Langfuse when those local links are configured.

Prometheus and Langfuse are separate tools. Prometheus is used to inspect scraped metrics; Langfuse is used to inspect agent and model traces. Langfuse requires its own sign-in. Local bootstrap login details are stored in the ignored `.local/langfuse/access.txt` file. Keep that file private and change the initial password before sharing the environment.

### Grafana dashboard (local kind)

The local kind deployment provisions a **Guardian Service Health** Grafana dashboard backed by Prometheus. It includes request rate, 5xx percentage, p95 latency, scrape-target status, request rate by HTTP status, p50/p95/p99 latency, confirmed demo orders, and demo order value. Dashboard filters let you choose service, environment, and namespace.

To open Grafana, start a port-forward from the repository root:

```bash
kubectl port-forward -n aiops-guardian service/guardian-grafana 3002:3000
```

Then open <http://localhost:3002>. The local demo login is `admin` / `guardian-local`. The Guardian header link opens the provisioned dashboard directly when this port-forward is active. Change the demo password before exposing Grafana beyond your local machine.

The dashboard currently covers metrics, not logs. Its order count and value are in-memory demo totals and reset when the checkout service restarts. Loki is provisioned as a datasource, but logs will remain empty until a log collector is configured to ship container logs into Loki.

## Main areas

- **Dashboard** gives a summary of open investigations, the approval queue, and shortcuts to investigations, reports, simulator, and integrations.
- **Ask Guardian** is a saved, conversational investigation. It gathers an initial snapshot, answers follow-up questions, and retains the conversation context.
- **Live reports** shows current metrics and recent time-series observations for one service scope.
- **Simulator** creates explicitly synthetic training incidents and shows the synthetic case library.
- **Investigations** lists investigation records. Open an ID to review its findings, evidence, proposed action, and execution trace.
- **Approvals** lists actions that are waiting for a decision.
- **Integrations** lets you configure available metrics and log sources.
- **Pipelines** and **Architecture** provide reference views of the sample pipeline and system design.

## Demo the sample checkout store

Open **Sample Store** from the Guardian header, or start a local tunnel with:

```bash
kubectl port-forward -n aiops-guardian service/checkout-api 18081:8080
```

Then open <http://localhost:18081>. Browse the fictional Northstar Supply products, add items to the bag, adjust quantities, and place a mock order. The cart is kept in your browser and recent orders are kept in memory by the demo service; restarting the service clears its order history. No name, address, card details, payment, or shipment is involved.

The **Checkout response** selector can generate normal traffic, add 450 ms of synthetic latency, or return a synthetic 503. Use these only in the local training environment. Each action updates the `checkout-api` Prometheus request/latency metrics; successful orders also emit synthetic order-count and order-value metrics for Grafana.

## Check live service health

1. Open **Live reports**.
2. Enter the exact application, environment, and namespace labels used by the telemetry source. The local demo defaults are `checkout-api`, `prod`, and `aiops-guardian`.
3. Choose a 15-, 30-, or 60-minute window and select **Refresh**.
4. Review the current request rate, 5xx rate, p95 latency, error-budget burn, and their time-series charts.
5. Expand **View observations** to inspect individual time buckets, or **Inspect source query** to see the PromQL used.
6. Review **Log evidence** when a log source is configured. Select **Open Ask Guardian** to investigate the same service scope.

A displayed `Unknown`, `Unavailable`, or chart gap means Guardian did not receive a usable measurement for that scope and time. It does not mean the service is healthy or the metric is zero. Check the selected labels, source health, and whether recent requests produced samples. The local Prometheus UI is useful for checking whether a target is `UP` and testing a PromQL query.

## Investigate with Ask Guardian

1. Open **Ask Guardian** and start a new conversation.
2. Set the application, environment, namespace, and telemetry mode before sending the first message. A conversation keeps this scope; start another conversation to change it.
3. Describe the symptom and ask a specific question, for example: “Checkout latency increased after the release. What should I check?”
	Press **Enter** to send; use **Shift+Enter** to add a newline.
4. Answer Guardian’s follow-up questions with what you know. Say when a detail is unknown; correct earlier information explicitly when needed.
5. Use **Refresh telemetry** when you want a fresh live snapshot. Existing messages and user-reported context remain in the conversation.
6. Expand the evidence sections to distinguish measured metrics, user-reported details, investigation hypotheses, synthetic historical examples, guardrails, and suggested next steps.

**Live Prometheus** asks Guardian to query the configured metrics source. **Simulated demo** uses sample evidence and is clearly labeled; it is not a measurement of a real service. A configured local Ollama model can provide LLM assistant replies without a cloud API key. LLM text is still an interpretation of supplied context, not independent proof. Verify important claims against the displayed evidence.

## Practice safely in Simulator

1. Open **Simulator** and choose a scenario: OOM after release, latency and 5xx spike, or pipeline failure.
2. Choose the environment and number of incidents (1 to 10), then select **Run scenario**.
3. Open a returned investigation ID to inspect the generated evidence and workflow. Any associated approval is also shown in the result.
4. Use the synthetic case library as historical training context. It contains fictional examples and does not describe the current service.

Simulator records are saved in investigation history and may create approval records. They are labeled as synthetic, but they can appear in shared dashboard counts and lists. Do not mistake them for live incidents. Running the simulator does not intentionally change the demo service or production systems.

## Review investigations and approvals

On an investigation detail page, review the status, confidence, root-cause hypothesis, evidence, similar synthetic cases, recommended action, guardrail decision, and agent execution trace. Treat a proposed root cause as a hypothesis unless the cited observations support it.

Production or other high-risk recommendations can pause for human approval. Open **Approvals**, inspect the action, environment, risk, and linked investigation, then approve or reject according to your team's policy. Approval records are workflow decisions; they are not evidence that a change succeeded. Check the resulting execution and verification status before considering an incident resolved.

Only make or approve operational changes under your organization’s normal incident, change-control, and access procedures. The local reference/demo environment is not a substitute for production identity, authorization, or change-management controls.

## Configure telemetry sources

Open **Integrations** to see available adapters and saved configurations. For an available Prometheus or Loki source:

1. Select the provider and provide a name and an endpoint reachable from the Guardian backend.
2. Select **Test connection** to make a read-only connectivity check.
3. Select **Save source** to store the configuration.
4. Select **Use for investigations** to make it the active source for new live investigations and reports.

Saving a source does not test it or select it. An active selection also does not prove the source is healthy; confirm the connection test and report evidence. If no Prometheus source is selected, Guardian uses its configured default. Never paste credentials into the source URL or into chat. If a backend bearer token is required, configure it as a backend environment secret and enter only its environment-variable name in Guardian.

## Traces in Langfuse

Open **Langfuse** from the Guardian header and sign in separately. Langfuse shows the model and agent observations that Guardian exports, such as the `guardian-conversation` chain and model generations. Tracing must be enabled and the backend must be able to reach the Langfuse instance. Langfuse traces can include prompts, answers, questions, and operational context; restrict access accordingly and avoid sending secrets or regulated data.

## Common issues

- **A report shows no measurements:** check application/environment/namespace labels, recent traffic, Prometheus target health, and the report time range.
- **The report has values but chart gaps:** the chart window includes intervals without samples. Missing intervals stay unknown.
- **Ask Guardian says Guided assistant:** no working LLM is configured, or the model request failed. In the local demo, check that Ollama is running and the model is available.
- **No Langfuse trace appears:** check that Langfuse is running, tracing is enabled, and the backend can reach its configured Langfuse URL. A trace is created by a traced workflow; simply opening a page does not create one.
- **Simulator data appears among investigations:** these are saved training records. Check their synthetic label and telemetry mode before treating them as live incidents.
- **A saved integration is not being used:** select **Use for investigations**, then refresh or start a new investigation/report. Selection affects new snapshots.
