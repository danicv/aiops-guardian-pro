# Guardrails and approvals

Guardrails are deterministic product policy, not merely natural-language instructions to an LLM.

## Four layers

### Input guardrails
Authentication, RBAC, tenant/environment scope, application scope, prompt abuse controls, and secret/PII handling.

### Tool guardrails

| Tool/action | Risk | Default |
|---|---:|---|
| get_pods / get_logs / query_metrics | READ_ONLY | Allow |
| restart_pod | LOW | policy/environment dependent |
| scale_deployment | MEDIUM | Require approval |
| rollback_deployment | HIGH | Require approval |
| delete_cluster / drop_database | PROHIBITED | Block |

Unknown actions are denied by default.

### Output guardrails
Minimum confidence, multiple independent evidence signals, source attribution/citations, sensitive-data filtering, and explicit uncertainty when evidence is insufficient.

### Action guardrails

```text
Recommendation -> Policy -> Risk
                        |-- ALLOW -> execute
                        |-- REQUIRE_APPROVAL -> human approval
                        |-- BLOCK -> stop
```

## Human-in-the-loop

```text
High-risk recommendation
   -> create approval record
   -> send email/notification
   -> secure portal link
   -> Entra authentication
   -> RBAC authorization
   -> approve/reject
   -> resume workflow if approved
```

Never execute a production change simply because somebody replies "yes" to an email.

## Approval audit fields
Request ID, incident/investigation ID, action, environment, risk, evidence summary, requester, request time, approver, decision time, comment, execution result and verification result.
