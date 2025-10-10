import { useState, useRef, useEffect } from 'react'
import { Send, Paperclip, Smile, Mic, X, AlertCircle } from 'lucide-react'
import { Button } from '../ui/Button'

/**
 * Message input component with rich features
 * @param {Object} props
 * @param {Function} props.onSendMessage - Function to send message
 * @param {boolean} props.disabled - Input disabled state
 * @param {boolean} props.sending - Message sending state
 * @param {string} props.placeholder - Input placeholder
 * @param {number} props.maxLength - Maximum message length (default: 1000)
 * @param {boolean} props.showCharacterCount - Show character count (default: true)
 * @param {boolean} props.allowAttachments - Allow file attachments (default: false)
 * @param {boolean} props.allowEmoji - Allow emoji picker (default: false)
 * @param {boolean} props.allowVoice - Allow voice recording (default: false)
 * @param {string} props.value - Controlled input value
 * @param {Function} props.onChange - Controlled input change handler
 */
export function MessageInput({
  onSendMessage,
  disabled = false,
  sending = false,
  placeholder = 'Type your message...',
  maxLength = 1000,
  showCharacterCount = true,
  allowAttachments = false,
  allowEmoji = false,
  allowVoice = false,
  value: controlledValue,
  onChange: controlledOnChange
}) {
  const [internalValue, setInternalValue] = useState('')
  const [error, setError] = useState('')
  const textareaRef = useRef(null)

  // Use controlled or internal state
  const value = controlledValue !== undefined ? controlledValue : internalValue
  const setValue = controlledOnChange || setInternalValue

  /**
   * Handle input change with validation
   */
  const handleInputChange = (e) => {
    const newValue = e.target.value

    // Clear error when user starts typing
    if (error) setError('')

    // Enforce max length
    if (newValue.length <= maxLength) {
      setValue(newValue)
    }
  }

  /**
   * Handle key press events
   */
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      if (e.shiftKey) {
        // Allow new line with Shift+Enter
        return
      } else {
        // Send message with Enter
        e.preventDefault()
        handleSendMessage()
      }
    }
  }

  /**
   * Auto-resize textarea based on content
   */
  const autoResizeTextarea = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }

  /**
   * Handle sending message
   */
  const handleSendMessage = async () => {
    const trimmedValue = value.trim()

    // Validation
    if (!trimmedValue) {
      setError('Please enter a message')
      return
    }

    if (trimmedValue.length > maxLength) {
      setError(`Message too long (${trimmedValue.length}/${maxLength} characters)`)
      return
    }

    if (disabled || sending) {
      return
    }

    try {
      await onSendMessage(trimmedValue)
      setValue('')
      setError('')

      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    } catch (err) {
      setError('Failed to send message. Please try again.')
    }
  }

  /**
   * Handle file attachment
   */
  const handleAttachment = () => {
    // TODO: Implement file attachment functionality
    console.log('File attachment clicked')
  }

  /**
   * Handle emoji picker
   */
  const handleEmoji = () => {
    // TODO: Implement emoji picker functionality
    console.log('Emoji picker clicked')
  }

  /**
   * Handle voice recording
   */
  const handleVoice = () => {
    // TODO: Implement voice recording functionality
    console.log('Voice recording clicked')
  }

  // Auto-resize effect
  useEffect(() => {
    autoResizeTextarea()
  }, [value])

  const remainingChars = maxLength - value.length
  const isOverLimit = remainingChars < 0
  const isNearLimit = remainingChars < 50
  const canSend = value.trim().length > 0 && !isOverLimit && !disabled && !sending

  return (
    <div className="border-t border-gray-200 bg-white">
      {/* Error Message */}
      {error && (
        <div className="px-4 py-2 bg-red-50 border-b border-red-200">
          <div className="flex items-center gap-2 text-red-700">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">{error}</span>
            <button
              onClick={() => setError('')}
              className="ml-auto p-1 hover:bg-red-100 rounded"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="p-4">
        <div className="flex items-end gap-3">
          {/* Attachment Button */}
          {allowAttachments && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleAttachment}
              disabled={disabled}
              className="flex-shrink-0"
            >
              <Paperclip className="h-4 w-4" />
            </Button>
          )}

          {/* Input Container */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={value}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              placeholder={placeholder}
              disabled={disabled || sending}
              className={`
                w-full resize-none border border-gray-300 rounded-lg px-3 py-2
                focus:ring-2 focus:ring-blue-500 focus:border-transparent
                placeholder-gray-500 text-gray-900
                min-h-[44px] max-h-32
                ${disabled || sending ? 'bg-gray-50 cursor-not-allowed' : ''}
                ${isOverLimit ? 'border-red-500 focus:ring-red-500' : ''}
              `}
              rows={1}
            />

            {/* Character Count */}
            {showCharacterCount && (
              <div className={`
                absolute bottom-1 right-2 text-xs
                ${isOverLimit ? 'text-red-500' : isNearLimit ? 'text-yellow-600' : 'text-gray-400'}
              `}>
                {value.length}/{maxLength}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex items-end gap-2">
            {/* Emoji Button */}
            {allowEmoji && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleEmoji}
                disabled={disabled}
                className="flex-shrink-0"
              >
                <Smile className="h-4 w-4" />
              </Button>
            )}

            {/* Voice Button */}
            {allowVoice && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleVoice}
                disabled={disabled}
                className="flex-shrink-0"
              >
                <Mic className="h-4 w-4" />
              </Button>
            )}

            {/* Send Button */}
            <Button
              onClick={handleSendMessage}
              disabled={!canSend}
              size="sm"
              className="flex-shrink-0"
            >
              {sending ? (
                <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Hint Text */}
        <div className="mt-2 text-xs text-gray-500">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  )
}

/**
 * Quick reply buttons component
 */
export function QuickReplies({ replies = [], onSelect, disabled = false }) {
  if (!replies.length) return null

  return (
    <div className="px-4 pb-4">
      <div className="text-xs text-gray-600 mb-2">Quick replies:</div>
      <div className="flex flex-wrap gap-2">
        {replies.map((reply, index) => (
          <Button
            key={index}
            variant="outline"
            size="sm"
            onClick={() => onSelect(reply)}
            disabled={disabled}
            className="text-xs"
          >
            {reply}
          </Button>
        ))}
      </div>
    </div>
  )
}

/**
 * Message input with quick replies
 */
export function MessageInputWithQuickReplies({
  quickReplies = [],
  onQuickReplySelect,
  ...props
}) {
  const handleQuickReplySelect = (reply) => {
    if (onQuickReplySelect) {
      onQuickReplySelect(reply)
    } else if (props.onChange) {
      // If no custom handler, just insert the reply text
      props.onChange({ target: { value: reply } })
    }
  }

  return (
    <div>
      <MessageInput {...props} />
      <QuickReplies
        replies={quickReplies}
        onSelect={handleQuickReplySelect}
        disabled={props.disabled || props.sending}
      />
    </div>
  )
}