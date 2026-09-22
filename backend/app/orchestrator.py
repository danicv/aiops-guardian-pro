from typing import Any, TypedDict
from uuid import uuid4
from langgraph.graph import END, StateGraph
from .agents.diagnostic import PipelineAgent, ChangeAgent, KubernetesAgent, MonitoringAgent, RAGAgent, HistoryAgent, RCAAgent, ReleaseRiskAgent, VerificationAgent
from .evaluation import evaluate_response
from .guardrails import evaluate_action, validate_rca
from .notifications import notifications
from .repository import repo
from .telemetry import tracer
from .live_telemetry import investigate_live

class GuardianState(TypedDict, total=False):
    investigation_id: str
    query: str
    application: str
    environment: str
    namespace: str
    intent: str
    plan: list[str]
    evidence: list[dict[str, Any]]
    agent_trace: list[dict[str, Any]]
    sre_metrics: list[dict[str, Any]]
    action_plan: list[dict[str, Any]]
    instrumentation: list[dict[str, Any]]
    telemetry_notice: str
    root_cause: str
    confidence_score: float
    validation: dict[str, Any]
    adaptive_action: str
    recommended_action: str
    recommended_target: str
    risk: str
    guardrail: dict[str, Any]
    approval_id: str
    status: str
    verification: dict[str, Any]
    evaluation: dict[str, Any]

pipeline = PipelineAgent(); change = ChangeAgent(); k8s = KubernetesAgent(); monitoring = MonitoringAgent()
rag = RAGAgent(); history = HistoryAgent(); rca = RCAAgent(); release_risk = ReleaseRiskAgent(); verification = VerificationAgent()

def append_result(state, result):
    return {
        "evidence": list(state.get("evidence", [])) + list(result.evidence),
        "agent_trace": list(state.get("agent_trace", [])) + [{"agent": result.agent, "summary": result.summary, "data": result.data}],
    }

def plan_node(state):
    q = state["query"].lower()
    if "pipeline" in q or "build" in q:
        intent, plan = "pipeline_investigation", ["pipeline","change","rca","validation"]
    elif "risk" in q or "safe to promote" in q or "release risk" in q:
        intent, plan = "release_risk", ["pipeline","change","release-risk"]
    else:
        intent, plan = "runtime_incident", ["kubernetes","monitoring","change","rag","history","rca","validation"]
    return {"intent": intent, "plan": plan, "agent_trace": [{"agent":"orchestrator","summary":f"Intent={intent}; dynamic plan={plan}","data":{"plan":plan}}]}

def collect_node(state):
    if state["intent"] == "pipeline_investigation": agents = [pipeline, change]
    elif state["intent"] == "release_risk": agents = [pipeline, change]
    else: agents = [k8s, monitoring, change, rag, history]
    evidence = list(state.get("evidence", [])); trace = list(state.get("agent_trace", [])); temp = dict(state)
    for agent in agents:
        result = agent.run(temp)
        evidence.extend(result.evidence); trace.append({"agent":result.agent,"summary":result.summary,"data":result.data})
        temp["evidence"] = evidence
    return {"evidence": evidence, "agent_trace": trace}

def analyze_node(state):
    if state["intent"] == "release_risk":
        result = release_risk.run(state)
        upd = append_result(state, result)
        upd.update({"root_cause":result.summary,"confidence_score":0.92,"recommended_action":"review_release","risk":result.data["risk"]})
        return upd
    result = rca.run(state); upd = append_result(state, result); upd.update(result.data); return upd

def validate_node(state):
    ok, reason = validate_rca(state.get("confidence_score",0.0), len(state.get("evidence",[])))
    trace = list(state.get("agent_trace", [])) + [
        {"agent":"validation","summary":reason,"data":{"is_sufficient":ok}},
        {"agent":"adaptive","summary":"accept_diagnosis" if ok else "retrieve_more_evidence","data":{}}
    ]
    return {"validation":{"is_sufficient":ok,"reason":reason},"adaptive_action":"accept_diagnosis" if ok else "retrieve_more_evidence","agent_trace":trace}

def validation_route(state): return "risk" if state["validation"]["is_sufficient"] else "more"

