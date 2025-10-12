import { useState, useEffect } from 'react'
import { MessageList } from './MessageList'
import { MessageInput } from './MessageInput'
import { ChatHeader } from './ChatHeader'
import { useChat } from '../../hooks/useChat'
import { chatAPI } from '../../services/chatAPI'
import { AlertCircle, WifiOff } from 'lucide-react'

/**
 * Main chat container component that combines all chat functionality
 * @param {Object} props
 * @param {string} props.leadExternalId - External ID of the lead
 * @param {Object} props.leadInfo - Lead information object
 * @param {Object} props.sessionInfo - Session information object
 * @param {boolean} props.businessOwnerMode - Whether business owner is active in chat
 * @param {Function} props.onTakeOver - Function to take over chat
 * @param {Function} props.onReleaseControl - Function to release control back to agent
 * @param {Function} props.onLeadClick - Function to handle lead profile click
 * @param {Function} props.onAgentClick - Function to handle agent profile click
 * @param {Array} props.quickReplies - Array of quick reply options
 * @param {boolean} props.compact - Compact mode for smaller displays
 */
export function ChatContainer({
  leadExternalId,
  leadInfo,
  sessionInfo,
  businessOwnerMode = false,
  onTakeOver,
  onReleaseControl,
  onLeadClick,
  onAgentClick,
  quickReplies = [],
  compact = false
}) {
  const [isTyping, setIsTyping] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState('connected')
  const [takeoverError, setTakeoverError] = useState(null)

  // Use chat hook
  const {
    messages,
    loading,
    error,
    sending,
    newMessage,
    setNewMessage,
    messagesEndRef,
    sendMessage,
    simulateLeadMessage,
    refreshMessages,
    conversationInfo,
    sessionInfo: hookSessionInfo
  } = useChat(leadExternalId, {
    pollInterval: 5000,
    autoScroll: true
  })

  // Use session info from hook if available, fallback to prop
  const currentSessionInfo = hookSessionInfo || sessionInfo

  /**
   * Handle sending a message
   */
  const handleSendMessage = async (content) => {
    if (businessOwnerMode) {
      // Send as business owner
      return await sendMessage(content, {
        sender_type: 'business_owner',
        take_over: true
      })
    } else {
      // Simulate lead message for testing
      return await simulateLeadMessage(content)
    }
  }

  /**
   * Handle taking over the conversation
   */
  const handleTakeOver = async () => {
    if (!currentSessionInfo?.id) {
      console.error('No session ID available for takeover')
      return
    }

    try {
      const response = await chatAPI.takeoverSession(currentSessionInfo.id, {
        reason: 'Business owner manual takeover'
      })

      if (response.data.success) {
        console.log('Session takeover successful:', response.data)
        // Call the parent handler to update UI state
        if (onTakeOver) {
          onTakeOver()
        }
      }
    } catch (error) {
      console.error('Failed to take over session:', error)
      setTakeoverError('Failed to take over conversation')
    }
  }

  /**
   * Handle releasing control back to agent
   */
  const handleReleaseControl = async () => {
    if (!currentSessionInfo?.id) {
      console.error('No session ID available for release')
      return
    }

    try {
      const response = await chatAPI.releaseSession(currentSessionInfo.id)

      if (response.data.success) {
        console.log('Session release successful:', response.data)
        // Call the parent handler to update UI state
        if (onReleaseControl) {
          onReleaseControl()
        }
      }
    } catch (error) {
      console.error('Failed to release session:', error)
      setTakeoverError('Failed to release conversation back to agent')
    }
  }

  /**
   * Monitor connection status
   */
  useEffect(() => {
    const handleOnline = () => setConnectionStatus('connected')
    const handleOffline = () => setConnectionStatus('disconnected')

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  /**
   * Simulate typing indicator when agent is responding
   */
  useEffect(() => {
    if (sending && !businessOwnerMode) {
      setIsTyping(true)
      const timer = setTimeout(() => {
        setIsTyping(false)
      }, 3000)

      return () => clearTimeout(timer)
    } else {
      setIsTyping(false)
    }
  }, [sending, businessOwnerMode])

  return (
    <div className={`flex flex-col h-full bg-white ${compact ? 'text-sm' : ''}`}>
      {/* Chat Header */}
      <ChatHeader
        leadInfo={leadInfo}
        sessionInfo={currentSessionInfo}
        businessOwnerMode={businessOwnerMode}
        connectionStatus={connectionStatus}
        onTakeOver={handleTakeOver}
        onReleaseControl={handleReleaseControl}
        onLeadClick={onLeadClick}
        onAgentClick={onAgentClick}
        onRefresh={refreshMessages}
        isTyping={isTyping}
        compact={compact}
      />

      {/* Connection Status Banner */}
      {connectionStatus === 'disconnected' && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-2">
          <div className="flex items-center gap-2 text-red-700">
            <WifiOff className="h-4 w-4" />
            <span className="text-sm">
              Connection lost. Messages may not be delivered until connection is restored.
            </span>
          </div>
        </div>
      )}

      {/* Business Owner Takeover Notice */}
      {businessOwnerMode && (
        <div className="bg-orange-50 border-b border-orange-200 px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
              <div>
                <span className="text-sm font-medium text-orange-800">
                  You have taken over this conversation
                </span>
                <p className="text-xs text-orange-600 mt-1">
                  The agent is paused and will not respond to new messages
                </p>
              </div>
            </div>
            <button
              onClick={handleReleaseControl}
              className="px-3 py-1 text-sm bg-orange-100 text-orange-700 hover:bg-orange-200 rounded-lg border border-orange-300"
            >
              Return to Agent
            </button>
          </div>
        </div>
      )}

      {/* Takeover Error Notice */}
      {takeoverError && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-red-700">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm font-medium">{takeoverError}</span>
            </div>
            <button
              onClick={() => setTakeoverError(null)}
              className="text-sm text-red-600 hover:text-red-800 underline"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Agent Active Notice */}
      {!businessOwnerMode && currentSessionInfo && (
        <div className="bg-green-50 border-b border-green-200 px-4 py-2">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-green-700">
              {isTyping
                ? `${currentSessionInfo.agent?.name || 'Agent'} is responding to the lead...`
                : `${currentSessionInfo.agent?.name || 'Agent'} is actively managing this conversation`
              }
            </span>
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 relative overflow-hidden">
        <MessageList
          messages={messages}
          loading={loading}
          error={error}
          onRefresh={refreshMessages}
          showTyping={isTyping}
          typingSender={currentSessionInfo?.agent?.name || 'Agent'}
          messagesEndRef={messagesEndRef}
          compact={compact}
        />
      </div>

      {/* Message Input */}
      <MessageInput
        value={newMessage}
        onChange={(e) => setNewMessage(e.target.value)}
        onSendMessage={handleSendMessage}
        sending={sending}
        disabled={connectionStatus === 'disconnected'}
        placeholder={
          businessOwnerMode
            ? 'Type your message as business owner...'
            : 'Type a message to simulate lead response...'
        }
        quickReplies={quickReplies}
        onQuickReplySelect={(reply) => {
          setNewMessage(reply)
        }}
      />
    </div>
  )
}

/**
 * Chat container with error boundary
 */
export function ChatContainerWithErrorBoundary(props) {
  const [hasError, setHasError] = useState(false)
  const [errorInfo, setErrorInfo] = useState(null)

  // Reset error state when props change
  useEffect(() => {
    setHasError(false)
    setErrorInfo(null)
  }, [props.leadExternalId])

  if (hasError) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8">
        <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Something went wrong
        </h3>
        <p className="text-gray-500 text-center mb-4">
          There was an error loading the chat. Please try refreshing the page.
        </p>
        {errorInfo && (
          <details className="text-sm text-gray-400 max-w-md">
            <summary>Error details</summary>
            <pre className="mt-2 whitespace-pre-wrap">{errorInfo}</pre>
          </details>
        )}
        <button
          onClick={() => {
            setHasError(false)
            setErrorInfo(null)
          }}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Try Again
        </button>
      </div>
    )
  }

  try {
    return <ChatContainer {...props} />
  } catch (error) {
    setHasError(true)
    setErrorInfo(error.toString())
    return null
  }
}

export default ChatContainerWithErrorBoundary