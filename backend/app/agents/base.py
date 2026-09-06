from dataclasses import dataclass, field
from typing import Any
from ..telemetry import tracer

@dataclass
class AgentResult:
    agent: str
    summary: str
    evidence: list[dict[str, Any]] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)

class BaseAgent:
    name = "base"
    def run(self, state):
        with tracer.start_as_current_span(f"agent.{self.name}"):
            return self.execute(state)
    def execute(self, state):
        raise NotImplementedError
