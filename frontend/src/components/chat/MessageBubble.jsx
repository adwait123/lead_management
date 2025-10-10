import { Bot, User, Clock, CheckCircle, XCircle } from 'lucide-react'
import { chatUtils } from '../../services/chatAPI'

/**
 * Individual message bubble component
 * @param {Object} props
 * @param {Object} props.message - Message object
 * @param {boolean} props.showTimestamp - Show timestamp (default: true)
 * @param {boolean} props.showAvatar - Show sender avatar (default: true)
 * @param {boolean} props.compact - Compact display mode (default: false)
 */
export function MessageBubble({
  message,
  showTimestamp = true,
  showAvatar = true,
  compact = false
}) {
  const senderInfo = chatUtils.getSenderInfo(message)
  const formattedTime = chatUtils.formatMessageTime(message.created_at)

  const getDeliveryStatus = () => {
    if (message.delivery_status === 'failed') {
      return { icon: XCircle, color: 'text-red-500', text: 'Failed' }
    }
    if (message.delivery_status === 'delivered') {
      return { icon: CheckCircle, color: 'text-green-500', text: 'Delivered' }
    }
    if (message.message_status === 'sent') {
      return { icon: Clock, color: 'text-gray-400', text: 'Sent' }
    }
    return null
  }

  const deliveryStatus = getDeliveryStatus()

  return (
    <div className={`flex gap-3 ${senderInfo.isAgent ? 'flex-row' : 'flex-row-reverse'} ${compact ? 'mb-2' : 'mb-4'}`}>
      {/* Avatar */}
      {showAvatar && (
        <div className={`flex-shrink-0 ${compact ? 'w-6 h-6' : 'w-8 h-8'}`}>
          <div className={`w-full h-full rounded-full ${senderInfo.avatarColor} flex items-center justify-center`}>
            {senderInfo.isAgent && <Bot className={`${compact ? 'h-3 w-3' : 'h-4 w-4'} text-white`} />}
            {senderInfo.isLead && <User className={`${compact ? 'h-3 w-3' : 'h-4 w-4'} text-white`} />}
            {senderInfo.isSystem && <span className={`${compact ? 'text-xs' : 'text-sm'} text-white font-bold`}>S</span>}
          </div>
        </div>
      )}

      {/* Message Content */}
      <div className={`flex flex-col ${senderInfo.isAgent ? 'items-start' : 'items-end'} max-w-[80%]`}>
        {/* Sender Name */}
        {!compact && (
          <div className={`${compact ? 'text-xs' : 'text-sm'} text-gray-600 mb-1 px-1`}>
            {senderInfo.name}
            {showTimestamp && (
              <span className="text-gray-400 ml-2">{formattedTime}</span>
            )}
          </div>
        )}

        {/* Message Bubble */}
        <div className={`
          relative px-4 py-2 rounded-lg shadow-sm
          ${senderInfo.isAgent
            ? 'bg-blue-50 border border-blue-200'
            : senderInfo.isLead
            ? 'bg-white border border-gray-200'
            : 'bg-gray-50 border border-gray-200'
          }
          ${compact ? 'px-3 py-1' : 'px-4 py-2'}
        `}>
          {/* Message Content */}
          <div className={`${compact ? 'text-sm' : 'text-base'} text-gray-900 whitespace-pre-wrap`}>
            {message.content}
          </div>

          {/* Message Metadata */}
          {message.message_metadata && Object.keys(message.message_metadata).length > 0 && (
            <div className="mt-2 pt-2 border-t border-gray-200">
              {/* AI Model Info */}
              {message.model_used && (
                <div className="text-xs text-gray-500">
                  Model: {message.model_used}
                  {message.response_time_ms && (
                    <span className="ml-2">• {message.response_time_ms}ms</span>
                  )}
                </div>
              )}

              {/* External Platform Info */}
              {message.external_platform && (
                <div className="text-xs text-gray-500">
                  via {message.external_platform}
                </div>
              )}
            </div>
          )}

          {/* Message bubble arrow */}
          <div className={`
            absolute top-2 w-2 h-2 transform rotate-45
            ${senderInfo.isAgent
              ? 'bg-blue-50 border-l border-b border-blue-200 -left-1'
              : 'bg-white border-r border-t border-gray-200 -right-1'
            }
          `} />
        </div>

        {/* Delivery Status and Timestamp (compact mode) */}
        <div className={`flex items-center gap-2 mt-1 px-1 ${senderInfo.isAgent ? 'flex-row' : 'flex-row-reverse'}`}>
          {compact && showTimestamp && (
            <span className="text-xs text-gray-400">{formattedTime}</span>
          )}

          {deliveryStatus && !senderInfo.isLead && (
            <div className="flex items-center gap-1">
              <deliveryStatus.icon className={`h-3 w-3 ${deliveryStatus.color}`} />
              <span className={`text-xs ${deliveryStatus.color}`}>
                {deliveryStatus.text}
              </span>
            </div>
          )}
        </div>

        {/* Error Message */}
        {message.error_message && (
          <div className="mt-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center gap-2">
              <XCircle className="h-4 w-4 text-red-500" />
              <span className="text-sm text-red-700">Error: {message.error_message}</span>
            </div>
          </div>
        )}

        {/* Quality Score */}
        {message.quality_score && (
          <div className="mt-1 px-1">
            <span className="text-xs text-gray-500">
              Quality: {Math.round(parseFloat(message.quality_score) * 100)}%
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * System message component for notifications and status updates
 */
export function SystemMessage({ message, compact = false }) {
  return (
    <div className={`flex justify-center ${compact ? 'my-2' : 'my-4'}`}>
      <div className={`
        px-3 py-1 bg-gray-100 border border-gray-200 rounded-full
        ${compact ? 'text-xs' : 'text-sm'} text-gray-600
      `}>
        <span className="font-medium">{message.sender_name || 'System'}:</span>{' '}
        {message.content}
      </div>
    </div>
  )
}

/**
 * Typing indicator component
 */
export function TypingIndicator({ senderName = 'Agent', compact = false }) {
  return (
    <div className={`flex gap-3 ${compact ? 'mb-2' : 'mb-4'}`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 ${compact ? 'w-6 h-6' : 'w-8 h-8'}`}>
        <div className="w-full h-full rounded-full bg-blue-500 flex items-center justify-center">
          <Bot className={`${compact ? 'h-3 w-3' : 'h-4 w-4'} text-white`} />
        </div>
      </div>

      {/* Typing Bubble */}
      <div className="flex flex-col items-start max-w-[80%]">
        <div className={`
          relative px-4 py-2 rounded-lg shadow-sm bg-blue-50 border border-blue-200
          ${compact ? 'px-3 py-1' : 'px-4 py-2'}
        `}>
          <div className="flex items-center gap-1">
            <span className={`${compact ? 'text-sm' : 'text-base'} text-gray-600`}>
              {senderName} is typing
            </span>
            <div className="flex gap-1 ml-2">
              <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>

          {/* Bubble arrow */}
          <div className="absolute top-2 w-2 h-2 transform rotate-45 bg-blue-50 border-l border-b border-blue-200 -left-1" />
        </div>
      </div>
    </div>
  )
}