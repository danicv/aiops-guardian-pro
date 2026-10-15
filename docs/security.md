# Security architecture

## Identity
- Microsoft Entra ID SSO for users
- AKS Workload Identity for workloads
- separate principals/service accounts for diagnostic and action capabilities

## Authorization
- application RBAC
- Kubernetes RBAC
- MCP capability policy
- environment/application scopes

## Secrets
- Azure Key Vault
- no secrets in Git
- no plaintext integration tokens in PostgreSQL

## Network
- MCP and PostgreSQL remain internal ClusterIP services
- TLS at ingress
- private endpoints / private cluster where client policy requires
- network policies

## AI-specific controls
- retrieved-document authorization
- evidence/citation requirement
- sensitive-output filtering
- deterministic tool allowlists
- bounded retries
- no private chain-of-thought exposure
- decision-support-only mode refuses infrastructure mutations, approvals, and notifications by default; API and MCP boundaries fail closed
- application logs redact record messages, exceptions, and structured `extra` fields before handlers receive them
- Langfuse trace payloads are replaced with a constant privacy marker; OpenTelemetry exports only operation timing/status, with attributes, events, resource values, and exception details stripped

Privacy note: decision-support mode intentionally favors omission over diagnostic detail in application logs and traces. Keep raw prompts, outputs, credentials, and customer data out of external observability systems. Redaction patterns outside the trace masks are defense in depth, not a guarantee that arbitrary text has no personal information.

## Conversation lifecycle
- Stored conversations expire after 30 days of inactivity by default; configure `CONVERSATION_RETENTION_DAYS` within 1–365 days.
- Cleanup runs hourly by default and on conversation access/creation.
- `DELETE /api/conversations/{id}` removes a saved conversation immediately. In-flight replies cannot resurrect deleted or expired rows.

## Audit
Record user, agent, tool, action, policy decision, approval, execution result and verification result.
