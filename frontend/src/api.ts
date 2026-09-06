import axios from 'axios'
export const api=axios.create({baseURL:import.meta.env.VITE_API_BASE_URL||'',timeout:30000})
export const getDashboard=async()=> (await api.get('/api/dashboard')).data
export const getInvestigations=async()=> (await api.get('/api/investigations')).data
export const getApprovals=async()=> (await api.get('/api/approvals')).data
export const getPipelines=async()=> (await api.get('/api/pipelines')).data
export const getIntegrations=async()=> (await api.get('/api/integrations')).data
export const getProviders=async()=> (await api.get('/api/integrations/providers')).data
export const investigate=async(payload:any)=> (await api.post('/api/investigations',payload)).data
