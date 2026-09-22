import {useState, type FormEvent, type CSSProperties} from 'react'
import {useQuery} from '@tanstack/react-query'
import {Link} from 'react-router-dom'
import {Activity, ArrowUpRight, ChartNoAxesCombined, Clock3, Database, FileDown, Gauge, RefreshCw, ScrollText, TriangleAlert, Waves} from 'lucide-react'
import {Area, AreaChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis} from 'recharts'
import {getTelemetryReport, requestError, type TelemetryMetric, type TelemetryScope, type TelemetrySeries} from '../api'

const signals = [
  {name: 'Request rate', label: 'Traffic', description: 'Requests per second · 5-minute rate', color: '#4bd9de', icon: Activity},
  {name: 'HTTP 5xx rate', label: 'Errors', description: 'Server errors as a share of requests', color: '#fb9d82', icon: TriangleAlert},
  {name: 'p95 latency', label: 'Latency', description: '95th percentile request duration', color: '#a99aff', icon: Waves},
  {name: 'Error-budget burn', label: 'SLO burn', description: 'Error rate relative to the SLO budget', color: '#efc773', icon: Gauge},
]
const initialScope: TelemetryScope = {application: 'checkout-api', environment: 'prod', namespace: 'aiops-guardian'}
const timeLabel = (timestamp: number) => new Date(timestamp * 1000).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})
const fullTime = (timestamp: string) => new Date(timestamp).toLocaleString()
const numberLabel = (value: number) => new Intl.NumberFormat(undefined, {maximumFractionDigits: 2, notation: Math.abs(value) >= 10000 ? 'compact' : 'standard'}).format(value)

