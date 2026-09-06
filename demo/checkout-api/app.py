import os
from fastapi import FastAPI
app=FastAPI(); VERSION=os.getenv("VERSION","v1.9.0")
@app.get("/health")
def health(): return {"status":"ok","version":VERSION}
@app.get("/checkout")
def checkout(): return {"status":"accepted","version":VERSION}
