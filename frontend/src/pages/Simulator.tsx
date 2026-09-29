import {useState} from 'react'
import {useMutation,useQuery,useQueryClient} from '@tanstack/react-query'
import {Link} from 'react-router-dom'
import {ArrowRight} from 'lucide-react'
import {BookOpenCheck, Database, Play, RefreshCw, ShieldAlert, Sparkles} from 'lucide-react'
import {getDemoCaseLibrary, getInvestigations, requestError, seedDemoCaseLibrary, simulateDemo} from '../api'

const categoryNames:Record<string,string>={
  'application-latency':'App latency','application-errors':'App errors','kubernetes':'Kubernetes','database':'Database','messaging':'Queues & streaming','networking':'Networking','pipeline':'CI/CD pipeline','deployment':'Deployments','security':'Security','observability':'Observability',
}

export default function Simulator(){
  const queryClient=useQueryClient()
  const [count,setCount]=useState(3)
  const [environment,setEnvironment]=useState('prod')
  const [scenario,setScenario]=useState('oom-release')
  const [result,setResult]=useState<any>(null)
  const library=useQuery({queryKey:['demo-case-library'],queryFn:getDemoCaseLibrary})
  const recent=useQuery({queryKey:['investigations'],queryFn:getInvestigations})
  const seed=useMutation({mutationFn:seedDemoCaseLibrary,onSuccess:async()=>{await queryClient.invalidateQueries({queryKey:['demo-case-library']})}})
  const run=useMutation({mutationFn:()=>simulateDemo({count,environment,scenario,application:'checkout-api'}),onSuccess:async value=>{setResult(value);await Promise.all([queryClient.invalidateQueries({queryKey:['demo-case-library']}),queryClient.invalidateQueries({queryKey:['investigations']}),queryClient.invalidateQueries({queryKey:['dashboard']})])}})
  const cases=library.data
  const latestCases=recent.data?.slice(0,5)||[]
  return <section className="simulator-page">
    <div className="title"><div className="eyebrow"><Sparkles size={14}/> SRE TRAINING LAB</div><h2>Practice on incidents. Learn from patterns.</h2><p>Explore a labeled synthetic case library, then generate a live incident workflow without touching production systems.</p></div>
    <div className="simulator-overview">
      <article className="panel corpus-panel"><div className="corpus-icon"><BookOpenCheck size={19}/></div><div className="panel-kicker">REASONING CORPUS</div><strong className="corpus-count">{cases?.count??'—'} <small>cases</small></strong><p>{cases?.synthetic_count??0} synthetic cases are available as historical context. Guardian labels them as examples, never as observations from your service.</p>
        <div className="case-category-grid">{Object.entries(cases?.categories||{}).map(([key,value])=><div key={key}><span>{categoryNames[key]||key}</span><strong>{value}</strong></div>)}</div>
        {cases?.seeding_enabled ? <button className="secondary-action" disabled={seed.isPending} onClick={()=>seed.mutate()}><Database size={15}/>{seed.isPending?'Loading library…':cases.count?'Refresh demo library':'Load demo case library'}</button> : <small className="muted-note">Seeding is disabled in this deployment.</small>}
        {seed.isError&&<div className="notice conversation-error" role="alert">{requestError(seed.error,'Unable to seed demo cases.')}</div>}
        {seed.isSuccess&&<div className="notice">Added <strong>{seed.data.inserted}</strong> synthetic cases. Total: {seed.data.total}.</div>}
      </article>
      <article className="panel simulator-controls"><div className="panel-kicker">SCENARIO RUNNER</div><h3>Create a practice incident</h3><p>Runs the investigation, evidence, guardrail, and approval path. Generated records are labeled demo.</p>
        <label>Scenario<select value={scenario} onChange={e=>setScenario(e.target.value)}><option value="oom-release">OOM after release</option><option value="latency-spike">Latency and 5xx spike</option><option value="pipeline-failure">Pipeline failure</option></select></label>
        <div className="form2"><label>Environment<select value={environment} onChange={e=>setEnvironment(e.target.value)}><option>dev</option><option>test</option><option>stage</option><option>prod</option></select></label><label>Incidents<input type="number" min="1" max="10" value={count} onChange={e=>setCount(Math.max(1,Math.min(10,Number(e.target.value)||1)))}/></label></div>
        <button className="primary" onClick={()=>run.mutate()} disabled={run.isPending}><Play size={15}/>{run.isPending?'Running scenario…':'Run scenario'}</button>
        {run.isError&&<div className="notice conversation-error" role="alert">{requestError(run.error,'Scenario could not run.')}</div>}
        {run.isPending&&<div className="sim-progress" role="status"><RefreshCw size={15} className="spin"/> Collecting signals, comparing cases, and applying guardrails…</div>}
      </article>
    </div>
    {result&&<div className="panel simulation-results"><div className="panelhead"><div><div className="panel-kicker">RUN COMPLETE</div><h3>Generated practice incidents</h3></div><span className="source-chip"><ShieldAlert size={13}/> Synthetic demo</span></div><div className="sim-result-grid">{result.incidents.map((item:any)=><article className="sim-result" key={item.investigation_id}><div><Link className="incident-link" to={`/investigations/${encodeURIComponent(item.investigation_id)}`}>{item.investigation_id}<ArrowRight size={13}/></Link><span className="case-status">{item.status}</span></div><p>{item.root_cause}</p><small>{item.approval_id?`Approval ${item.approval_id} is waiting for review.`:'No approval required for this outcome.'}</small></article>)}</div></div>}
    <div className="panel corpus-recent"><div className="panelhead"><div><div className="panel-kicker">RECENT TRAINING RUNS</div><h3>Investigation history</h3></div><span className="source-chip"><Database size={13}/>{latestCases.length} shown</span></div>{latestCases.length?latestCases.map((item:any)=><div className="row" key={item.id}><div><Link className="incident-link" to={`/investigations/${encodeURIComponent(item.id)}`}>{item.id}<ArrowRight size={13}/></Link><small>{item.application} · {item.environment}</small></div><span>{item.status}</span><span>{item.confidence?`${Math.round(item.confidence*100)}%`:'—'}</span></div>):<div className="empty">Seed the case library or run a scenario to start building the training history.</div>}</div>
  </section>
}
