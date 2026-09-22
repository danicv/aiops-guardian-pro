import {useEffect, useRef, useState} from 'react'
import axios from 'axios'
import {createConversation, getConversation, getConversations, sendConversationMessage} from '../api'
import type {Conversation, ConversationScope, ConversationSummary} from '../api'

const STORAGE_KEY = 'guardian.activeConversation'
const DEFAULT_SCOPE: ConversationScope = {application: 'checkout-api', environment: 'prod', namespace: 'aiops-guardian', telemetry_mode: 'live'}
const CONTEXT_LABELS: Record<string, string> = {original_problem: 'Initial problem', symptom: 'Symptoms', onset: 'When it started', recent_change: 'Recent changes', impact: 'Reported impact'}

function remember(id?: string) {
  try {
    if (id) localStorage.setItem(STORAGE_KEY, id)
    else localStorage.removeItem(STORAGE_KEY)
  } catch { /* Conversations also remain available in the saved list. */ }
}

function errorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (error.code === 'ECONNABORTED') return 'Guardian took too long to respond. Reopen the saved conversation to check for a reply before retrying.'
  }
  return 'Unable to reach Guardian. Check the API connection and try again.'
}

function contextText(value: unknown): string {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value.map(contextText).join('; ')
  return JSON.stringify(value)
}

function EvidenceDetails({conversation}: {conversation: Conversation}) {
  const r = conversation.result?.result || conversation.result
  const reports = Object.entries(conversation.context || {}).filter(([key, value]) => key in CONTEXT_LABELS && value != null && value !== '')
  const followUps = Array.isArray(conversation.context?.follow_up_answers) ? conversation.context.follow_up_answers as {question: string; answer: string}[] : []
  return <div className="conversation-evidence">
    <details className="panel" open={reports.length > 0}>
      <summary>User-reported context <span>From this conversation</span></summary>
      <p className="evidence-note">These details came from your messages; telemetry has not independently verified them.</p>
      {reports.length ? <dl className="context-list">{reports.map(([key, value]) => <div key={key}><dt>{CONTEXT_LABELS[key] || key.replace(/_/g, ' ')}</dt><dd>{contextText(value)}</dd></div>)}</dl> : <p>No additional context yet. Tell Guardian what changed or what you are seeing.</p>}
      {followUps.length > 0 && <dl className="context-list">{followUps.map((item, index) => <div key={index}><dt>{item.question}</dt><dd>{item.answer}</dd></div>)}</dl>}
    </details>
    {r && <details className="panel">
      <summary>{conversation.telemetry_mode === 'live' ? 'Observed telemetry & investigation' : 'Simulated evidence & investigation'} <span>{(r.sre_metrics || []).length} metric checks</span></summary>
      <p className="evidence-note">{conversation.telemetry_mode === 'live' ? 'Metrics are a point-in-time snapshot. Use Refresh telemetry to collect new evidence.' : 'Demo values are simulated, not measurements of your service.'}</p>
      {r.snapshot_at && <p><strong>Snapshot collected:</strong> <time dateTime={r.snapshot_at}>{new Date(r.snapshot_at).toLocaleString()}</time></p>}
      {r.telemetry_notice && <div className="notice">{r.telemetry_notice}</div>}
      <div className="grid2 result">
        <div><h3>Investigation findings</h3><p>{r.root_cause || 'No finding is available yet.'}</p><h4>Recommended action</h4><code>{r.recommended_action || 'Review evidence'} → {r.recommended_target || 'review'}</code>
          {r.guardrail && <><h4>Guardrail</h4><p><strong>{r.guardrail.decision}</strong> · {r.guardrail.reason}</p></>}
          {r.approval_id && <div className="notice">Approval created: <strong>{r.approval_id}</strong></div>}
        </div>
        <div><h3>Agent execution trace</h3>{(r.agent_trace || []).map((t: any, i: number) => <div className="trace" key={i}><span>{i + 1}</span><div><strong>{t.agent}</strong><p>{t.summary}</p></div></div>)}</div>
      </div>
      <h3 className="evidence-heading">Advanced metrics</h3>
      <div className="metric-list">{(r.sre_metrics || []).map((metric: any, i: number) => <div className="metric" key={`${metric.name}-${i}`}><div><strong>{metric.name}</strong><small>{metric.value ?? 'Unknown'} · Reference: {metric.baseline || 'Not configured'}</small>{metric.observed_at && <small>Evaluated: {metric.observed_at}</small>}{metric.error && <p>{metric.error}</p>}</div><span className={`risk ${metric.status || 'unknown'}`}>{metric.status || 'unknown'}</span>{metric.query && <code>{metric.query}</code>}</div>)}</div>
    </details>}
    {r && <details className="panel">
      <summary>Action plan & instrumentation <span>Review suggested next steps</span></summary>
      <h3 className="evidence-heading">SRE action plan</h3>
      {(r.action_plan || []).map((item: any, i: number) => <div className="plan-step" key={i}><strong>{item.step}</strong><p>{item.instruction}</p><small>Owner: {item.owner}</small></div>)}
      <h3 className="evidence-heading">Instrumentation recommendations</h3>
      <div className="instrument-grid">{(r.instrumentation || []).map((item: any, i: number) => <div className="instrument" key={i}><strong>{item.name}</strong><p>{item.instruction}</p><code>{item.example}</code></div>)}</div>
    </details>}
  </div>
}

