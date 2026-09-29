import sys
from types import ModuleType

from app.config import settings
from app import langfuse_tracing
from app.langfuse_tracing import create_langfuse_callback, flush_langfuse_callback
from app import orchestrator


def test_langfuse_is_disabled_by_default(monkeypatch):
    monkeypatch.setattr(settings, "langfuse_enabled", False)
    assert create_langfuse_callback() is None


def test_enabled_without_all_credentials_is_a_noop(monkeypatch):
    monkeypatch.setattr(settings, "langfuse_enabled", True)
    monkeypatch.setattr(settings, "langfuse_host", "http://langfuse.internal")
    monkeypatch.setattr(settings, "langfuse_public_key", "")
    monkeypatch.setattr(settings, "langfuse_secret_key", "")
    assert create_langfuse_callback() is None


def test_callback_uses_self_hosted_project_credentials(monkeypatch):
    captured = {}
    monkeypatch.setattr(langfuse_tracing, "_client", None)
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

    class CallbackHandler:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    class LangfuseClient:
        def __init__(self, **kwargs):
            captured["client"] = kwargs

    langfuse_module = ModuleType("langfuse")
    langfuse_module.Langfuse = LangfuseClient
    langchain_module = ModuleType("langfuse.langchain")
    langchain_module.CallbackHandler = CallbackHandler
    langfuse_module.langchain = langchain_module
    monkeypatch.setitem(sys.modules, "langfuse", langfuse_module)
    monkeypatch.setitem(sys.modules, "langfuse.langchain", langchain_module)
    monkeypatch.setattr(settings, "langfuse_enabled", True)
    monkeypatch.setattr(settings, "langfuse_host", "http://langfuse.internal/")
    monkeypatch.setattr(settings, "langfuse_public_key", "pk-test")
    monkeypatch.setattr(settings, "langfuse_secret_key", "sk-test")

    callback = create_langfuse_callback()

    assert isinstance(callback, CallbackHandler)
    assert captured == {
        "public_key": "pk-test",
        "client": {
            "public_key": "pk-test",
            "secret_key": "sk-test",
            "host": "http://langfuse.internal",
            "environment": settings.app_env,
        },
    }
    assert __import__("os").environ["LANGFUSE_HOST"] == "http://langfuse.internal"
    assert __import__("os").environ["LANGFUSE_SECRET_KEY"] == "sk-test"


def test_flush_is_optional_and_failure_does_not_raise(caplog):
    flush_langfuse_callback(None)

    class BrokenClient:
        def flush(self):
            raise RuntimeError("offline")

    class BrokenCallback:
        client = BrokenClient()

    flush_langfuse_callback(BrokenCallback())
    assert "Could not flush Langfuse" in caplog.text


def test_demo_graph_receives_and_flushes_langfuse_callback(monkeypatch):
    callback = object()
    flushed = []
    invocations = []

    class Graph:
        def invoke(self, state, config):
            invocations.append((state, config))
            return {"status": "awaiting_approval"}

    monkeypatch.setattr(orchestrator, "graph", Graph())
    monkeypatch.setattr(orchestrator, "create_langfuse_callback", lambda: callback)
    monkeypatch.setattr(orchestrator, "flush_langfuse_callback", flushed.append)
    result = orchestrator.run_investigation({
        "telemetry_mode": "demo", "investigation_id": "INV-LANGFUSE",
        "query": "Investigate checkout-api", "application": "checkout-api",
        "environment": "prod", "namespace": "aiops-guardian",
    })

    assert result["investigation_id"] == "INV-LANGFUSE"
    assert invocations[0][1]["callbacks"] == [callback]
    assert invocations[0][1]["metadata"]["investigation_id"] == "INV-LANGFUSE"
    assert flushed == [callback]