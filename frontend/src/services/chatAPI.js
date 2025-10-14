import api from '../lib/api.js'

/**
 * Chat API service for messaging functionality
 * Integrates with existing backend messaging endpoints
 */
export const chatAPI = {
  /**
   * Get all recent conversations with leads
   * @param {Object} params - Query parameters
   * @param {number} params.limit - Number of conversations to return (default: 10)
   * @returns {Promise} Response with conversations array
   */
  getRecentConversations: (params = {}) =>
    api.get('/api/messages/conversations/recent', { params }),

  /**
   * Get conversation history for a specific lead
   * @param {number} leadId - Internal ID of the lead
   * @param {Object} params - Query parameters
   * @param {string} params.since_timestamp - ISO timestamp to get messages after this time
   * @param {number} params.limit - Maximum number of messages to return (default: 50)
   * @returns {Promise} Response with messages array (both agent and lead messages)
   */
  getConversationHistory: (leadId, params = {}) =>
    api.get(`/api/messages/lead/${leadId}/messages`, { params }),

  /**
   * Get conversation history for a specific lead using external ID (deprecated)
   * @deprecated Use getConversationHistory with leadId for better performance
   * @param {string} leadExternalId - External ID of the lead (e.g., Yelp lead ID)
   * @param {Object} params - Query parameters
   * @param {string} params.since_timestamp - ISO timestamp to get messages after this time
   * @param {number} params.limit - Maximum number of messages to return (default: 50)
   * @returns {Promise} Response with messages array (both agent and lead messages)
   */
  getConversationHistoryByExternalId: (leadExternalId, params = {}) =>
    api.get(`/api/messages/conversation/${leadExternalId}`, { params }),

  /**
   * Send a message from lead (for simulation/testing)
   * @param {Object} messageData - Message data
   * @param {string} messageData.yelp_lead_id - Lead external ID
   * @param {string} messageData.conversation_id - Conversation ID
   * @param {string} messageData.message_content - Message content
   * @param {string} messageData.sender - Sender type ('customer' or 'business')
   * @param {string} messageData.timestamp - ISO timestamp
   * @returns {Promise} Response with agent message
   */
  sendLeadMessage: (messageData) =>
    api.post('/api/webhooks/zapier/yelp-message-received', messageData),

  /**
   * Send a message from business owner (route through system)
   * @param {Object} messageData - Message data
   * @param {number} messageData.lead_id - Internal lead ID
   * @param {string} messageData.message - Message content
   * @param {string} messageData.message_type - Message type (default: 'text')
   * @param {Object} messageData.metadata - Additional metadata
   * @returns {Promise} Response with routing result
   */
  sendBusinessMessage: (messageData) =>
    api.post('/api/messages/route', messageData),

  /**
   * Get active session for a lead
   * @param {number} leadId - Internal lead ID
   * @returns {Promise} Response with active session info
   */
  getLeadActiveSession: (leadId) =>
    api.get(`/api/messages/lead/${leadId}/active-session`),

  /**
   * Get session context (agent, lead, session details)
   * @param {number} sessionId - Session ID
   * @returns {Promise} Response with session context
   */
  getSessionContext: (sessionId) =>
    api.get(`/api/messages/session/${sessionId}/context`),

  /**
   * Mark a message as delivered
   * @param {number} messageId - Message ID
   * @param {string} externalMessageId - External platform message ID (optional)
   * @returns {Promise} Response with delivery confirmation
   */
  markMessageDelivered: (messageId, externalMessageId = null) =>
    api.post(`/api/webhooks/zapier/mark-delivered/${messageId}`, {
      external_message_id: externalMessageId
    }),

  /**
   * Record agent response
   * @param {Object} responseData - Response data
   * @param {number} responseData.session_id - Session ID
   * @param {string} responseData.response - Response content
   * @param {Object} responseData.response_metadata - Response metadata
   * @returns {Promise} Response with success status
   */
  recordAgentResponse: (responseData) =>
    api.post('/api/messages/agent-response', responseData),

  /**
   * Get messaging statistics
   * @returns {Promise} Response with stats
   */
  getMessagingStats: () =>
    api.get('/api/messages/stats'),

  /**
   * Simulate a lead message for testing
   * @param {number} leadId - Lead ID
   * @param {string} message - Message content
   * @returns {Promise} Response with simulation result
   */
  simulateLeadMessage: (leadId, message) =>
    api.post('/api/messages/simulate/lead-message', null, {
      params: { lead_id: leadId, message }
    }),

  /**
   * Take over a session from the agent
   * @param {number} sessionId - Session ID
   * @param {Object} takeoverData - Takeover details
   * @param {string} takeoverData.reason - Reason for takeover
   * @param {string} takeoverData.business_owner_id - Business owner ID
   * @returns {Promise} Response with takeover result
   */
  takeoverSession: (sessionId, takeoverData = {}) =>
    api.post(`/api/messages/session/${sessionId}/takeover`, {
      reason: takeoverData.reason || 'Manual takeover',
      business_owner_id: takeoverData.business_owner_id || 'default'
    }),

  /**
   * Release session back to agent control
   * @param {number} sessionId - Session ID
   * @returns {Promise} Response with release result
   */
  releaseSession: (sessionId) =>
    api.post(`/api/messages/session/${sessionId}/release`),

  /**
   * Get session status and control information
   * @param {number} sessionId - Session ID
   * @returns {Promise} Response with session status
   */
  getSessionStatus: (sessionId) =>
    api.get(`/api/messages/session/${sessionId}/status`)
}