function MetricChart({signal, series, metric, index, windowMinutes}: {signal: typeof signals[number]; series?: TelemetrySeries; metric?: TelemetryMetric; index: number; windowMinutes: number}) {
  const hasData = series?.points.some(point => point.value !== null && Number.isFinite(point.value))
  const threshold = typeof metric?.baseline === 'number' ? metric.baseline : null
  return <article className="panel trend-panel">
    <div className="trend-heading"><div><div className="eyebrow">{signal.label}</div><h3>{signal.name}</h3></div><span className="unit-tag">{series?.unit || metric?.unit || '—'}</span></div>
    <p className="chart-description">{signal.description}</p>
    <div className="telemetry-chart" role="img" aria-label={`${signal.name} over the last ${windowMinutes} minutes. ${hasData ? 'Exact values are available in the observations table below.' : 'No measurements available.'}`}>
      {hasData ? <ResponsiveContainer width="100%" height="100%"><AreaChart data={series!.points} margin={{top: 12, right: 12, left: 0, bottom: 0}} accessibilityLayer>
        <defs><linearGradient id={`signal-fill-${index}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={signal.color} stopOpacity={0.22}/><stop offset="100%" stopColor={signal.color} stopOpacity={0.01}/></linearGradient></defs>
        <CartesianGrid vertical={false} stroke="#223047" strokeDasharray="3 5"/>
        <XAxis dataKey="timestamp" type="number" domain={['dataMin', 'dataMax']} tickFormatter={timeLabel} stroke="#344158" tick={{fill: '#91a1b9', fontSize: 11}} tickLine={false} axisLine={false} minTickGap={36}/>
        <YAxis domain={[0, 'auto']} tickFormatter={numberLabel} tick={{fill: '#91a1b9', fontSize: 11}} tickLine={false} axisLine={false} width={48}/>
        <Tooltip labelFormatter={value => new Date(Number(value) * 1000).toLocaleString()} formatter={value => [`${numberLabel(Number(value))} ${series!.unit}`, signal.name]} contentStyle={{background: '#101e30', border: '1px solid #344865', borderRadius: 10, color: '#e4edf9'}} labelStyle={{color: '#b5c6dd', marginBottom: 6}}/>
        {threshold !== null && <ReferenceLine y={threshold} stroke="#64758e" strokeDasharray="4 4" ifOverflow="extendDomain" label={{value: 'Threshold', fill: '#96a7bf', fontSize: 10, position: 'insideTopRight'}}/>}
        <Area type="linear" dataKey="value" stroke={signal.color} strokeWidth={2} fill={`url(#signal-fill-${index})`} connectNulls={false} isAnimationActive={false} dot={false} activeDot={{r: 4, stroke: '#0d1728', strokeWidth: 2}}/>
      </AreaChart></ResponsiveContainer> : <div className="chart-empty"><Database size={24}/><strong>No measurements available</strong><span>Check source connectivity, matching labels, and recent traffic.</span></div>}
    </div>
    <div className="chart-foot"><span>Last {windowMinutes} minutes</span><span>Gaps mean missing evidence</span></div>
    {series && series.points.length > 0 && <details className="query-details"><summary>View observations</summary><div className="observations-table"><table><caption>{signal.name} · local time · {series.unit}</caption><thead><tr><th>Observed at</th><th>Value</th></tr></thead><tbody>{series.points.map((point, pointIndex) => <tr key={`${point.timestamp}-${pointIndex}`}><td>{new Date(point.timestamp * 1000).toLocaleString()}</td><td>{point.value === null ? 'Unavailable' : `${numberLabel(point.value)} ${series.unit}`}</td></tr>)}</tbody></table></div></details>}
    {metric?.query && <details className="query-details"><summary>Inspect source query</summary><code>{metric.query}</code></details>}
  </article>
}

export default function Reports() {
  const [draft, setDraft] = useState(initialScope)
  const [scope, setScope] = useState(initialScope)
  const [windowMinutes, setWindowMinutes] = useState(30)
  const report = useQuery({queryKey: ['telemetry-report', scope, windowMinutes], queryFn: () => getTelemetryReport(scope, windowMinutes), retry: false})
  const data = report.data
  const availableCount = data?.summary.filter(metric => metric.numeric_value !== null && Number.isFinite(metric.numeric_value)).length ?? 0
  function refresh(event: FormEvent) {
    event.preventDefault()
    const next = {application: draft.application.trim(), environment: draft.environment.trim(), namespace: draft.namespace.trim()}
    if (JSON.stringify(next) === JSON.stringify(scope)) void report.refetch()
    else setScope(next)
  }
  return <section className="reports-page">
    <div className="report-hero"><div><div className="eyebrow"><ChartNoAxesCombined size={15}/> RELIABILITY INTELLIGENCE</div><h2>Every signal.<br/><span>A clearer picture.</span></h2><p>Explore live service health, inspect the evidence, and take your next question to Guardian.</p></div><div className="report-hero-actions"><Link className="text-link" to="/integrations">Manage data sources <ArrowUpRight size={15}/></Link><button className="quiet-button" onClick={() => window.print()} disabled={!data}><FileDown size={15}/> Print / save PDF</button></div></div>
    <form className="panel report-filters" onSubmit={refresh} aria-label="Report scope">
      <label>Application<input required value={draft.application} onChange={e => setDraft({...draft, application: e.target.value})}/></label>
      <label>Environment<input required value={draft.environment} onChange={e => setDraft({...draft, environment: e.target.value})}/></label>
      <label>Namespace<input required value={draft.namespace} onChange={e => setDraft({...draft, namespace: e.target.value})}/></label>
      <label>Time window<select value={windowMinutes} onChange={e => setWindowMinutes(Number(e.target.value))}><option value={15}>Last 15 minutes</option><option value={30}>Last 30 minutes</option><option value={60}>Last 60 minutes</option></select></label>
      <button className="primary" type="submit" disabled={report.isFetching}><RefreshCw size={15} className={report.isFetching ? 'spin' : ''}/>{report.isFetching ? 'Fetching…' : 'Refresh'}</button>
    </form>
    {report.isError && <div role="alert" className="notice conversation-error">{requestError(report.error, 'Unable to load the telemetry report.')}{data && ' The report below is from the previous successful request.'}</div>}
    {!data && report.isFetching && <div className="panel report-loading" role="status"><RefreshCw size={22} className="spin"/><strong>Reading your telemetry sources</strong><span>Collecting current measurements and historical trends…</span></div>}
    {data && <>
      <div className="report-meta"><div><span className="source-chip"><Database size={12}/>{data.source.name || data.source.provider}</span><span>{data.scope.application} / {data.scope.environment} / {data.scope.namespace}</span></div><span><Clock3 size={13}/> Captured {fullTime(data.generated_at)}</span></div>
      <div className="report-metrics">{signals.map((signal, index) => {
        const metric = data.summary.find(item => item.name === signal.name)
        const known = metric?.numeric_value !== null && metric?.numeric_value !== undefined && Number.isFinite(metric.numeric_value)
        const Icon = signal.icon
        return <article className="report-metric" key={signal.name} style={{'--signal-color': signal.color} as CSSProperties}><div className="metric-card-head"><span>{signal.name}</span><Icon size={17}/></div><div className="metric-card-value">{known ? numberLabel(metric!.numeric_value!) : '—'}<small>{known ? metric!.unit : 'Unknown'}</small></div><div className="metric-card-bottom"><span className={`signal-status ${known ? metric!.status : 'unknown'}`}>{known ? (metric!.status === 'healthy' ? 'Within threshold' : metric!.status === 'observed' ? 'Observed' : metric!.status) : 'No current reading'}</span><span className="signal-index">0{index + 1}</span></div></article>
      })}</div>
      <div className="report-evidence-note"><span className={`evidence-dot ${availableCount === 4 ? 'complete' : ''}`}/><span><strong>{availableCount} of 4</strong> current signals available. {data.snapshot.telemetry_notice || 'Charts show queried observations; missing telemetry never counts as recovery.'}</span></div>
      {data.source_errors.length > 0 && <div className="source-warnings" role="status"><TriangleAlert size={17}/><div><strong>Some evidence is unavailable</strong><ul>{data.source_errors.map((error, index) => <li key={index}>{error}</li>)}</ul><Link to="/integrations">Review source configuration <ArrowUpRight size={12}/></Link></div></div>}
      <div className="report-chart-grid">{signals.map((signal, index) => <MetricChart key={signal.name} signal={signal} index={index} windowMinutes={data.window_minutes} series={data.series.find(series => series.name === signal.name)} metric={data.summary.find(metric => metric.name === signal.name)}/>)}</div>
      <div className="report-bottom-grid"><article className="panel log-panel"><div className="panelhead"><h3><ScrollText size={17}/> Log evidence</h3><span className="unit-tag">{data.log_entries.length} entries</span></div><p className="chart-description">Recent logs for the same application, environment, namespace, and time window.</p>{data.log_entries.length ? <div className="log-stream">{data.log_entries.map((entry, index) => <div className="log-entry" key={`${entry.timestamp}-${index}`}><time dateTime={entry.timestamp}>{fullTime(entry.timestamp)}</time><pre>{entry.line}</pre>{entry.labels && <div className="log-labels">{Object.entries(entry.labels).map(([key, value]) => <span key={key}>{key}={value}</span>)}</div>}</div>)}</div> : <div className="log-empty"><ScrollText size={25}/><strong>No log evidence returned</strong><p>{data.source_errors.some(error => /loki|log/i.test(error)) ? 'The log source is unconfigured or unavailable. Review the source details above.' : 'No matching logs were found in this window. Confirm the source labels and time range.'}</p><Link to="/integrations">Configure a log source <ArrowUpRight size={13}/></Link></div>}</article><article className="panel report-next"><div className="eyebrow">FROM EVIDENCE TO ACTION</div><h3>Make the next<br/>question count.</h3><p>{data.snapshot.root_cause || 'Use these observations to refine an investigation and decide what to check next.'}</p><div className="report-scope-note">Start or select a live conversation in Ask Guardian with this report’s scope: <strong>{data.scope.application}</strong> · {data.scope.environment} · {data.scope.namespace}.</div><Link className="primary button-link" to="/ask">Open Ask Guardian <ArrowUpRight size={16}/></Link><small>Metric changes are evidence, not proof of a root cause.</small></article></div>
    </>}
  </section>
}
