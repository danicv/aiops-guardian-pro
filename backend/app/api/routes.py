from uuid import uuid4
from fastapi import APIRouter, HTTPException
from ..integrations.providers import PROVIDERS
from ..notifications import notifications
from ..orchestrator import run_investigation
from ..repository import repo
from ..remediation_service import execute_approved_action
from ..schemas import ApprovalDecision, IntegrationCreate, InvestigationRequest, NotificationRequest, ReleaseRiskRequest

router = APIRouter(prefix="/api")

@router.get("/healthz")
def healthz(): return {"status":"ok"}

@router.get("/dashboard")
def dashboard():
    investigations=repo.list_investigations(10); approvals=repo.list_approvals()
    return {"summary":{"open_incidents":sum(1 for i in investigations if i["status"] not in ("resolved","completed")),"pending_approvals":sum(1 for a in approvals if a["status"]=="pending"),"pipeline_risk":"HIGH","platform_status":"Healthy"},"recent_investigations":investigations[:5],"pending_approvals":[a for a in approvals if a["status"]=="pending"][:5]}

@router.post("/investigations")
def investigate(request: InvestigationRequest):
    inv_id=f"INV-{uuid4().hex[:8].upper()}"; payload=request.model_dump(); payload["investigation_id"]=inv_id
    repo.create_investigation(inv_id,payload); result=run_investigation(payload); repo.save_investigation_result(inv_id,result)
    return {"investigation_id":inv_id,"status":result.get("status"),"result":result}

@router.get("/investigations")
def investigations(): return repo.list_investigations()

@router.get("/investigations/{inv_id}")
def investigation(inv_id):
    item=repo.get_investigation(inv_id)
    if not item: raise HTTPException(404,"Investigation not found")
    return item

@router.post("/release-risk")
def release_risk(request: ReleaseRiskRequest):
    return investigate(InvestigationRequest(query=f"Assess release risk for {request.application} {request.version}. Changes: {request.changes}",application=request.application,environment=request.environment))

@router.get("/approvals")
def approvals(): return repo.list_approvals()

@router.post("/approvals/{approval_id}/approve")
def approve(approval_id, decision: ApprovalDecision):
    result=repo.decide_approval(approval_id,"approved",str(decision.decided_by),decision.comment)
    if not result: raise HTTPException(404,"Approval not found")
    result["decided_by"] = str(decision.decided_by)
    result["execution"] = execute_approved_action(result)
    return result

@router.post("/approvals/{approval_id}/reject")
def reject(approval_id, decision: ApprovalDecision):
    result=repo.decide_approval(approval_id,"rejected",str(decision.decided_by),decision.comment)
    if not result: raise HTTPException(404,"Approval not found")
    return result

@router.get("/integrations/providers")
def providers(): return [{"provider":name,"capabilities":p.capabilities()} for name,p in PROVIDERS.items()]
@router.get("/integrations")
def integrations(): return repo.list_integrations()
@router.post("/integrations")
def add_integration(request: IntegrationCreate):
    if request.provider not in PROVIDERS: raise HTTPException(400,"Unsupported provider")
    return {"id":repo.add_integration(request.provider,request.name,request.configuration,request.enabled),"status":"created"}
@router.post("/integrations/test")
def test_integration(request: IntegrationCreate):
    if request.provider not in PROVIDERS: raise HTTPException(400,"Unsupported provider")
    return PROVIDERS[request.provider].test_connection(request.configuration)

@router.post("/notifications/email")
def send_email(request: NotificationRequest): return notifications.send_email(str(request.to),request.subject,request.body)

@router.get("/pipelines")
def pipelines():
    return [{"id":"PIPE-1847","application":"checkout-api","status":"success","risk":"HIGH","version":"v2.0.0"},{"id":"PIPE-1846","application":"checkout-api","status":"success","risk":"LOW","version":"v1.9.0"},{"id":"PIPE-1832","application":"payments-api","status":"failed","risk":"MEDIUM","version":"v5.1.2"}]
