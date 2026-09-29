import {useQuery} from '@tanstack/react-query'
import {Link, useParams} from 'react-router-dom'
import {ArrowLeft, ArrowRight, BadgeCheck, CircleAlert, Database, Gauge, ShieldAlert, Sparkles} from 'lucide-react'
import {getInvestigation, requestError} from '../api'

function EvidenceList({items=[]}:{items:any[]}) {
  if(!items.length) return <div className="empty">No evidence items were attached to this investigation.</div>
  return <div className="incident-evidence-list">
    {items.map((item:any,index:number)=><article className="incident-evidence" key={`${item.source}-${item.signal}-${index}`}>
      <div><span className="source-chip"><Database size={12}/>{item.source||'unknown source'}</span>{item.synthetic&&<span className="case-status">Synthetic</span>}</div>
      <strong>{item.signal||'Observation'}</strong>
      <p>{item.value ?? (item.after!==undefined ? `${item.before ?? '—'} → ${item.after}` : 'No value reported')}</p>
      {item.error&&<small>{item.error}</small>}
    </article>)}
  </div>
}

export default function InvestigationDetail() {
  const {investigationId=''}=useParams()
  const investigation=useQuery({queryKey:['investigation',investigationId],queryFn:()=>getInvestigation(investigationId),enabled:Boolean(investigationId),retry:false})
  if(investigation.isLoading) return <section className="panel empty">Loading investigation…</section>
  if(investigation.isError||!investigation.data) return <section><Link className="text-link" to="/investigations"><ArrowLeft size={15}/> Back to investigations</Link><div className="notice conversation-error" role="alert">{requestError(investigation.error,'Investigation not found.')}</div></section>

  const item=investigation.data
  const result=item.result||{}
  const simulated=result.telemetry_mode==='demo'||Boolean(result.telemetry_notice?.toLowerCase().includes('simulated'))
  const metricList=result.sre_metrics||[]
  const similar=result.similar_incidents||[]

  return <section className="investigation-detail">
    <Link className="text-link back-link" to="/investigations"><ArrowLeft size={15}/> All investigations</Link>
    <header className="incident-detail-hero">
      <div>
        <div className="eyebrow"><CircleAlert size={14}/> INCIDENT RECORD</div>
        <h2>{item.application} investigation</h2>
        <p>{item.query}</p>
        <div className="incident-meta"><code>{item.id}</code><span>{item.environment}</span><span>{item.status?.replaceAll('_',' ')}</span><span>{item.created_at?new Date(item.created_at).toLocaleString():''}</span></div>
      </div>
      <div className="incident-confidence"><span>RCA confidence</span><strong>{item.confidence?`${Math.round(item.confidence*100)}%`:'—'}</strong><small>{simulated?'Demo analysis':'Investigation snapshot'}</small></div>
    </header>
    {simulated&&<div className="notice"><Sparkles size={15}/> This investigation uses synthetic demo signals. It is not a measurement of a live service.</div>}
    <div className="incident-summary-grid">
      <article className="panel"><div className="panel-kicker">WORKING HYPOTHESIS</div><h3>{result.root_cause||item.root_cause||'No root-cause hypothesis recorded yet.'}</h3><p>Correlate this explanation with the evidence below before treating it as confirmed.</p></article>
      <article className="panel"><div className="panel-kicker">GUARDRAIL DECISION</div><div className="detail-guardrail"><ShieldAlert size={18}/><strong>{result.guardrail?.decision||'No action decision'}</strong></div><p>{result.guardrail?.reason||'No guardrail reason was recorded.'}</p>{result.recommended_action&&<div className="recommended-action"><small>Recommended action</small><strong>{result.recommended_action} → {result.recommended_target||'review'}</strong></div>}{result.approval_id&&<Link className="panel-action" to="/approvals">Review approval {result.approval_id} <ArrowRight size={14}/></Link>}</article>
    </div>
    <article className="panel detail-section">
      <div className="panelhead"><div><div className="panel-kicker">OBSERVATIONS</div><h3>Evidence attached to this investigation</h3></div><span className="source-chip">{metricList.length} metric checks</span></div>
      <p className="evidence-note">Evidence is scoped to this investigation. Unknown or missing readings are not treated as healthy.</p>
      <EvidenceList items={result.evidence||[]}/>
      {metricList.length>0&&<div className="detail-metrics">{metricList.map((metric:any,index:number)=><div className="metric" key={`${metric.name}-${index}`}><div><strong><Gauge size={14}/> {metric.name}</strong><small>{metric.value??'Unknown'} · baseline {metric.baseline??'not provided'}</small>{metric.observed_at&&<small>Observed {metric.observed_at}</small>}{metric.error&&<p>{metric.error}</p>}</div><span className={`risk ${metric.status||'unknown'}`}>{metric.status||'unknown'}</span>{metric.query&&<code>{metric.query}</code>}</div>)}</div>}
    </article>
    {similar.length>0&&<article className="panel detail-section"><div className="panelhead"><div><div className="panel-kicker">COMPARATIVE CONTEXT</div><h3>Similar incident patterns</h3></div><span className="case-status">Synthetic precedents</span></div><p className="evidence-note">These cases are training/history references, not evidence that the same cause occurred here.</p><div className="related-case-list">{similar.map((caseItem:any)=><article className="related-case" key={caseItem.case_id}><div><span>{caseItem.case_id}</span><span className="case-status">{caseItem.severity}</span></div><strong>{caseItem.title}</strong><p>{caseItem.root_cause}</p><small>Matched: {(caseItem.matched_terms||caseItem.tags||[]).slice(0,6).join(', ')}</small><details><summary>Remediation and verification</summary><ol>{(caseItem.remediation||[]).map((step:string,index:number)=><li key={`action-${index}`}>{step}</li>)}</ol><strong>Recovery checks</strong><ul>{(caseItem.verification||[]).map((step:string,index:number)=><li key={`verify-${index}`}>{step}</li>)}</ul></details></article>)}</div></article>}
    <div className="detail-lower-grid">
      <article className="panel detail-section"><div className="panel-kicker">AGENT TRACE</div><h3>How Guardian reached this result</h3>{(result.agent_trace||[]).length?(result.agent_trace||[]).map((step:any,index:number)=><div className="trace" key={`${step.agent}-${index}`}><span>{index+1}</span><div><strong>{step.agent}</strong><p>{step.summary}</p></div></div>):<div className="empty">No agent execution trace was stored.</div>}</article>
      <article className="panel detail-section"><div className="panel-kicker">NEXT STEPS</div><h3>SRE action plan</h3>{(result.action_plan||[]).length?(result.action_plan||[]).map((step:any,index:number)=><div className="plan-step" key={`${step.step}-${index}`}><strong>{step.step}</strong><p>{step.instruction}</p><small>{step.owner&&`Owner: ${step.owner}`}</small></div>):<p>No structured action plan was recorded. Review the live evidence and runbook before deciding.</p>}{result.instrumentation?.length>0&&<><div className="panel-kicker instrumentation-kicker">INSTRUMENTATION</div>{result.instrumentation.map((entry:any,index:number)=><p className="detail-instrument" key={`${entry.name}-${index}`}><BadgeCheck size={14}/><span><strong>{entry.name}:</strong> {entry.instruction}</span></p>)}</>}</article>
    </div>
  </section>
}
