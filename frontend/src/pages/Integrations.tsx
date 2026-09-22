import {useQuery, useQueryClient} from '@tanstack/react-query'
import {useState, type FormEvent} from 'react'
import {Link} from 'react-router-dom'
import {ArrowUpRight, Check, CheckCircle2, CircleDashed, Database, FlaskConical, KeyRound, Layers3, PlugZap, Radio, RefreshCw, Save, ScrollText} from 'lucide-react'
import {activateIntegration, getIntegrations, getProviders, requestError, saveIntegration, testIntegration, type Integration, type IntegrationInput, type IntegrationProvider} from '../api'

const displayName = (provider: string) => ({prometheus: 'Prometheus', loki: 'Grafana Loki', datadog: 'Datadog', cloudwatch: 'Amazon CloudWatch', azure_monitor: 'Azure Monitor', github: 'GitHub', azure_devops: 'Azure DevOps', servicenow: 'ServiceNow', opentelemetry: 'OpenTelemetry', kubernetes: 'Kubernetes', pagerduty: 'PagerDuty', grafana: 'Grafana', elasticsearch: 'Elasticsearch', new_relic: 'New Relic', gcp_monitoring: 'Google Cloud Monitoring'}[provider] || provider.replace(/_/g, ' '))
type Feedback = {kind: 'success' | 'error' | 'info'; message: string}

