import { useState, useEffect, useCallback, useRef } from 'react'
import { chatAPI, chatUtils } from '../services/chatAPI'

/**
 * Custom hook for managing individual chat conversations
 * @param {string} leadExternalId - External ID of the lead
 * @param {Object} options - Configuration options
 * @param {number} options.pollInterval - Polling interval in milliseconds (default: 5000)
 * @param {boolean} options.autoScroll - Auto scroll to bottom on new messages (default: true)
 * @returns {Object} Chat state and functions
 */
export function useChat(leadExternalId, options = {}) {
  const {
    pollInterval = 5000, // Poll every 5 seconds
    autoScroll = true
  } = options

  // State
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sending, setSending] = useState(false)
  const [conversationInfo, setConversationInfo] = useState(null)
  const [sessionInfo, setSessionInfo] = useState(null)
  const [newMessage, setNewMessage] = useState('')

  // Refs
  const messagesEndRef = useRef(null)
  const pollIntervalRef = useRef(null)
  const lastMessageTimestamp = useRef(null)

  /**
   * Scroll to bottom of messages
   */
  const scrollToBottom = useCallback(() => {
    if (autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [autoScroll])

  /**
   * Load conversation history
   */
  const loadMessages = useCallback(async (since = null) => {
    if (!leadExternalId) return

    try {
      const params = {}
      if (since) params.since_timestamp = since

      const response = await chatAPI.getConversationHistory(leadExternalId, params)

      if (response.data.success) {
        const newMessages = response.data.messages || []

        if (since) {
          // Append new messages
          setMessages(prev => [...prev, ...newMessages])
        } else {
          // Replace all messages
          setMessages(newMessages)
        }

        // Update last message timestamp
        if (newMessages.length > 0) {
          const latestMessage = newMessages[newMessages.length - 1]
          lastMessageTimestamp.current = latestMessage.created_at
        }

        // Set conversation info
        if (response.data.lead_id && !conversationInfo) {
          setConversationInfo({
            leadId: response.data.lead_id,
            leadExternalId: response.data.lead_external_id
          })

          // Fetch session information for takeover functionality
          fetchSessionInfo(response.data.lead_id)
        }
      }
    } catch (err) {
      console.error('Error loading messages:', err)
      setError('Failed to load messages')
    } finally {
      setLoading(false)
    }
  }, [leadExternalId, conversationInfo])

  /**
   * Fetch session information for takeover functionality
   */
  const fetchSessionInfo = useCallback(async (leadId) => {
    try {
      const response = await chatAPI.getLeadActiveSession(leadId)

      if (response.data.has_active_session && response.data.session) {
        setSessionInfo({
          id: response.data.session.session_id,
          agent: response.data.session.agent,
          lead: response.data.session.lead,
          session: response.data.session.session
        })
      }
    } catch (err) {
      console.error('Error fetching session info:', err)
      // Don't set error state for session info as it's not critical for basic functionality
    }
  }, [])

  /**
   * Poll for new messages
   */
  const pollForNewMessages = useCallback(async () => {
    if (!lastMessageTimestamp.current) return

    try {
      await loadMessages(lastMessageTimestamp.current)
    } catch (err) {
      console.error('Error polling for new messages:', err)
    }
  }, [loadMessages])

  /**
   * Send a message from the business owner
   */
  const sendMessage = useCallback(async (content, metadata = {}) => {
    if (!content.trim() || !conversationInfo) return

    setSending(true)
    try {
      // Send message through the system
      const messageData = {
        lead_id: conversationInfo.leadId,
        message: content.trim(),
        message_type: 'text',
        metadata: {
          ...metadata,
          sender: 'business_owner',
          platform: 'web_ui'
        }
      }

      const response = await chatAPI.sendBusinessMessage(messageData)

      if (response.data.success) {
        // Clear input
        setNewMessage('')

        // Immediately poll for new messages to get the sent message and any agent response
        setTimeout(() => {
          pollForNewMessages()
        }, 1000)

        return true
      } else {
        throw new Error(response.data.error || 'Failed to send message')
      }
    } catch (err) {
      console.error('Error sending message:', err)
      setError('Failed to send message')
      return false
    } finally {
      setSending(false)
    }
  }, [conversationInfo, pollForNewMessages])

  /**
   * Simulate a lead message (for testing)
   */
  const simulateLeadMessage = useCallback(async (content) => {
    if (!content.trim() || !conversationInfo) return

    try {
      const messageData = {
        yelp_lead_id: leadExternalId,
        conversation_id: `conv_${leadExternalId}`,
        message_content: content.trim(),
        sender: 'customer',
        timestamp: new Date().toISOString()
      }

      const response = await chatAPI.sendLeadMessage(messageData)

      if (response.data.success) {
        // Poll for new messages to get the lead message and agent response
        setTimeout(() => {
          pollForNewMessages()
        }, 1000)

        return true
      }
    } catch (err) {
      console.error('Error simulating lead message:', err)
      setError('Failed to simulate lead message')
      return false
    }
  }, [leadExternalId, conversationInfo, pollForNewMessages])

  /**
   * Start polling for new messages
   */
  const startPolling = useCallback(() => {
    if (pollIntervalRef.current) return

    pollIntervalRef.current = setInterval(pollForNewMessages, pollInterval)
  }, [pollForNewMessages, pollInterval])

  /**
   * Stop polling for new messages
   */
  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
  }, [])

  /**
   * Refresh messages manually
   */
  const refreshMessages = useCallback(() => {
    setLoading(true)
    loadMessages()
  }, [loadMessages])

  // Effects
  useEffect(() => {
    if (leadExternalId) {
      loadMessages()
    }
  }, [leadExternalId, loadMessages])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  useEffect(() => {
    if (!loading && leadExternalId) {
      startPolling()
    }

    return () => {
      stopPolling()
    }
  }, [loading, leadExternalId, startPolling, stopPolling])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPolling()
    }
  }, [stopPolling])

  return {
    // State
    messages,
    loading,
    error,
    sending,
    conversationInfo,
    sessionInfo,
    newMessage,
    setNewMessage,

    // Refs
    messagesEndRef,

    // Functions
    sendMessage,
    simulateLeadMessage,
    refreshMessages,
    startPolling,
    stopPolling,
    fetchSessionInfo,

    // Utilities
    formatMessageTime: chatUtils.formatMessageTime,
    getSenderInfo: chatUtils.getSenderInfo
  }
}