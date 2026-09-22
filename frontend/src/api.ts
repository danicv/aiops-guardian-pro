import axios from 'axios'
export const api=axios.create({baseURL:import.meta.env.VITE_API_BASE_URL||'',timeout:30000})
export const getDashboard=async()=> (await api.get('/api/dashboard')).data
export const getInvestigations=async()=> (await api.get('/api/investigations')).data
export const getApprovals=async()=> (await api.get('/api/approvals')).data
export const getPipelines=async()=> (await api.get('/api/pipelines')).data
export const getIntegrations=async()=> (await api.get('/api/integrations')).data
export const getProviders=async()=> (await api.get('/api/integrations/providers')).data
export const investigate=async(payload:any)=> (await api.post('/api/investigations',payload)).data
export const simulateDemo=async(payload:any)=> (await api.post('/api/demo/simulate',payload)).data

export type TelemetryScope = { application: string; environment: string; namespace: string }
export type TelemetryMetric = { name: string; value: string; numeric_value: number | null; unit: string; status: string; baseline?: string | number | null; query?: string; error?: string; observed_at?: number | null }
export type TelemetrySeries = { name: string; unit: string; status: string; points: { timestamp: number; value: number | null }[] }
export type TelemetryReport = {
  scope: TelemetryScope
  window_minutes: number
  generated_at: string
  source: { provider: string; name: string; integration_id?: string | null }
  summary: TelemetryMetric[]
  series: TelemetrySeries[]
  log_entries: { timestamp: string; line: string; labels?: Record<string, string> }[]
  source_errors: string[]
  snapshot: { root_cause?: string; telemetry_notice?: string }
}
export type IntegrationProvider = { provider: string; capabilities: string[]; status: 'available' | 'planned'; category: string; description: string; configuration_example?: Record<string, unknown> }
export type Integration = { id: string; provider: string; name: string; enabled: boolean; configuration: { url?: string; bearer_token_env?: string; use_for_investigations?: boolean } }
export type IntegrationInput = { provider: string; name: string; enabled: boolean; configuration: { url: string; bearer_token_env?: string } }
export const getTelemetryReport = async (scope: TelemetryScope, windowMinutes: number): Promise<TelemetryReport> => (await api.get('/api/reports/telemetry', { params: { ...scope, window_minutes: windowMinutes }, timeout: 90000 })).data
export const testIntegration = async (payload: IntegrationInput): Promise<{ ok: boolean; message: string }> => (await api.post('/api/integrations/test', payload, { timeout: 90000 })).data
export const saveIntegration = async (payload: IntegrationInput): Promise<Integration> => (await api.post('/api/integrations', payload)).data
export const activateIntegration = async (id: string): Promise<unknown> => (await api.post(`/api/integrations/${encodeURIComponent(id)}/activate`, {}, { timeout: 90000 })).data

export function requestError(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (!error.response) return `${fallback} Check the API connection and try again.`
  }
  return fallback
}

export type ConversationScope = {
  application: string
  environment: string
  namespace: string
  telemetry_mode: 'live' | 'demo'
}
export type ConversationSummary = ConversationScope & {
  id: string
  title: string
  revision: number
  updated_at: string
}
export type ConversationMessage = {
  role: 'user' | 'assistant'
  content: string
  question?: string
  assistant_mode?: 'llm' | 'guided'
  notice?: string
  created_at: string
}
export type Conversation = ConversationSummary & {
  messages: ConversationMessage[]
  context: Record<string, unknown>
  result: any
}
export const getConversations = async (): Promise<ConversationSummary[]> => (await api.get('/api/conversations')).data
export const getConversation = async (id: string): Promise<Conversation> => (await api.get(`/api/conversations/${encodeURIComponent(id)}`)).data
export const createConversation = async (payload: ConversationScope & {message: string}): Promise<Conversation> => (await api.post('/api/conversations', payload, {timeout: 90000})).data
export const sendConversationMessage = async (id: string, payload: {message: string; expected_revision: number; refresh_metrics?: boolean}): Promise<Conversation> => (await api.post(`/api/conversations/${encodeURIComponent(id)}/messages`, payload, {timeout: 90000})).data
