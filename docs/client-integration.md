# Client Integration Hub

A client should be able to connect existing tools without modifying the agent core.

## Integration patterns

1. **MCP** for standardized agent tool/resource access.
2. **REST APIs** for generic request/response integration.
3. **Webhooks** for events such as pipeline completion, deployment, alerts, incidents and approvals.
4. **Native adapters** for frequently used enterprise platforms.

## Provider abstraction

```text
Agent
  |
MCP / Integration Service
  |
IntegrationProvider interface
  |-- GitHubProvider
  |-- AzureDevOpsProvider
  |-- GitLabProvider
  |-- ServiceNowProvider
  |-- PrometheusProvider
  |-- WebhookProvider
```

Each provider implements:

```python
test_connection(config)
capabilities()
execute(operation, params, config)
```

This lets the Pipeline Agent ask for `get_pipeline` without caring whether the client uses GitHub Actions, Azure DevOps or GitLab.

## Client onboarding UX

```text
Settings -> Integrations -> Add Integration
-> Select Provider
-> Authenticate/configure endpoint
-> Test Connection
-> Scope capabilities/environment
-> Save
```

## Target connectors

- CI/CD: GitHub Actions, Azure DevOps, GitLab, Jenkins, Bitbucket, Harness
- ITSM: ServiceNow, Jira Service Management
- Incident: PagerDuty, Opsgenie
- Collaboration: Teams, Slack, Email
- Observability: Prometheus, Grafana, Azure Monitor, Splunk, Datadog, New Relic
- Runtime: AKS, EKS, GKE, generic Kubernetes

## Credentials

The sample API strips obvious token/password/secret fields from persisted integration metadata. Production should use OAuth where possible, Azure Key Vault, Workload Identity, encrypted connection metadata, rotation, and least-privilege scopes.
