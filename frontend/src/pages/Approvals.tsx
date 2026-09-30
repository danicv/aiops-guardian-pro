import {useQuery, useQueryClient} from '@tanstack/react-query'
import {Link} from 'react-router-dom'
import {ExternalLink} from 'lucide-react'
import {api, getApprovals} from '../api'
import RiskBadge from '../components/RiskBadge'

export default function Approvals() {
	const queryClient = useQueryClient()
	const {data = [], isLoading, isError} = useQuery({queryKey: ['approvals'], queryFn: getApprovals})

	async function decide(id: string, decision: 'approve' | 'reject') {
		await api.post(`/api/approvals/${id}/${decision}`, {
			decided_by: 'approver@example.com',
			comment: `${decision}d from Guardian portal`,
		})
		await Promise.all([
			queryClient.invalidateQueries({queryKey: ['approvals']}),
			queryClient.invalidateQueries({queryKey: ['investigations']}),
		])
	}

	return <section>
		<div className="title">
			<h2>Human approvals</h2>
			<p>Review the linked investigation and evidence before deciding on a proposed action.</p>
		</div>
		{isError && <div className="notice conversation-error" role="alert">Unable to load approval requests. Check the backend connection and reload.</div>}
		<div className="cards">
			{data.map((approval: any) => {
				const investigation = approval.investigation
				const evidence = investigation?.evidence || []
				const metrics = investigation?.sre_metrics || []
				return <article className="panel approval-card" key={approval.id}>
					<div className="panelhead">
						<div><div className="panel-kicker">APPROVAL REQUEST</div><h3>{approval.id}</h3></div>
						<RiskBadge risk={approval.risk}/>
					</div>
					<div className="approval-action"><span>Proposed action</span><strong>{approval.action}{investigation?.recommended_target ? ` → ${investigation.recommended_target}` : ''}</strong></div>
					<div className="approval-meta"><span>{investigation?.application || 'Application unavailable'}</span><span>{approval.environment}</span><span>{approval.status.replaceAll('_', ' ')}</span><span>{investigation?.telemetry_mode === 'demo' ? 'Synthetic demo' : 'Live investigation'}</span></div>
					{investigation ? <>
						<section className="approval-rationale">
							<div className="panel-kicker">WHY THIS NEEDS A DECISION</div>
							<p className="approval-question">{investigation.query}</p>
							<h4>Working hypothesis</h4>
							<p>{investigation.root_cause || 'No root-cause hypothesis was recorded.'}</p>
							<small>RCA confidence: {investigation.confidence == null ? 'not recorded' : `${Math.round(investigation.confidence * 100)}%`}. Treat this as a hypothesis; review its supporting evidence.</small>
						</section>
						{metrics.length > 0 && <section className="approval-evidence">
							<h4>Key telemetry</h4>
							<div className="approval-metrics">{metrics.slice(0, 4).map((metric: any, index: number) => <div key={`${metric.name}-${index}`}><span>{metric.name}</span><strong>{metric.value || 'Unknown'}</strong><small>{metric.status || 'status unavailable'}{metric.baseline ? ` · baseline ${metric.baseline}` : ''}</small></div>)}</div>
						</section>}
						{evidence.length > 0 && <section className="approval-evidence">
							<h4>Supporting observations</h4>
							<ul>{evidence.slice(0, 5).map((item: any, index: number) => <li key={`${item.source}-${item.signal}-${index}`}><span>{item.source || 'source unavailable'}</span><strong>{item.signal || 'Observation'}:</strong> {item.value ?? (item.after !== undefined ? `${item.before ?? '—'} → ${item.after}` : 'No value recorded')}{item.synthetic && <em> · synthetic</em>}</li>)}</ul>
						</section>}
						{investigation.telemetry_notice && <p className="evidence-note">{investigation.telemetry_notice}</p>}
					</> : <div className="notice">The linked investigation record is unavailable. Do not approve until you can review its rationale.</div>}
					<div className="approval-footer">
						<Link className="text-link" to={`/investigations/${encodeURIComponent(approval.investigation_id)}`}>View full investigation <ExternalLink size={14}/></Link>
						{approval.status === 'pending' && <div className="actions"><button className="primary" disabled={!investigation} onClick={() => decide(approval.id, 'approve')}>Approve</button><button disabled={!investigation} onClick={() => decide(approval.id, 'reject')}>Reject</button></div>}
					</div>
				</article>
			})}
			{!isLoading && !data.length && !isError && <div className="panel empty">No approvals are waiting for a decision.</div>}
			{isLoading && <div className="panel empty">Loading approval requests…</div>}
		</div>
	</section>
}
