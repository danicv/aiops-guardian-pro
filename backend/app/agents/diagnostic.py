from .base import AgentResult, BaseAgent

class PipelineAgent(BaseAgent):
    name = "pipeline"
    def execute(self, state):
        return AgentResult(self.name, "Latest pipeline deployed checkout-api v2.0.0.", [
            {"source":"pipeline","signal":"pipeline_id","value":"PIPE-1847"},
            {"source":"pipeline","signal":"version","value":"v2.0.0"}], {"status":"success"})

class ChangeAgent(BaseAgent):
    name = "change"
    def execute(self, state):
        return AgentResult(self.name, "Memory limit changed from 1Gi to 128Mi.", [
            {"source":"git-diff","signal":"memory_before","value":"1Gi"},
            {"source":"git-diff","signal":"memory_after","value":"128Mi"}], {"change":"resources.limits.memory"})

class KubernetesAgent(BaseAgent):
    name = "kubernetes"
    def execute(self, state):
        return AgentResult(self.name, "Pods are restarting and Kubernetes reports OOMKilled.", [
            {"source":"kubernetes","signal":"restarts","value":9},
            {"source":"kubernetes","signal":"termination_reason","value":"OOMKilled"}], {"healthy_replicas":0,"desired_replicas":3})

class MonitoringAgent(BaseAgent):
    name = "monitoring"
    def execute(self, state):
        return AgentResult(self.name, "5xx and p95 latency increased immediately after deployment.", [
            {"source":"prometheus","signal":"http_5xx_pct","before":0.2,"after":6.8},
            {"source":"prometheus","signal":"p95_latency_ms","before":180,"after":690}], {"error_rate":6.8})

class RAGAgent(BaseAgent):
    name = "rag"
    def execute(self, state):
        return AgentResult(self.name, "OOMKilled runbook recommends rollback/restoring validated memory limits.", [
            {"source":"runbook","signal":"document","value":"Kubernetes OOMKilled Recovery Procedure"}], {"recommended_minimum":"768Mi"})

class HistoryAgent(BaseAgent):
    name = "history"
    def execute(self, state):
        return AgentResult(self.name, "Similar incident INC-1024 was caused by an unsafe memory-limit reduction.", [
            {"source":"incident-history","signal":"similar_incident","value":"INC-1024"}], {"resolution":"rollback"})

class RCAAgent(BaseAgent):
    name = "rca"
    def execute(self, state):
        root = ("The latest checkout-api deployment reduced the container memory limit from 1Gi to 128Mi. "
                "The new limit is below application demand, causing OOMKilled terminations, pod restarts, "
                "HTTP 5xx errors, and latency degradation.")
        confidence = 0.97 if len(state.get("evidence", [])) >= 6 else 0.82
        return AgentResult(self.name, root, [], {"root_cause":root,"confidence_score":confidence,"recommended_action":"rollback_deployment","recommended_target":"v1.9.0"})

class ReleaseRiskAgent(BaseAgent):
    name = "release-risk"
    def execute(self, state):
        return AgentResult(self.name, "Release risk is HIGH: 91/100.", [
            {"source":"risk-engine","signal":"risk_score","value":91}], {"risk":"HIGH","risk_score":91,"factors":["Memory limit reduced","Historical incident match","Load test missing"]})

class VerificationAgent(BaseAgent):
    name = "verification"
    def execute(self, state):
        return AgentResult(self.name, "Post-remediation health checks passed.", [
            {"source":"kubernetes","signal":"healthy_replicas","value":"3/3"},
            {"source":"prometheus","signal":"http_5xx_pct","value":0.2}], {"verified":True,"status":"healthy"})
