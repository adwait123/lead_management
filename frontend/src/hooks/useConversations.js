import { useState, useEffect, useCallback, useRef } from 'react'
import { chatAPI, chatUtils } from '../services/chatAPI'

/**
 * Custom hook for managing conversations list
 * @param {Object} options - Configuration options
 * @param {number} options.limit - Number of conversations to fetch (default: 20)
 * @param {number} options.pollInterval - Polling interval in milliseconds (default: 10000)
 * @param {boolean} options.autoRefresh - Auto refresh conversations (default: true)
 * @returns {Object} Conversations state and functions
 */
export function useConversations(options = {}) {
  const {
    limit = 20,
    pollInterval = 10000, // Poll every 10 seconds
    autoRefresh = true
  } = options

  // State
  const [conversations, setConversations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [stats, setStats] = useState({
    active: 0,
    total: 0,
    needsAttention: 0,
    highPriority: 0
  })

  // Refs
  const pollIntervalRef = useRef(null)

  /**
   * Load conversations from API
   */
  const loadConversations = useCallback(async () => {
    try {
      const response = await chatAPI.getRecentConversations({ limit })

      if (response.data.conversations) {
        const conversationsData = response.data.conversations.map(conv => ({
          ...conv,
          // Add computed properties
          status: chatUtils.getConversationStatus(conv),
          needsAttention: chatUtils.needsAttention(conv),
          priority: chatUtils.getPriority(conv),
          formattedTime: chatUtils.formatMessageTime(conv.last_message_at || conv.created_at)
        }))

        setConversations(conversationsData)

        // Calculate stats
        const newStats = {
          total: conversationsData.length,
          active: conversationsData.filter(c => c.session_status === 'active').length,
          needsAttention: conversationsData.filter(c => c.needsAttention).length,
          highPriority: conversationsData.filter(c => c.priority === 'high').length
        }
        setStats(newStats)

        setError(null)
      }
    } catch (err) {
      console.error('Error loading conversations:', err)
      setError('Failed to load conversations')
    } finally {
      setLoading(false)
    }
  }, [limit])

  /**
   * Refresh conversations manually
   */
  const refreshConversations = useCallback(() => {
    setLoading(true)
    loadConversations()
  }, [loadConversations])

  /**
   * Start auto-refresh polling
   */
  const startPolling = useCallback(() => {
    if (pollIntervalRef.current || !autoRefresh) return

    pollIntervalRef.current = setInterval(() => {
      loadConversations()
    }, pollInterval)
  }, [loadConversations, pollInterval, autoRefresh])

  /**
   * Stop auto-refresh polling
   */
  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
  }, [])

  /**
   * Get conversations by status
   */
  const getConversationsByStatus = useCallback((status) => {
    return conversations.filter(conv => conv.session_status === status)
  }, [conversations])

  /**
   * Get conversations that need attention
   */
  const getConversationsNeedingAttention = useCallback(() => {
    return conversations.filter(conv => conv.needsAttention)
  }, [conversations])

  /**
   * Get high priority conversations
   */
  const getHighPriorityConversations = useCallback(() => {
    return conversations.filter(conv => conv.priority === 'high')
  }, [conversations])

  /**
   * Sort conversations by different criteria
   */
  const sortConversations = useCallback((sortBy = 'latest') => {
    const sorted = [...conversations]

    switch (sortBy) {
      case 'latest':
        return sorted.sort((a, b) =>
          new Date(b.last_message_at || b.created_at) - new Date(a.last_message_at || a.created_at)
        )

      case 'priority':
        return sorted.sort((a, b) => {
          const priorityOrder = { high: 3, medium: 2, low: 1 }
          return priorityOrder[b.priority] - priorityOrder[a.priority]
        })

      case 'status':
        return sorted.sort((a, b) => {
          const statusOrder = { escalated: 4, active: 3, paused: 2, completed: 1 }
          return statusOrder[b.session_status] - statusOrder[a.session_status]
        })

      case 'agent':
        return sorted.sort((a, b) => (a.agent_name || '').localeCompare(b.agent_name || ''))

      case 'lead':
        return sorted.sort((a, b) => (a.lead_name || '').localeCompare(b.lead_name || ''))

      default:
        return sorted
    }
  }, [conversations])

  /**
   * Search conversations by lead name, agent name, or content
   */
  const searchConversations = useCallback((query) => {
    if (!query.trim()) return conversations

    const lowercaseQuery = query.toLowerCase()
    return conversations.filter(conv =>
      (conv.lead_name || '').toLowerCase().includes(lowercaseQuery) ||
      (conv.agent_name || '').toLowerCase().includes(lowercaseQuery) ||
      (conv.session_goal || '').toLowerCase().includes(lowercaseQuery)
    )
  }, [conversations])

  /**
   * Get conversation by ID
   */
  const getConversationById = useCallback((sessionId) => {
    return conversations.find(conv => conv.session_id === sessionId)
  }, [conversations])

  /**
   * Update a specific conversation in the list
   */
  const updateConversation = useCallback((sessionId, updates) => {
    setConversations(prev =>
      prev.map(conv =>
        conv.session_id === sessionId
          ? {
              ...conv,
              ...updates,
              status: chatUtils.getConversationStatus({ ...conv, ...updates }),
              needsAttention: chatUtils.needsAttention({ ...conv, ...updates }),
              priority: chatUtils.getPriority({ ...conv, ...updates }),
              formattedTime: chatUtils.formatMessageTime(updates.last_message_at || conv.last_message_at || conv.created_at)
            }
          : conv
      )
    )
  }, [])

  // Effects
  useEffect(() => {
    loadConversations()
  }, [loadConversations])

  useEffect(() => {
    if (!loading) {
      startPolling()
    }

    return () => {
      stopPolling()
    }
  }, [loading, startPolling, stopPolling])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPolling()
    }
  }, [stopPolling])

  return {
    // State
    conversations,
    loading,
    error,
    stats,

    // Functions
    refreshConversations,
    startPolling,
    stopPolling,

    // Data access
    getConversationsByStatus,
    getConversationsNeedingAttention,
    getHighPriorityConversations,
    sortConversations,
    searchConversations,
    getConversationById,
    updateConversation
  }
}