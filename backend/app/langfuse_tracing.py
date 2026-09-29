"""Optional Langfuse callback wiring for LangChain and LangGraph."""
import logging
import os
from threading import Lock

from .config import settings

logger = logging.getLogger(__name__)
_client = None
_client_lock = Lock()


def create_langfuse_callback():
    if not settings.langfuse_enabled:
        return None
    if not all((settings.langfuse_host, settings.langfuse_public_key, settings.langfuse_secret_key)):
        logger.warning("Langfuse is enabled but host or project credentials are missing; tracing is disabled.")
        return None
    try:
        os.environ.setdefault("LANGFUSE_HOST", settings.langfuse_host.rstrip("/"))
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.langfuse_public_key)
        os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.langfuse_secret_key)
        from langfuse import Langfuse
        from langfuse.langchain import CallbackHandler
    except ImportError:
        logger.exception("Langfuse tracing is enabled but the Langfuse SDK is unavailable.")
        return None
    try:
        global _client
        if _client is None:
            with _client_lock:
                if _client is None:
                    _client = Langfuse(
                        public_key=settings.langfuse_public_key,
                        secret_key=settings.langfuse_secret_key,
                        host=settings.langfuse_host.rstrip("/"),
                        environment=settings.app_env,
                    )
        return CallbackHandler(
            public_key=settings.langfuse_public_key,
        )
    except Exception:
        logger.exception("Could not initialize the Langfuse callback; continuing without Langfuse tracing.")
        return None


def flush_langfuse_callback(callback):
    if callback is None:
        return
    client = getattr(callback, "client", None)
    flush = getattr(client, "flush", None) or getattr(callback, "flush", None)
    if callable(flush):
        try:
            flush()
        except Exception:
            logger.exception("Could not flush Langfuse trace events.")