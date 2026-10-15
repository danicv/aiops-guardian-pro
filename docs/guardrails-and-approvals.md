# Guardrails and decision-support mode

Guardrails are deterministic product policy, not merely natural-language instructions to an LLM.
The submitted capstone runs with `DECISION_SUPPORT_ONLY=true` by default. In this mode
Guardian may collect and explain read-only evidence but refuses infrastructure mutation,
approval, remediation, and notification requests. The mode is enforced in the API,
orchestrator, backend action services, MCP gateway, and MCP tool process; a conversational
refusal is only an additional UX layer. Changing the setting to `false` is an explicit
deployment policy change and must be reviewed independently.

## Four layers

### Input guardrails
Authentication, RBAC, tenant/environment scope, application scope, prompt abuse controls, and secret/PII handling.

### Tool guardrails

| Tool/action | Risk | Default |
|---|---:|---|
| get_pods / get_logs / query_metrics | READ_ONLY | Allow |
| restart_pod | LOW | Block in decision-support mode |
| scale_deployment | MEDIUM | Block in decision-support mode |
| rollback_deployment | HIGH | Block in decision-support mode |
| delete_cluster / drop_database | PROHIBITED | Block |

Unknown actions are denied by default.

### Output guardrails
Minimum confidence, multiple independent evidence signals, source attribution/citations, sensitive-data filtering, and explicit uncertainty when evidence is insufficient.

### Action guardrails

```text
Read-only request -> collect evidence -> explain uncertainty -> recommend checks
Mutation request  -> deterministic refusal -> no approval, notification, or tool call
```

The approval workflow remains in the codebase for deployments that deliberately
configure an action-enabled policy, but it is unavailable in the capstone's default
decision-support mode. Existing pending approvals cannot be approved while that mode
is active. Rejecting or deleting an approval does not execute infrastructure changes.

## Conversation retention

Saved conversations expire after 30 days without activity by default. The retention
period is configurable with `CONVERSATION_RETENTION_DAYS` (1–365 days); a background
cleanup runs hourly by default (`CONVERSATION_CLEANUP_SECONDS`) and cleanup also runs
on conversation access or creation. Expired rows are physically deleted. Users with
conversation access can delete an individual conversation through
`DELETE /api/conversations/{id}`. Updates use a revision check so a reply already in
flight cannot recreate a conversation after deletion.

## Approval audit fields
Request ID, incident/investigation ID, action, environment, risk, evidence summary, requester, request time, approver, decision time, comment, execution result and verification result.
