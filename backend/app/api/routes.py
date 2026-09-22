from uuid import uuid4
from typing import Literal
from fastapi import APIRouter, HTTPException, Query
from ..integrations.providers import PROVIDERS, validate_configuration
from ..telemetry_reports import telemetry_report
from ..notifications import notifications
from ..orchestrator import run_investigation
from ..repository import repo
from ..auth import approver, viewer
from ..conversations import start_conversation, continue_conversation, get_conversation, list_conversations
from ..schemas import ConversationCreate, ConversationMessage
from ..remediation_service import execute_approved_action
from ..schemas import ApprovalDecision, DemoSimulationRequest, IntegrationCreate, InvestigationRequest, NotificationRequest, ReleaseRiskRequest

router = APIRouter(prefix="/api")

@router.get("/healthz")
def healthz(): return {"status":"ok"}

@router.get("/dashboard", dependencies=[viewer])
def dashboard():
    investigations=repo.list_investigations(10); approvals=repo.list_approvals()
    return {"summary":{"open_incidents":sum(1 for i in investigations if i["status"] not in ("resolved","completed")),"pending_approvals":sum(1 for a in approvals if a["status"]=="pending"),"pipeline_risk":"HIGH","platform_status":"Healthy"},"recent_investigations":investigations[:5],"pending_approvals":[a for a in approvals if a["status"]=="pending"][:5]}

@router.post("/investigations", dependencies=[viewer])
def investigate(request: InvestigationRequest):
    inv_id=f"INV-{uuid4().hex[:8].upper()}"; payload=request.model_dump(); payload["investigation_id"]=inv_id
    repo.create_investigation(inv_id,payload); result=run_investigation(payload); repo.save_investigation_result(inv_id,result)
    return {"investigation_id":inv_id,"status":result.get("status"),"result":result}

@router.post("/demo/simulate", dependencies=[viewer])
def simulate_demo(request: DemoSimulationRequest):
    queries = {
        "oom-release": "Simulate checkout-api OOMKilled incidents after a production release with a reduced memory limit.",
        "latency-spike": "Simulate checkout-api latency and 5xx spikes after today's production deployment.",
        "pipeline-failure": "Simulate a checkout-api deployment pipeline failure and investigate the release.",
    }
    created = []
    for _ in range(request.count):
        result = investigate(InvestigationRequest(telemetry_mode="demo", query=queries[request.scenario], application=request.application, environment=request.environment))
        outcome = result["result"]
        created.append({"investigation_id": result["investigation_id"], "status": result["status"], "approval_id": outcome.get("approval_id"), "root_cause": outcome.get("root_cause")})
    return {"scenario": request.scenario, "count": len(created), "incidents": created}

@router.get("/investigations", dependencies=[viewer])
def investigations(): return repo.list_investigations()

@router.get("/investigations/{inv_id}", dependencies=[viewer])
def investigation(inv_id):
    item=repo.get_investigation(inv_id)
    if not item: raise HTTPException(404,"Investigation not found")
    return item

@router.post("/release-risk", dependencies=[viewer])
def release_risk(request: ReleaseRiskRequest):
    return investigate(InvestigationRequest(telemetry_mode="demo", query=f"Assess release risk for {request.application} {request.version}. Changes: {request.changes}",application=request.application,environment=request.environment))

@router.get("/approvals", dependencies=[viewer])
def approvals(): return repo.list_approvals()

@router.post("/approvals/{approval_id}/approve", dependencies=[approver])
def approve(approval_id, decision: ApprovalDecision):
    try:
        result=repo.decide_approval(approval_id,"approved",str(decision.decided_by),decision.comment)
    except ValueError as error:
        raise HTTPException(409, str(error)) from None
    if not result: raise HTTPException(404,"Approval not found")
    result["decided_by"] = str(decision.decided_by)
    result["execution"] = execute_approved_action(result)
    return result

@router.post("/approvals/{approval_id}/reject", dependencies=[approver])
def reject(approval_id, decision: ApprovalDecision):
    try:
        result=repo.decide_approval(approval_id,"rejected",str(decision.decided_by),decision.comment)
    except ValueError as error:
        raise HTTPException(409, str(error)) from None
    if not result: raise HTTPException(404,"Approval not found")
    return result

@router.get("/integrations/providers", dependencies=[viewer])
def providers():
    return [{'provider': name, 'capabilities': p.capabilities(), 'status': p.status,
             'category': p.category, 'description': p.description,
             'configuration_example': p.configuration_example} for name, p in PROVIDERS.items()]
@router.get("/integrations", dependencies=[viewer])
def integrations(): return repo.list_integrations()
@router.post("/integrations", dependencies=[approver])
def add_integration(request: IntegrationCreate):
    if request.provider not in PROVIDERS: raise HTTPException(400,"Unsupported provider")
    try:
        integration_id = repo.add_integration(request.provider, request.name, request.configuration, request.enabled)
    except ValueError as error:
        raise HTTPException(400, str(error)) from None
    return {'id': integration_id, 'status': 'created'}
@router.post("/integrations/test", dependencies=[viewer])
def test_integration(request: IntegrationCreate):
    if request.provider not in PROVIDERS: raise HTTPException(400,"Unsupported provider")
    if PROVIDERS[request.provider].status == 'available':
        try:
            validate_configuration(request.configuration)
        except ValueError as error:
            raise HTTPException(400, str(error)) from None
    return PROVIDERS[request.provider].test_connection(request.configuration)

@router.post('/integrations/{integration_id}/activate', dependencies=[approver])
def activate_integration(integration_id: str):
    try:
        result = repo.activate_integration(integration_id)
    except ValueError as error:
        raise HTTPException(400, str(error)) from None
    if result is None:
        raise HTTPException(404, 'Integration not found')
    return result

@router.get('/reports/telemetry', dependencies=[viewer])
def report_telemetry(application: str = Query(default='checkout-api', min_length=1, max_length=128),
                     environment: Literal['dev', 'test', 'stage', 'prod'] = 'prod',
                     namespace: str = Query(default='aiops-guardian', min_length=1, max_length=128),
                     window_minutes: int = Query(default=30)):
    if window_minutes not in (15, 30, 60):
        raise HTTPException(422, 'window_minutes must be 15, 30, or 60.')
    return telemetry_report({'application': application, 'environment': environment, 'namespace': namespace}, window_minutes)

@router.post("/notifications/email", dependencies=[approver])
def send_email(request: NotificationRequest): return notifications.send_email(str(request.to),request.subject,request.body)

@router.get("/pipelines", dependencies=[viewer])
def pipelines():
    return [{"id":"PIPE-1847","application":"checkout-api","status":"success","risk":"HIGH","version":"v2.0.0"},{"id":"PIPE-1846","application":"checkout-api","status":"success","risk":"LOW","version":"v1.9.0"},{"id":"PIPE-1832","application":"payments-api","status":"failed","risk":"MEDIUM","version":"v5.1.2"}]

# Conversations collect evidence and offer advice; they never execute remediation.

@router.post("/conversations", dependencies=[viewer])
def create_conversation(request: ConversationCreate):
    return start_conversation(request)

@router.get("/conversations", dependencies=[viewer])
def conversations():
    return list_conversations()

@router.get("/conversations/{conversation_id}", dependencies=[viewer])
def conversation(conversation_id: str):
    return get_conversation(conversation_id)

@router.post("/conversations/{conversation_id}/messages", dependencies=[viewer])
def conversation_message(conversation_id: str, request: ConversationMessage):
    return continue_conversation(conversation_id, request)
