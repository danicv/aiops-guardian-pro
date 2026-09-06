# AKS / Kubernetes manifests

- Replace `YOUR_ACR` and `guardian.example.com`.
- Use Key Vault CSI / Workload Identity for real secrets.
- `postgres-demo.yaml` satisfies the capstone request for PostgreSQL in a separate container; use managed PostgreSQL for production.
- Backend and MCP deployments explicitly demonstrate the requested **OpenTelemetry Collector sidecar container**.
- In production, separate read MCP and action MCP service accounts/RBAC.
