import {useState} from 'react'
import {simulateDemo} from '../api'

export default function Simulator(){
  const [count,setCount]=useState(3)
  const [environment,setEnvironment]=useState('prod')
  const [scenario,setScenario]=useState('oom-release')
  const [loading,setLoading]=useState(false)
  const [result,setResult]=useState<any>(null)
  async function run(){setLoading(true);try{setResult(await simulateDemo({count,environment,scenario,application:'checkout-api'}))}finally{setLoading(false)}}
  return <section><div className="title"><h2>Incident simulator</h2><p>Generate deterministic demo incidents to exercise the investigation and approval workflow.</p></div>
    <div className="grid2"><div className="panel"><h3>Scenario controls</h3>
      <label>Scenario<select value={scenario} onChange={e=>setScenario(e.target.value)}><option value="oom-release">OOM after release</option><option value="latency-spike">Latency and 5xx spike</option><option value="pipeline-failure">Pipeline failure</option></select></label>
      <label>Environment<select value={environment} onChange={e=>setEnvironment(e.target.value)}><option>dev</option><option>test</option><option>stage</option><option>prod</option></select></label>
      <label>Incidents to create<input type="number" min="1" max="10" value={count} onChange={e=>setCount(Math.max(1,Math.min(10,Number(e.target.value)||1)))}/></label>
      <button className="primary" onClick={run} disabled={loading}>{loading?'Simulating…':'Generate incidents'}</button>
      {result&&<div className="notice">Created <strong>{result.count}</strong> {result.scenario} incident{result.count===1?'':'s'}.</div>}
    </div><div className="panel"><h3>Created incidents</h3>{result?.incidents?.map((item:any)=><div className="row" key={item.investigation_id}><div><strong>{item.investigation_id}</strong><small>{item.status}</small></div><span>{item.approval_id?'Approval created':'No approval'}</span></div>)}{!result&&<div className="empty">Choose a scenario and generate demo data.</div>}</div></div>
  </section>
}