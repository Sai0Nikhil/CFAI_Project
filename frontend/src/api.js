import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

export const getHospitals = ()                          => api.get('/hospitals')
export const getGraph    = (profile = 'staff', hospital = 'charite') => api.get(`/graph?profile=${profile}&hospital=${hospital}`)
export const getNodes    = (hospital = 'charite')       => api.get(`/nodes?hospital=${hospital}`)
export const getProfiles = ()                           => api.get('/profiles')
export const getHealth   = ()                           => api.get('/health')

export const runSearch   = (body) => api.post('/search', body)
export const compareAll  = (body) => api.post('/compare', body)

export const parseNLP    = (body) => api.post('/nlp', body)

export const validateCSP = (body) => api.post('/csp/validate', body)
export const timeWindow  = (profile, node) =>
  api.get(`/csp/time-window?profile=${profile}&node=${node}`)

export const runGame     = (body) => api.post('/game', body)
export const runMCTS     = (body) => api.post('/game/mcts', body)
export const runNotNamedYet = (body) => api.post('/game/not-named-yet', body)

export const bayesInfer  = (body) => api.post('/bayes/infer', body)
export const bayesHMM    = (body) => api.post('/bayes/hmm', body)
export const bayesRoute  = (body) => api.post('/bayes/route', body)
export const bayesOptions= ()     => api.get('/bayes/options')

export const aiExplain   = (body) => api.post('/ai/explain', body)

export const runEthicalTriage = (body) => api.post('/csp/ethical-triage', body)
export const runMultilingualExplain = (body) => api.post('/explain/multilingual', body)
export const runActiveBelief = (body) => api.post('/bayes/active-belief', body)
export const runMultiAgentSearch = (body) => api.post('/search/multi-agent', body)

export default api


