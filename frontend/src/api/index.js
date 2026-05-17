import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const msg = error.response?.data?.detail || error.message || 'Unknown error'
    return Promise.reject(new Error(msg))
  }
)

// Requirements
export const importRequirements = (payload) => api.post('/requirements/import', payload)
export const listRequirements = () => api.get('/requirements')
export const parseRequirement = (id) => api.post(`/requirements/${id}/parse`)
export const parseBatch = () => api.post('/requirements/parse-batch')
export const updateRequirement = (id, data) => api.put(`/requirements/${id}`, data)
export const updateStructure = (id, data) => api.put(`/requirements/${id}/structure`, data)
export const deleteRequirement = (id) => api.delete(`/requirements/${id}`)

// Risk
export const analyzeRisk = (reqIds) => api.post('/risk/analyze', { req_ids: reqIds })
export const getRiskReport = () => api.get('/risk/report')
export const updateRisk = (id, data) => api.put(`/risk/${id}`, data)

// Test Cases
export const generateTestCases = (payload) => api.post('/testcases/generate', payload)
export const listTestSuites = () => api.get('/testcases/suites')
export const listTestCases = (params) => api.get('/testcases', { params })
export const createTestCase = (data) => api.post('/testcases', data)
export const updateTestCase = (id, data) => api.put(`/testcases/${id}`, data)
export const deleteTestCase = (id) => api.delete(`/testcases/${id}`)

// Coverage / Traceability
export const getTraceability = (suiteId) => api.get(`/coverage/${suiteId}/traceability`)
export const updateStrategy = (suiteId, techniques) =>
  api.put(`/coverage/${suiteId}/strategy`, { techniques })

// Whitebox (State Diagram)
export const generateStateDiagram = (reqId) => api.post(`/whitebox/requirements/${reqId}/state-diagram`)
export const getStateDiagram = (reqId) => api.get(`/whitebox/requirements/${reqId}/state-diagram`)

// Oracle
export const generateOracle = (tcIds) => api.post('/testcases/generate-oracle', { tc_ids: tcIds })

// Optimize
export const optimizeSuite = (suiteId, strategy = 'risk_based') =>
  api.post('/optimize', { suite_id: suiteId, strategy })

// Export
export const exportArtifacts = (payload) =>
  api.post('/export', payload, { responseType: 'blob' })
