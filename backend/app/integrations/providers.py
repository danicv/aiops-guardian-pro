from .base import IntegrationProvider

class SimpleProvider(IntegrationProvider):
    def __init__(self, name, caps, required=None):
        self.provider_name = name
        self._caps = caps
        self.required = required or []
    def test_connection(self, config):
        ok = all(config.get(k) for k in self.required)
        return {"ok": ok, "provider": self.provider_name, "message": "Configuration validated." if ok else f"Missing required fields: {self.required}"}
    def capabilities(self):
        return self._caps
    def execute(self, operation, params, config):
        if operation not in self._caps:
            raise ValueError(f"Unsupported operation: {operation}")
        return {"provider": self.provider_name, "operation": operation, "status": "adapter-ready", "params": params}

PROVIDERS = {
    "github": SimpleProvider("github", ["get_commit","get_pull_request","get_workflow_run","compare_releases"], ["repo"]),
    "azure-devops": SimpleProvider("azure-devops", ["get_pipeline","get_build_logs","get_test_results","get_release"], ["organization","project"]),
    "gitlab": SimpleProvider("gitlab", ["get_pipeline","get_job_log","compare_commits"], ["project"]),
    "servicenow": SimpleProvider("servicenow", ["create_incident","get_incident","add_work_note"], ["instance"]),
    "prometheus": SimpleProvider("prometheus", ["query","query_range"], ["url"]),
    "webhook": SimpleProvider("webhook", ["send_webhook"], ["url"]),
}
