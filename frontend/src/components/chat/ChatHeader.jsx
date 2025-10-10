import { ArrowLeft, Settings, User, RefreshCw, WifiOff } from 'lucide-react'

/**
 * Header component for the chat interface
 * @param {Object} props
 * @param {Object} props.leadInfo - Lead information
 * @param {Object} props.sessionInfo - Session information
 * @param {boolean} props.businessOwnerMode - Business owner mode active
 * @param {string} props.connectionStatus - Connection status ('connected', 'disconnected')
 * @param {Function} props.onTakeOver - Take over conversation handler
 * @param {Function} props.onReleaseControl - Release control handler
 * @param {Function} props.onLeadClick - Lead profile click handler
 * @param {Function} props.onAgentClick - Agent settings click handler
 * @param {Function} props.onRefresh - Refresh messages handler
 * @param {boolean} props.isTyping - Is agent typing
 * @param {boolean} props.compact - Compact mode
 */
export function ChatHeader({
  leadInfo,
  sessionInfo,
  businessOwnerMode,
  connectionStatus,
  onTakeOver,
  onReleaseControl,
  onLeadClick,
  onAgentClick,
  onRefresh,
  isTyping,
  compact = false
}) {
  const agentName = sessionInfo?.agent?.name || 'Agent'

  // Render a loading state or a fallback if leadInfo is not available
  if (!leadInfo) {
    return (
      <div className={`bg-white border-b border-gray-200 px-4 ${compact ? 'py-2' : 'py-3'}`}>
        <div className="flex items-center justify-between h-16">
            <div className="animate-pulse flex space-x-4 w-full">
                <div className="rounded-full bg-slate-200 h-10 w-10"></div>
                <div className="flex-1 space-y-2 py-1">
                  <div className="h-4 bg-slate-200 rounded w-3/4"></div>
                  <div className="h-3 bg-slate-200 rounded w-1/2"></div>
                </div>
            </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`bg-white border-b border-gray-200 px-4 ${compact ? 'py-2' : 'py-3'}`}>
      <div className="flex items-center justify-between">
        {/* Left Side: Lead Info */}
        <div className="flex items-center gap-4">
          {!compact && (
            <button
              onClick={onLeadClick}
              className="flex items-center gap-2 text-left hover:bg-gray-100 p-2 rounded-lg"
            >
              <div className="w-10 h-10 rounded-full bg-green-500 flex items-center justify-center text-white">
                <User className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">{leadInfo.name}</h1>
                <p className="text-sm text-gray-500">
                  {leadInfo.service_requested || 'Unknown Service'}
                </p>
              </div>
            </button>
          )}
        </div>

        {/* Right Side: Agent Info & Actions */}
        <div className="flex items-center gap-4">
          {/* Agent Status Banner */}
          {sessionInfo && !businessOwnerMode && (
            <div className="flex items-center gap-2 px-3 py-1 bg-green-50 border border-green-200 rounded-full">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-green-700">
                {isTyping ? `${agentName} is responding...` : `${agentName} is managing this conversation`}
              </span>
            </div>
          )}

          {sessionInfo && (
            <button
              onClick={onAgentClick}
              className="flex items-center gap-2 text-left hover:bg-gray-100 p-2 rounded-lg"
            >
              <div className="relative">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white ${
                  businessOwnerMode ? 'bg-gray-500' : 'bg-blue-500'
                }`}>
                  <Settings className="h-5 w-5" />
                </div>
                {isTyping && !businessOwnerMode && (
                  <span className="absolute bottom-0 right-0 block h-3 w-3 rounded-full bg-green-400 border-2 border-white animate-pulse" />
                )}
              </div>
              <div>
                <h2 className="text-base font-medium text-gray-800">{agentName}</h2>
                <p className={`text-sm ${
                  businessOwnerMode
                    ? 'text-gray-500'
                    : isTyping
                      ? 'text-green-600'
                      : 'text-blue-600'
                }`}>
                  {businessOwnerMode
                    ? 'Paused'
                    : isTyping
                      ? 'Typing...'
                      : 'Active'
                  }
                </p>
              </div>
            </button>
          )}

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={onRefresh}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full"
              title="Refresh Conversation"
            >
              <RefreshCw className="h-5 w-5" />
            </button>

            {!businessOwnerMode ? (
              <button
                onClick={onTakeOver}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
              >
                Take Over
              </button>
            ) : (
              <button
                onClick={onReleaseControl}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg text-sm font-medium hover:bg-gray-300"
              >
                Release Control
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
