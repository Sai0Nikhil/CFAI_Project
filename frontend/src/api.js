import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

export const getGraph    = (profile = 'staff')  => api.get(`/graph?profile=${profile}`)
export const getNodes    = ()                    => api.get('/nodes')
export const getProfiles = ()                    => api.get('/profiles')
export const getHealth   = ()                    => api.get('/health')

export const runSearch   = (body) => api.post('/search', body)
export const compareAll  = (body) => api.post('/compare', body)

export const parseNLP    = (body) => api.post('/nlp', body)

export const validateCSP = (body) => api.post('/csp/validate', body)
export const timeWindow  = (profile, node) =>
  api.get(`/csp/time-window?profile=${profile}&node=${node}`)

export const runGame     = (body) => api.post('/game', body)

export const bayesInfer  = (body) => api.post('/bayes/infer', body)
export const bayesHMM    = (body) => api.post('/bayes/hmm', body)
export const bayesRoute  = (body) => api.post('/bayes/route', body)
export const bayesOptions= ()     => api.get('/bayes/options')

export default api
