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

## Audit
Record user, agent, tool, action, policy decision, approval, execution result and verification result.
