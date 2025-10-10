import axios from 'axios'

const api = axios.create({
  baseURL: 'https://lead-management-staging-backend.onrender.com',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for auth tokens
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// API endpoints
export const dashboardAPI = {
  getMetrics: () => api.get('/api/dashboard/metrics'),
  getRecentLeads: () => api.get('/api/dashboard/recent-leads'),
  getActivity: () => api.get('/api/dashboard/activity'),
}

export const leadsAPI = {
  getAll: (params = {}) => api.get('/api/leads/', { params }),
  getById: (id) => api.get(`/api/leads/${id}`),
  create: (data) => api.post('/api/leads/', data),
  update: (id, data) => api.put(`/api/leads/${id}`, data),
  delete: (id) => api.delete(`/api/leads/${id}`),
  addNote: (id, note) => api.post(`/api/leads/${id}/notes`, note),
  getStats: () => api.get('/api/leads/stats/overview'),
}

export const agentsAPI = {
  getAll: (params = {}) => api.get('/api/agents/', { params }),
  getById: (id) => api.get(`/api/agents/${id}`),
  create: (data) => api.post('/api/agents/', data),
  update: (id, data) => api.put(`/api/agents/${id}`, data),
  delete: (id) => api.delete(`/api/agents/${id}`),
  test: (id, message) => api.post(`/api/agents/${id}/chat`, {
    message,
    model: 'gpt-3.5-turbo',
    temperature: 0.7
  }),
  testMock: (id, message) => api.post(`/api/agents/${id}/test`, { message }),
  getStats: (id) => api.get(`/api/agents/${id}/stats`),
  getOverview: () => api.get('/api/agents/stats/overview'),
  getByType: () => api.get('/api/agents/stats/by-type'),
}

export const workflowsAPI = {
  getAll: () => api.get('/api/workflows'),
  getById: (id) => api.get(`/api/workflows/${id}`),
  create: (data) => api.post('/api/workflows', data),
  update: (id, data) => api.put(`/api/workflows/${id}`, data),
  delete: (id) => api.delete(`/api/workflows/${id}`),
  execute: (id, leadId) => api.post(`/api/workflows/${id}/execute`, { leadId }),
}

export const integrationsAPI = {
  getAll: () => api.get('/api/integrations'),
  connect: (id) => api.post(`/api/integrations/${id}/connect`),
  disconnect: (id) => api.post(`/api/integrations/${id}/disconnect`),
  getStatus: (id) => api.get(`/api/integrations/${id}/status`),
}

export const demoAPI = {
  reset: () => api.post('/api/demo/reset'),
}

// Chat API endpoints (re-export from chatAPI service)
export const chatAPI = {
  getRecentConversations: (params = {}) =>
    api.get('/api/messages/conversations/recent', { params }),

  getConversationHistory: (leadExternalId, params = {}) =>
    api.get(`/api/webhooks/zapier/get-agent-responses/${leadExternalId}`, { params }),

  sendLeadMessage: (messageData) =>
    api.post('/api/webhooks/zapier/yelp-message-received', messageData),

  sendBusinessMessage: (messageData) =>
    api.post('/api/messages/route', messageData),

  getLeadActiveSession: (leadId) =>
    api.get(`/api/messages/lead/${leadId}/active-session`),

  getSessionContext: (sessionId) =>
    api.get(`/api/messages/session/${sessionId}/context`),
}

export default api