export default function Integrations() {
  const qc = useQueryClient()
  const integrations = useQuery<Integration[]>({queryKey: ['integrations'], queryFn: getIntegrations})
  const providers = useQuery<IntegrationProvider[]>({queryKey: ['providers'], queryFn: getProviders})
  const [provider, setProvider] = useState('prometheus')
  const [name, setName] = useState('Production metrics')
  const [url, setUrl] = useState('')
  const [tokenEnv, setTokenEnv] = useState('')
  const [busy, setBusy] = useState<'test' | 'save' | null>(null)
  const [feedback, setFeedback] = useState<Feedback | null>(null)
  const [activating, setActivating] = useState<string | null>(null)
  const [activationFeedback, setActivationFeedback] = useState<Feedback | null>(null)
  const availableProviders = (providers.data || []).filter(item => item.status === 'available')
  const selected = availableProviders.find(item => item.provider === provider)
  const configured = integrations.data || []
  const activeCount = configured.filter(item => item.enabled && item.configuration.use_for_investigations).length
  function clearFeedback() { setFeedback(null) }
  function selectProvider(next: string) { setProvider(next); setName(next === 'loki' ? 'Production logs' : 'Production metrics'); setUrl(''); setTokenEnv(''); clearFeedback() }
  function payload(): IntegrationInput { return {provider, name: name.trim(), enabled: true, configuration: {url: url.trim(), ...(tokenEnv.trim() ? {bearer_token_env: tokenEnv.trim()} : {})}} }
  async function run(action: 'test' | 'save', event: FormEvent) {
    event.preventDefault()
    if (!selected || busy) return
    setBusy(action); clearFeedback()
    try {
      if (action === 'test') { const result = await testIntegration(payload()); setFeedback({kind: result.ok ? 'success' : 'error', message: result.message}) }
      else { await saveIntegration(payload()); setFeedback({kind: 'info', message: 'Configuration saved. Select “Use for investigations” to make this the active source. Saving does not verify connectivity.'}); await qc.invalidateQueries({queryKey: ['integrations']}) }
    } catch (error) { setFeedback({kind: 'error', message: requestError(error, action === 'test' ? 'Connection test failed.' : 'Unable to save this integration.')}) }
    finally { setBusy(null) }
  }
  async function activate(id: string) {
    setActivating(id); setActivationFeedback(null)
    try { await activateIntegration(id); await Promise.all([qc.invalidateQueries({queryKey: ['integrations']}), qc.invalidateQueries({queryKey: ['telemetry-report']})]); setActivationFeedback({kind: 'success', message: 'Source selected for new live investigations and reports. Refresh existing investigations to collect new evidence.'}) }
    catch (error) { setActivationFeedback({kind: 'error', message: requestError(error, 'Unable to activate this source.')}) }
    finally { setActivating(null) }
  }
  return <section className="integrations-page">
    <div className="integration-hero"><div><div className="eyebrow"><PlugZap size={15}/> YOUR OPERATIONAL CONTEXT</div><h2>Better connected.<br/><span>Better informed.</span></h2><p>Bring metrics and logs into the same investigation. Choose which sources Guardian can read.</p></div><Link className="text-link" to="/reports">Explore live reports <ArrowUpRight size={16}/></Link></div>
    <div className="integration-overview"><div><Database size={19}/><strong>{providers.data ? availableProviders.length : '—'}</strong><span>Available adapters</span></div><div><Layers3 size={19}/><strong>{integrations.data ? configured.length : '—'}</strong><span>Saved configurations</span></div><div><Radio size={19}/><strong>{integrations.data ? activeCount : '—'}</strong><span>Selected saved sources</span></div><p>Read-only evidence collection.<br/>Credentials stay on your backend.</p></div>
    {(providers.isError || integrations.isError) && <div className="notice conversation-error" role="alert">Unable to load integration settings. Check the backend connection.<button className="quiet-button" onClick={() => {void providers.refetch(); void integrations.refetch()}}>Retry</button></div>}
    <div className="integration-workspace"><form className="panel connection-form" onSubmit={event => {void run('save', event)}}><div className="panelhead"><h3>Connect a source</h3><span className="unit-tag">01 / CONFIGURE</span></div><p className="chart-description">Enter an endpoint reachable from the Guardian backend.</p>
      <fieldset disabled={busy !== null || providers.isLoading} className="connection-fields">
        <label>Provider<select value={provider} onChange={event => selectProvider(event.target.value)}>{availableProviders.length ? availableProviders.map(item => <option key={item.provider} value={item.provider}>{displayName(item.provider)}</option>) : <option value="prometheus">{providers.isLoading ? 'Loading providers…' : 'No available provider'}</option>}</select></label>
        <label>Connection name<input required maxLength={120} value={name} placeholder="Production metrics" onChange={event => {setName(event.target.value); clearFeedback()}}/></label>
        <label>Endpoint URL<input required type="url" value={url} placeholder={provider === 'loki' ? 'http://loki:3100' : 'http://prometheus:9090'} onChange={event => {setUrl(event.target.value); clearFeedback()}}/></label>
        <label>Bearer token environment variable <span className="optional-label">Optional</span><input value={tokenEnv} pattern="GUARDIAN_INTEGRATION_[A-Z0-9_]+_TOKEN" placeholder={provider === 'loki' ? 'GUARDIAN_INTEGRATION_LOKI_TOKEN' : 'GUARDIAN_INTEGRATION_PROMETHEUS_TOKEN'} onChange={event => {setTokenEnv(event.target.value); clearFeedback()}}/></label>
        <div className="credential-note"><KeyRound size={15}/><span>Set a dedicated GUARDIAN_INTEGRATION_*_TOKEN variable in the backend environment. Enter only its name here; never paste the secret.</span></div>
        <div className="connection-actions"><button type="submit" disabled={!selected} className="primary"><Save size={15}/> Save source</button><button type="button" disabled={!selected} onClick={event => {const form = event.currentTarget.form; if (form?.reportValidity()) void run('test', event)}}><FlaskConical size={15}/> Test connection</button></div>
      </fieldset>
      {busy && <p className="connection-progress" role="status"><RefreshCw size={14} className="spin"/>{busy === 'test' ? 'Making a read-only request to the source…' : 'Saving the configuration…'}</p>}
      {feedback && <div className={`connection-feedback ${feedback.kind}`} role={feedback.kind === 'error' ? 'alert' : 'status'}>{feedback.message}</div>}
    </form>
    <div className="panel saved-sources"><div className="panelhead"><h3>Your sources</h3><span className="unit-tag">02 / SELECT</span></div><p className="chart-description">One selected source per provider supplies live investigations and reports.</p>{integrations.isLoading && <p role="status">Loading saved sources…</p>}{configured.map(item => {
      const supported = availableProviders.some(entry => entry.provider === item.provider)
      const active = item.enabled && item.configuration.use_for_investigations
      return <article key={item.id} className={`saved-source ${active ? 'selected-source' : ''}`}><div className="saved-source-heading"><div className="source-icon">{item.provider === 'loki' ? <ScrollText size={19}/> : <Database size={19}/>}</div><div><strong>{item.name}</strong><span>{displayName(item.provider)}</span></div><span className={`connection-badge ${active ? 'selected' : ''}`}>{active ? <><Check size={12}/> Selected</> : item.enabled ? 'Saved' : 'Disabled'}</span></div>{item.configuration.url && <p className="source-url">{item.configuration.url}</p>}<div className="saved-source-footer">{active ? <span><CheckCircle2 size={13}/> Used for investigations</span> : <span>{supported ? 'Not selected for investigations' : 'Adapter not yet available'}</span>}{supported && item.enabled && !active && <button onClick={() => void activate(item.id)} disabled={activating !== null}>{activating === item.id ? 'Selecting…' : 'Use for investigations'}</button>}</div></article>
    })}{!integrations.isLoading && !configured.length && <div className="sources-empty"><PlugZap size={28}/><h4>Your first source starts here</h4><p>Save a Prometheus or Loki connection, then select it for investigations.</p></div>}{activationFeedback && <div className={`connection-feedback ${activationFeedback.kind}`} role={activationFeedback.kind === 'error' ? 'alert' : 'status'}>{activationFeedback.message}</div>}<div className="source-footnote">“Selected” records the source choice, not its health. Use a connection test and inspect report evidence. With no selected metrics source, the backend’s configured Prometheus default is used.</div></div></div>
    <div className="provider-section-heading"><div><div className="eyebrow">THE INTEGRATION CATALOG</div><h3>A broader view of your systems</h3></div><span>Available today and planned next</span></div>
    <div className="provider-grid">{(providers.data || []).map(item => <article key={item.provider} className={`provider-card ${item.status}`}><div className="provider-heading"><div className="provider-symbol">{item.provider === 'loki' ? <ScrollText size={21}/> : item.status === 'available' ? <Radio size={21}/> : <Layers3 size={21}/>}</div><span className={`connection-badge ${item.status === 'available' ? 'available' : ''}`}>{item.status === 'available' ? 'Available' : <><CircleDashed size={11}/> Planned</>}</span></div><small className="provider-category">{item.category}</small><h4>{displayName(item.provider)}</h4><p>{item.description}</p><div className="capability-tags">{item.capabilities.map(capability => <span key={capability}>{capability.replace(/_/g, ' ')}</span>)}</div>{item.status === 'available' ? <button className="provider-connect" onClick={() => {selectProvider(item.provider); document.querySelector('.connection-form')?.scrollIntoView({behavior: 'smooth', block: 'start'})}}>Configure source <ArrowUpRight size={14}/></button> : <div className="planned-note">Adapter not implemented</div>}</article>)}</div>
  </section>
}