export default function AskGuardian() {
  const [scope, setScope] = useState<ConversationScope>(DEFAULT_SCOPE)
  const [draft, setDraft] = useState('')
  const [conversation, setConversation] = useState<Conversation | null>(null)
  const [saved, setSaved] = useState<ConversationSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [listError, setListError] = useState('')
  const [status, setStatus] = useState('Loading saved conversations…')
  const composer = useRef<HTMLTextAreaElement>(null)
  const log = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (log.current) log.current.scrollTop = log.current.scrollHeight
  }, [conversation?.id, conversation?.revision])

  function accept(next: Conversation) {
    setConversation(next)
    setScope({application: next.application, environment: next.environment, namespace: next.namespace, telemetry_mode: next.telemetry_mode})
    setSaved(items => [next, ...items.filter(item => item.id !== next.id)])
    remember(next.id)
  }

  useEffect(() => {
    let active = true
    let activeId: string | null = null
    try { activeId = localStorage.getItem(STORAGE_KEY) } catch { /* Storage is optional. */ }
    const listRequest = getConversations().then(items => { if (active) setSaved(items) }).catch(() => { if (active) setListError('Saved conversations could not be loaded.') })
    const restoreRequest = activeId ? getConversation(activeId).then(next => {
      if (active) {
        setConversation(next)
        setScope({application: next.application, environment: next.environment, namespace: next.namespace, telemetry_mode: next.telemetry_mode})
      }
    }).catch((failure: unknown) => {
      if (active) {
        if (axios.isAxiosError(failure) && failure.response?.status === 404) remember()
        setError(`Could not restore the previous conversation. ${errorMessage(failure)}`)
      }
    }) : Promise.resolve()
    Promise.all([listRequest, restoreRequest]).finally(() => { if (active) { setLoading(false); setStatus('') } })
    return () => { active = false }
  }, [])

  async function openConversation(id: string, preserveDraft = false) {
    if (!id) return
    setLoading(true)
    setError('')
    setStatus('Opening conversation…')
    try { accept(await getConversation(id)); if (!preserveDraft) setDraft('') } catch (failure) { setError(errorMessage(failure)) }
    finally { setLoading(false); setStatus('') }
  }

  function startNew() {
    setConversation(null)
    setDraft('')
    setError('')
    setStatus('')
    remember()
    composer.current?.focus()
  }

  async function submit(refresh = false) {
    if (loading || (!refresh && !draft.trim())) return
    setLoading(true)
    setError('')
    setStatus(refresh ? 'Refreshing telemetry and reassessing…' : 'Guardian is reviewing your message…')
    const message = refresh ? 'Refresh the current telemetry and reassess.' : draft.trim()
    try {
      const next = conversation
        ? await sendConversationMessage(conversation.id, {message, expected_revision: conversation.revision, refresh_metrics: refresh})
        : await createConversation({...scope, application: scope.application.trim(), namespace: scope.namespace.trim(), message})
      accept(next)
      if (!refresh) setDraft('')
      setStatus(refresh ? 'Telemetry refreshed. Guardian has reassessed the evidence.' : 'Guardian replied.')
    } catch (failure) {
      if (axios.isAxiosError(failure) && failure.response?.status === 409 && conversation) {
        try {
          accept(await getConversation(conversation.id))
          setError('This conversation changed in another session. The latest messages are loaded; your draft is still here. Review the reply, then send again.')
        } catch { setError('This conversation changed in another session, but the latest messages could not be loaded. Your draft is still here. Reopen this conversation before sending again.') }
      } else setError(errorMessage(failure))
      setStatus('')
    } finally { setLoading(false) }
  }

  const assistantMessages = conversation?.messages.filter(message => message.role === 'assistant') || []
  const lastAssistant = assistantMessages[assistantMessages.length - 1]
  const canSend = !!draft.trim() && !!scope.application.trim() && !!scope.namespace.trim() && !loading
  return <section className="ask-guardian">
    <div className="title"><h2>Ask Guardian</h2><p>Investigate together. Answer follow-up questions, add context, and refine the next step.</p></div>
    <div className="panel conversation-toolbar">
      <label>Saved conversations<select aria-label="Saved conversations" value={conversation?.id || ''} disabled={loading} onChange={e => openConversation(e.target.value)}><option value="" disabled>Choose a conversation</option>{saved.map(item => <option value={item.id} key={item.id}>{item.title || item.application} · {item.environment}</option>)}</select></label>
      <button type="button" disabled={loading} onClick={startNew}>New conversation</button>
      {conversation && <button type="button" disabled={loading} onClick={() => openConversation(conversation.id, true)}>Reload conversation</button>}
      {listError && <p className="saved-error" role="status">{listError}</p>}
    </div>
    <div className="panel conversation-panel">
      {conversation ? <div className="conversation-scope"><div><strong>{conversation.application}</strong><span>{conversation.environment} / {conversation.namespace}</span></div><span className="assistant-badge">{conversation.telemetry_mode === 'live' ? 'Live Prometheus' : 'Simulated demo'}</span><small>Start a new conversation to change scope.</small></div> : <fieldset className="scope-fields" disabled={loading}><legend>Investigation scope</legend>
        <div className="form2"><label>Application<input value={scope.application} maxLength={120} onChange={e => setScope({...scope, application: e.target.value})}/></label><label>Environment<select value={scope.environment} onChange={e => setScope({...scope, environment: e.target.value})}><option>dev</option><option>test</option><option>stage</option><option>prod</option></select></label></div>
        <div className="form2"><label>Telemetry<select value={scope.telemetry_mode} onChange={e => setScope({...scope, telemetry_mode: e.target.value as 'live' | 'demo'})}><option value="live">Live Prometheus</option><option value="demo">Simulated demo</option></select></label><label>Namespace<input value={scope.namespace} maxLength={120} onChange={e => setScope({...scope, namespace: e.target.value})}/></label></div>
      </fieldset>}
      <div className="conversation-log" ref={log} role="log" aria-label="Investigation conversation" aria-live="polite" aria-relevant="additions" aria-busy={loading}>
        {!conversation && <div className="conversation-welcome"><h3>What are you investigating?</h3><p>Describe a symptom or ask a question. Guardian uses the selected telemetry and asks for missing details as the investigation develops.</p><p className="example-prompt">For example: “Checkout requests became slow after the latest deployment. What should I check?”</p></div>}
        {conversation?.messages.map((message, index) => <article className={`conversation-message ${message.role}`} key={`${conversation.id}-${index}`} aria-label={`${message.role === 'user' ? 'You' : 'Guardian'}, message ${index + 1}`}>
          <div className="message-heading"><strong>{message.role === 'user' ? 'You' : 'Guardian'}</strong>{message.role === 'assistant' && <span className="assistant-badge">{message.assistant_mode === 'llm' ? 'LLM assistant' : 'Guided assistant'}</span>}<time dateTime={message.created_at}>{new Date(message.created_at).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}</time></div>
          <p className="message-content">{message.content}</p>
          {message.notice && <p className="message-notice">{message.notice}</p>}
          {message.question && <div className="followup-question"><strong>To refine this investigation</strong><p>{message.question}</p></div>}
        </article>)}
      </div>
      {error && <div className="notice conversation-error" role="alert">{error}</div>}
      <form className="conversation-composer" onSubmit={e => { e.preventDefault(); void submit() }}>
        <label htmlFor="guardian-message">{conversation ? 'Reply or ask a follow-up question' : 'Describe the issue'}<textarea id="guardian-message" ref={composer} rows={3} maxLength={4000} disabled={loading} value={draft} onChange={e => setDraft(e.target.value)} placeholder={conversation ? 'Answer Guardian, correct a detail, or ask what to do next…' : 'What is happening, and what would you like to understand?'}/></label>
        <div className="composer-actions"><div className="actions"><button className="primary" disabled={!canSend}>{loading ? 'Working…' : conversation ? 'Send reply' : 'Start investigation'}</button>{conversation && <button type="button" disabled={loading} onClick={() => submit(true)}>Refresh telemetry</button>}</div><small>{draft.length}/4000</small></div>
        <p className="conversation-status" role="status">{status || (conversation ? 'Follow-ups retain your context and the current telemetry snapshot.' : 'Guardian will collect an initial telemetry snapshot when you send.')}</p>
        {lastAssistant?.assistant_mode !== 'llm' && <p className="assistant-explainer">Guided mode uses evidence-based prompts and structured suggestions. When a supported LLM is configured, replies are labeled LLM assistant.</p>}
      </form>
    </div>
    {conversation && <EvidenceDetails conversation={conversation}/>}
  </section>
}
