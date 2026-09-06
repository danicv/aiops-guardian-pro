# Langflow

Langflow is the **visual design and experimentation layer**. Production orchestration remains in LangGraph because Guardian requires deterministic state, conditional routing, bounded retries, approval pauses, resumability, and testability.

Reference flow:

```text
Input -> Orchestrator/Intent
      -> Kubernetes + Monitoring + Change
      -> RAG + History
      -> RCA -> Validation -> Adaptive
      -> Risk/Guardrail -> Approval
      -> Remediation -> Verification
```

The JSON in `flows/` is a logical reference because exact Langflow export schemas can vary by release.