def more_node(state):
    extra={"source":"adaptive-investigation","signal":"deployment_timing","value":"errors began 2 minutes after release"}
    return {"evidence":list(state.get("evidence",[]))+[extra],"validation":{"is_sufficient":True,"reason":"Additional timing evidence collected."},"adaptive_action":"accept_diagnosis","agent_trace":list(state.get("agent_trace",[]))+[{"agent":"adaptive","summary":"Collected additional deployment timing evidence.","data":extra}]}

def risk_node(state):
    if state.get("recommended_action") == "review_release":
        g={"decision":"REQUIRE_APPROVAL","risk":state.get("risk","HIGH"),"reason":"High-risk release requires human approval.","approval_required":True}
        return {"guardrail":g,"risk":g["risk"]}
    decision=evaluate_action(state.get("recommended_action","unknown"),state["environment"])
    return {"risk":decision.risk,"guardrail":{"decision":decision.decision,"risk":decision.risk,"reason":decision.reason,"approval_required":decision.approval_required}}

def guardrail_route(state):
    if state["guardrail"]["decision"] == "BLOCK": return "blocked"
    if state["guardrail"]["approval_required"]: return "approval"
    return "remediate"

def approval_node(state):
    aid=repo.create_approval(state["investigation_id"],state.get("recommended_action","review_release"),state["environment"],state.get("risk","HIGH"))
    notice=notifications.send_approval_request(aid,state["investigation_id"],state.get("recommended_action","review_release"),state.get("risk","HIGH"))
    return {"approval_id":aid,"status":"awaiting_approval","agent_trace":list(state.get("agent_trace",[]))+[{"agent":"notification","summary":"Approval created; email notification attempted.","data":{"approval_id":aid,"notification":notice}}]}

def remediation_node(state):
    return {"status":"remediated","agent_trace":list(state.get("agent_trace",[]))+[{"agent":"remediation","summary":"Governed action executed through Action MCP (demo implementation).","data":{"action":state.get("recommended_action"),"target":state.get("recommended_target")}}]}

def verification_node(state):
    result=verification.run(state); upd=append_result(state,result); upd.update({"verification":result.data,"status":"resolved" if result.data.get("verified") else "verification_failed"}); return upd

def blocked_node(state): return {"status":"blocked"}
def eval_node(state): return {"evaluation":evaluate_response(state)}

builder=StateGraph(GuardianState)
for name, fn in [("plan",plan_node),("collect",collect_node),("analyze",analyze_node),("validate",validate_node),("more",more_node),("risk",risk_node),("approval",approval_node),("remediate",remediation_node),("verify",verification_node),("blocked",blocked_node),("evaluate",eval_node)]: builder.add_node(name,fn)
builder.set_entry_point("plan"); builder.add_edge("plan","collect"); builder.add_edge("collect","analyze"); builder.add_edge("analyze","validate")
builder.add_conditional_edges("validate",validation_route,{"risk":"risk","more":"more"}); builder.add_edge("more","risk")
builder.add_conditional_edges("risk",guardrail_route,{"blocked":"blocked","approval":"approval","remediate":"remediate"})
builder.add_edge("blocked","evaluate"); builder.add_edge("approval","evaluate"); builder.add_edge("remediate","verify"); builder.add_edge("verify","evaluate"); builder.add_edge("evaluate",END)
graph=builder.compile()

def run_investigation(payload):
    inv_id=payload.get("investigation_id") or f"INV-{uuid4().hex[:8].upper()}"
    initial={"investigation_id":inv_id,"query":payload["query"],"application":payload.get("application","checkout-api"),"environment":payload.get("environment","prod"),"namespace":payload.get("namespace","default"),"evidence":[],"agent_trace":[],"status":"running"}
    with tracer.start_as_current_span("incident.request"):
        if payload.get("telemetry_mode", "live") == "live":
            result = {**initial, **investigate_live(initial), "telemetry_mode": "live"}
        else:
            result = graph.invoke(initial)
            result["telemetry_mode"] = "demo"
            result.setdefault("telemetry_notice", "Simulated demo: release and diagnostic evidence are sample data, not live observations.")
    result["investigation_id"]=inv_id
    return result
