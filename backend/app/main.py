from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from .api.routes import router
from .config import settings
from .db import init_db
from .redaction import install_log_redaction
from .conversations import purge_expired_conversations
import asyncio
from contextlib import suppress

install_log_redaction()

app=FastAPI(title="AIOps Guardian Pro API",version="1.0.0",description="Agentic DevOps, Release & Reliability Intelligence Platform")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(",")],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
@app.on_event("startup")
async def startup():
    init_db()
    await asyncio.to_thread(purge_expired_conversations)
    async def cleanup():
        while True:
            await asyncio.sleep(settings.conversation_cleanup_seconds)
            try:
                await asyncio.to_thread(purge_expired_conversations)
            except Exception:
                # Never include database exceptions or SQL parameters in logs.
                import logging
                logging.getLogger(__name__).error('Conversation retention cleanup failed; retry scheduled.')
    app.state.retention_task = asyncio.create_task(cleanup())

@app.on_event("shutdown")
async def shutdown():
    app.state.retention_task.cancel()
    with suppress(asyncio.CancelledError):
        await app.state.retention_task
@app.get("/")
def root(): return {"product":"AIOps Guardian Pro","message":"Prevent. Resolve. Learn.","docs":"/docs"}
app.include_router(router)
# Automatic HTTP spans can contain URL parameters, headers and exception details.
# Decision-support mode exports only the explicit application spans.
if not settings.decision_support_only:
    FastAPIInstrumentor.instrument_app(app)