/**
 * Utility functions for chat functionality
 */
export const chatUtils = {
  /**
   * Format timestamp for display
   * @param {string} timestamp - ISO timestamp
   * @returns {string} Formatted time string
   */
  formatMessageTime: (timestamp) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffInMinutes = Math.floor((now - date) / (1000 * 60))

    if (diffInMinutes < 1) return 'Just now'
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    })
  },

  /**
   * Get message sender display info
   * @param {Object} message - Message object
   * @returns {Object} Sender info with name, type, and styling
   */
  getSenderInfo: (message) => {
    const isAgent = message.sender_type === 'agent'
    const isLead = message.sender_type === 'lead'
    const isSystem = message.sender_type === 'system'

    return {
      name: message.sender_name || (isAgent ? 'Agent' : isLead ? 'Lead' : 'System'),
      type: message.sender_type,
      isAgent,
      isLead,
      isSystem,
      avatarColor: isAgent ? 'bg-blue-500' : isLead ? 'bg-green-500' : 'bg-gray-500',
      bubbleColor: isAgent ? 'bg-blue-50 border-blue-200' : 'bg-white border-gray-200'
    }
  },

  /**
   * Get conversation status info
   * @param {Object} conversation - Conversation object
   * @returns {Object} Status info with color and display text
   */
  getConversationStatus: (conversation) => {
    const status = conversation.session_status || 'unknown'

    const statusMap = {
      active: { text: 'Active', color: 'green', icon: '🟢' },
      completed: { text: 'Completed', color: 'blue', icon: '✅' },
      escalated: { text: 'Escalated', color: 'orange', icon: '⚠️' },
      paused: { text: 'Paused', color: 'yellow', icon: '⏸️' },
      failed: { text: 'Failed', color: 'red', icon: '❌' },
      unknown: { text: 'Unknown', color: 'gray', icon: '❓' }
    }

    return statusMap[status] || statusMap.unknown
  },

  /**
   * Check if conversation needs attention
   * @param {Object} conversation - Conversation object
   * @returns {boolean} True if needs attention
   */
  needsAttention: (conversation) => {
    const status = conversation.session_status
    const lastMessageTime = new Date(conversation.last_message_at)
    const now = new Date()
    const hoursAgo = (now - lastMessageTime) / (1000 * 60 * 60)

    // Needs attention if escalated, or active but no response in 2+ hours
    return status === 'escalated' ||
           (status === 'active' && hoursAgo > 2 && conversation.last_message_from === 'lead')
  },

  /**
   * Get priority level for conversation
   * @param {Object} conversation - Conversation object
   * @returns {string} Priority level: 'high', 'medium', 'low'
   */
  getPriority: (conversation) => {
    if (conversation.session_status === 'escalated') return 'high'
    if (chatUtils.needsAttention(conversation)) return 'medium'
    return 'low'
  }
}

export default chatAPI