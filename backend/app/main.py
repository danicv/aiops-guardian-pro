from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from .api.routes import router
from .config import settings
from .db import init_db

app=FastAPI(title="AIOps Guardian Pro API",version="1.0.0",description="Agentic DevOps, Release & Reliability Intelligence Platform")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(",")],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
@app.on_event("startup")
def startup(): init_db()
@app.get("/")
def root(): return {"product":"AIOps Guardian Pro","message":"Prevent. Resolve. Learn.","docs":"/docs"}
app.include_router(router)
FastAPIInstrumentor.instrument_app(app)
