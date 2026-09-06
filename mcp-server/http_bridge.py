from fastapi import FastAPI
from pydantic import BaseModel
from tools import k8s_get_pods,k8s_get_events,get_pipeline,find_similar_incident,rollback_deployment
app=FastAPI(title="AIOps Guardian MCP HTTP Demo Bridge")
@app.get("/healthz")
def health(): return {"status":"ok","note":"FastMCP server is defined in server.py"}
@app.get("/tools/k8s/pods")
def pods(namespace="default",app_name="checkout-api"): return k8s_get_pods(namespace,app_name)
@app.get("/tools/k8s/events")
def events(namespace="default",app_name="checkout-api"): return k8s_get_events(namespace,app_name)
@app.get("/tools/pipeline/{pipeline_id}")
def pipeline(pipeline_id): return get_pipeline(pipeline_id)
@app.get("/tools/incidents/similar")
def similar(application="checkout-api"): return find_similar_incident(application)
class ActionRequest(BaseModel):
    namespace:str="default"; deployment:str="checkout-api"; target_version:str="v1.9.0"
@app.post("/tools/action/rollback")
def rollback(req:ActionRequest): return rollback_deployment(req.namespace,req.deployment,req.target_version)
