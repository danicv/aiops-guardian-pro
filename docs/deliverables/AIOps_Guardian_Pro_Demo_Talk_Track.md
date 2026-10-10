# AIOps Guardian Pro: Demo Talk Track

**Target length:** 6-7 minutes, including the live UI walkthrough  
**Deck:** `AIOps_Guardian_Pro_Demo_Oct_10_2026.pptx`

## Before the demo

Confirm the local cluster is up and these pages load:

- Guardian UI: <http://localhost:30081/ask>
- Sample store: <http://localhost:18081>
- Grafana: <http://localhost:3002/d/guardian-service-health/guardian-service-health>
- Prometheus: <http://localhost:19090/graph>
- Langfuse, optional: <http://localhost:3000>

In Prometheus, confirm `up{job="checkout-api"}` returns `1`. Have Ollama running for chat answers. To create fresh demo traffic, run this against the **local sample store only** before presenting:

```bash
for i in $(seq 1 40); do
  curl -s -o /dev/null -w '%{http_code}\n' \
    -X POST 'http://localhost:18081/api/orders?fail=true&delay_ms=400' \
    -H 'Content-Type: application/json' \
    -d '{"items":[{"sku":"TRAIL-BOTTLE","quantity":1}]}'
done
```

Expect HTTP 503 responses. Allow one Prometheus scrape interval before opening the live investigation. The environment label `prod` is part of this **local demo scope**; this is not a real production service.

## Talk Track

### 1. The page | 20 seconds

**Show:** Slide 1.

**Say:** “It’s 2:07 a.m. Maya is on call, and checkout is failing. Her problem isn’t a shortage of dashboards. It’s that the evidence she needs is scattered, and she has to make a safe decision quickly. This demo follows her investigation.”

**Transition:** “First, what makes this hard?”

### 2. The problem and solution | 35 seconds

**Show:** Slide 2.

**Say:** “Metrics show symptoms. Deploy history, runtime events, logs, and past incidents may each hold another piece. Switching among them costs time, while a generic assistant can sound certain without proof. Guardian brings scoped evidence together, explains what is known and missing, suggests the next check, and routes risky actions through deterministic policy and human approval.”

**Transition:** “Here’s where those responsibilities sit.”

### 3. Architecture | 45 seconds

**Show:** Slide 3; trace left to right.

**Say:** “Maya uses the React UI. FastAPI passes the investigation to a LangGraph orchestrator, which plans work for specialist agents. They use the MCP tool plane to reach observability and runtime systems, while PostgreSQL and FAISS support operational memory and knowledge retrieval. The local Qwen model helps interpret and format evidence; it does not own policy. The Python guardrail engine is a separate boundary, and telemetry and traces make the work inspectable.”

**Transition:** “That architecture produces a bounded investigation flow.”

### 4. Investigation flow | 35 seconds

**Show:** Slide 4.

**Say:** “An alert starts a scoped plan. Guardian gathers and correlates evidence, then checks whether a cause is actually supported. If evidence is thin, it stays read-only and asks for the next check. If an action is risky, policy routes it to a person. Any approved action must still be verified and audited.”

**Transition:** “Let’s see what the alert looks like in this scenario.”

### 5. The signal | 45 seconds

**Show:** Slide 5, then open the Grafana dashboard or the Ask Guardian page.

**Say:** “We inject failing requests into the local checkout demo and Prometheus measures the result. In the recorded October 3 run, 40 failing orders produced a 100% 5xx rate and 500-times error-budget burn. Latency, at 487 milliseconds, was still below the 500-millisecond threshold. Notice that the signals establish degradation, but they don’t establish its cause.”

**Do:** In Ask Guardian, select **Live Prometheus** and the `checkout-api` / `prod` / `aiops-guardian` scope. Ask: “Why is checkout-api failing in production right now?” Point to the measured evidence and PromQL. If today’s values differ, describe the live values on screen; the numbers printed on the slide are from the recorded run.

**Transition:** “A useful assistant should know when to stop short.”

### 6. The honest answer | 35 seconds

**Show:** Slide 6 and the live investigation result.

**Say:** “The live investigation detects the 5xx and error-budget burn, but it has no deployment, log, or trace evidence to prove a root cause. So Guardian says ‘needs review,’ reports confidence zero, and asks to collect evidence. It doesn’t turn a symptom into a confident-sounding story or make a production change.”

**Transition:** “To show retrieval, I’ll switch scenarios. This next one is simulated.”

### 7. A past case, clearly labeled | 30 seconds

**Show:** Slide 7, then switch Ask Guardian to **Simulated demo** and run the OOM example.

**Say:** “This is not the cause of the live incident. In this controlled replay, a memory-limit change from 1 GiB to 128 MiB precedes OOMKilled restarts. Guardian retrieves the matching synthetic precedent, `SYN-K8S-001`, and the runbook’s suggested check. A precedent is useful context, not proof about Maya’s live incident.”

**Transition:** “Even with a recommendation, the system doesn’t get the final say.”

### 8. Maya decides | 35 seconds

**Show:** Slide 8, then the approval queue. Do not approve the action during the demo.

**Say:** “A production rollback is high risk, so deterministic policy requires human approval. The demo creates an approval record and leaves the action unexecuted. Maya can inspect the evidence and context before deciding. The point is not autonomous remediation; it’s faster investigation with authority still in human hands.”

**Close:** “Guardian helps Maya find and explain evidence sooner. It does not replace her judgment, and it does not bypass the policy gate.”

## If the live data is quiet

Do not present stale metrics as live. Use the recorded values on Slide 5 and call them the **October 3 forced run**. You can still show that Prometheus is connected with `up{job="checkout-api"}` returning `1`, then continue to the live investigation and explain that no current traffic means no recent rate to display.

## Keep These Distinctions Clear

- **Live mode:** measured Prometheus data; current RCA may remain unconfirmed.
- **Simulated demo mode:** scripted OOM scenario and synthetic precedent; not live evidence.
- **Approval:** a request is not execution. The recorded risky action was held and not executed.
- **Slide metrics:** recorded on 2026-10-03. Read current values from the live UI if they differ.