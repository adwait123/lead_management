import { useEffect, useRef, useState } from 'react'
import { RefreshCw, AlertCircle } from 'lucide-react'
import { MessageBubble, SystemMessage, TypingIndicator } from './MessageBubble'
import { Button } from '../ui/Button'

/**
 * Scrollable message list component
 * @param {Object} props
 * @param {Array} props.messages - Array of message objects
 * @param {boolean} props.loading - Loading state
 * @param {string} props.error - Error message
 * @param {Function} props.onRefresh - Refresh function
 * @param {boolean} props.autoScroll - Auto scroll to bottom (default: true)
 * @param {boolean} props.showTyping - Show typing indicator (default: false)
 * @param {string} props.typingSender - Name of typing sender
 * @param {boolean} props.compact - Compact display mode (default: false)
 * @param {Object} props.messagesEndRef - Ref for auto-scrolling
 */
export function MessageList({
  messages = [],
  loading = false,
  error = null,
  onRefresh,
  autoScroll = true,
  showTyping = false,
  typingSender = 'Agent',
  compact = false,
  messagesEndRef
}) {
  const listRef = useRef(null)
  const [isUserScrolling, setIsUserScrolling] = useState(false)
  const [showScrollToBottom, setShowScrollToBottom] = useState(false)

  /**
   * Check if user has scrolled away from bottom
   */
  const checkScrollPosition = () => {
    if (!listRef.current) return

    const { scrollTop, scrollHeight, clientHeight } = listRef.current
    const isAtBottom = scrollTop + clientHeight >= scrollHeight - 50 // 50px threshold

    setShowScrollToBottom(!isAtBottom && messages.length > 0)
    setIsUserScrolling(!isAtBottom)
  }

  /**
   * Scroll to bottom of messages
   */
  const scrollToBottom = () => {
    if (messagesEndRef?.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
    setIsUserScrolling(false)
    setShowScrollToBottom(false)
  }

  /**
   * Group messages by date for date separators
   */
  const groupMessagesByDate = (messages) => {
    const groups = []
    let currentDate = null

    messages.forEach((message) => {
      const messageDate = new Date(message.created_at).toDateString()

      if (messageDate !== currentDate) {
        groups.push({
          type: 'date-separator',
          date: messageDate,
          id: `date-${messageDate}`
        })
        currentDate = messageDate
      }

      groups.push({
        type: 'message',
        data: message,
        id: message.id
      })
    })

    return groups
  }

  /**
   * Format date for separator
   */
  const formatDateSeparator = (dateString) => {
    const date = new Date(dateString)
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)

    if (date.toDateString() === today.toDateString()) {
      return 'Today'
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday'
    } else {
      return date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }
  }

  // Auto-scroll effect
  useEffect(() => {
    if (autoScroll && !isUserScrolling) {
      scrollToBottom()
    }
  }, [messages, autoScroll, isUserScrolling])

  // Scroll event listener
  useEffect(() => {
    const listElement = listRef.current
    if (!listElement) return

    listElement.addEventListener('scroll', checkScrollPosition)
    return () => listElement.removeEventListener('scroll', checkScrollPosition)
  }, [])

  const messageGroups = groupMessagesByDate(messages)

  return (
    <div className="flex flex-col h-full relative">
      {/* Messages Container */}
      <div
        ref={listRef}
        className="flex-1 overflow-y-auto px-4 py-4 space-y-1"
        style={{ scrollBehavior: 'smooth', minHeight: 0 }}
      >
        {/* Loading State */}
        {loading && messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full py-12">
            <RefreshCw className="h-8 w-8 text-gray-400 animate-spin mb-4" />
            <p className="text-gray-500">Loading conversation...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="h-8 w-8 text-red-500 mb-4" />
            <p className="text-red-600 mb-4">{error}</p>
            {onRefresh && (
              <Button variant="outline" onClick={onRefresh}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            )}
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full py-12">
            <div className="text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">💬</span>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No messages yet</h3>
              <p className="text-gray-500">
                This conversation will appear here once messages are exchanged.
              </p>
            </div>
          </div>
        )}

        {/* Messages */}
        {messageGroups.map((group) => {
          if (group.type === 'date-separator') {
            return (
              <div key={group.id} className="flex justify-center my-6">
                <div className="px-3 py-1 bg-gray-100 border border-gray-200 rounded-full text-sm text-gray-600">
                  {formatDateSeparator(group.date)}
                </div>
              </div>
            )
          }

          const message = group.data

          // Render system messages differently
          if (message.sender_type === 'system') {
            return (
              <SystemMessage
                key={message.id}
                message={message}
                compact={compact}
              />
            )
          }

          return (
            <MessageBubble
              key={message.id}
              message={message}
              compact={compact}
              showTimestamp={!compact}
              showAvatar={!compact}
            />
          )
        })}

        {/* Typing Indicator */}
        {showTyping && (
          <TypingIndicator
            senderName={typingSender}
            compact={compact}
          />
        )}

        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </div>

      {/* Scroll to Bottom Button */}
      {showScrollToBottom && (
        <div className="absolute bottom-20 right-6">
          <Button
            variant="outline"
            size="sm"
            onClick={scrollToBottom}
            className="shadow-lg bg-white border-gray-300 hover:bg-gray-50"
          >
            <span className="mr-2">↓</span>
            Scroll to bottom
          </Button>
        </div>
      )}

      {/* Loading indicator for new messages */}
      {loading && messages.length > 0 && (
        <div className="flex justify-center py-2">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Loading new messages...
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * Message list with pagination support
 */
export function PaginatedMessageList({
  messages,
  loading,
  error,
  onRefresh,
  onLoadMore,
  hasMore = false,
  ...props
}) {
  const [loadingMore, setLoadingMore] = useState(false)

  const handleLoadMore = async () => {
    if (loadingMore || !hasMore || !onLoadMore) return

    setLoadingMore(true)
    try {
      await onLoadMore()
    } finally {
      setLoadingMore(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Load More Button */}
      {hasMore && (
        <div className="flex justify-center p-4 border-b border-gray-200">
          <Button
            variant="outline"
            onClick={handleLoadMore}
            disabled={loadingMore}
          >
            {loadingMore ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Loading...
              </>
            ) : (
              'Load earlier messages'
            )}
          </Button>
        </div>
      )}

      {/* Message List */}
      <MessageList
        messages={messages}
        loading={loading}
        error={error}
        onRefresh={onRefresh}
        {...props}
      />
    </div>
  )
}