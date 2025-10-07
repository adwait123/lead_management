import axios from 'axios'

// Create axios instance with default config
const getApiUrl = () => {
  const hostname = window.location.hostname
  const apiUrl = hostname.includes('onrender.com')
    ? 'https://lead-management-j828.onrender.com'
    : import.meta.env.VITE_API_URL || 'http://localhost:8000'

  console.log('API URL Detection:', {
    hostname,
    isRender: hostname.includes('onrender.com'),
    selectedUrl: apiUrl,
    envVar: import.meta.env.VITE_API_URL
  })

  return apiUrl
}

const api = axios.create({
  baseURL: getApiUrl(),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for adding auth tokens (if needed)
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

export default api