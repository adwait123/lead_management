import { useState } from 'react'
import {
  Bot,
  User,
  Search,
  Filter,
  MoreVertical,
  MessageCircle,
  Clock,
  AlertTriangle,
  CheckCircle,
  Pause,
  Phone,
  Mail,
  ExternalLink
} from 'lucide-react'
import { Button } from '../ui/Button'
import { Card, CardContent } from '../ui/Card'
import { chatUtils } from '../../services/chatAPI'

/**
 * Individual conversation card component
 * @param {Object} props
 * @param {Object} props.conversation - Conversation object
 * @param {Function} props.onSelect - Function called when conversation is selected
 * @param {Function} props.onLeadClick - Function called when lead is clicked
 * @param {Function} props.onAgentClick - Function called when agent is clicked
 * @param {boolean} props.isSelected - Whether this conversation is selected
 * @param {boolean} props.compact - Compact display mode
 */
export function ConversationCard({
  conversation,
  onSelect,
  onLeadClick,
  onAgentClick,
  isSelected = false,
  compact = false
}) {
  const [showActions, setShowActions] = useState(false)

  const handleCardClick = () => {
    onSelect?.(conversation)
  }

  const handleLeadClick = (e) => {
    e.stopPropagation()
    onLeadClick?.(conversation)
  }

  const handleAgentClick = (e) => {
    e.stopPropagation()
    onAgentClick?.(conversation)
  }

  const getStatusIcon = () => {
    switch (conversation.session_status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'escalated':
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      case 'paused':
        return <Pause className="h-4 w-4 text-yellow-500" />
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-blue-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getPriorityStyle = () => {
    switch (conversation.priority) {
      case 'high':
        return 'border-l-4 border-red-500'
      case 'medium':
        return 'border-l-4 border-yellow-500'
      default:
        return 'border-l-4 border-transparent'
    }
  }

  return (
    <Card
      className={`
        cursor-pointer transition-all duration-200 hover:shadow-md
        ${isSelected ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:bg-gray-50'}
        ${getPriorityStyle()}
        ${conversation.needsAttention ? 'bg-yellow-50' : ''}
      `}
      onClick={handleCardClick}
    >
      <CardContent className={`${compact ? 'p-3' : 'p-4'}`}>
        <div className="flex items-start gap-3">
          {/* Lead Avatar */}
          <div
            className={`
              flex-shrink-0 ${compact ? 'w-8 h-8' : 'w-10 h-10'}
              bg-green-500 rounded-full flex items-center justify-center
              hover:bg-green-600 transition-colors
            `}
            onClick={handleLeadClick}
          >
            <User className={`${compact ? 'h-4 w-4' : 'h-5 w-5'} text-white`} />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Header Row */}
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3
                    className={`
                      ${compact ? 'text-sm' : 'text-base'} font-medium text-gray-900
                      truncate hover:text-blue-600 cursor-pointer
                    `}
                    onClick={handleLeadClick}
                  >
                    {conversation.lead_name || 'Unknown Lead'}
                  </h3>

                  {getStatusIcon()}

                  {conversation.needsAttention && (
                    <span className="inline-block w-2 h-2 bg-red-500 rounded-full" />
                  )}
                </div>

                <div className="flex items-center gap-2 text-sm text-gray-500">
                  {/* Agent Info */}
                  <div
                    className="flex items-center gap-1 hover:text-blue-600 cursor-pointer"
                    onClick={handleAgentClick}
                  >
                    <Bot className="h-3 w-3" />
                    <span>{conversation.agent_name || 'Agent'}</span>
                  </div>

                  <span>•</span>

                  {/* Message Count */}
                  <div className="flex items-center gap-1">
                    <MessageCircle className="h-3 w-3" />
                    <span>{conversation.message_count || 0}</span>
                  </div>

                  <span>•</span>

                  {/* Time */}
                  <span>{conversation.formattedTime}</span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-1">
                <div className="relative">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      setShowActions(!showActions)
                    }}
                  >
                    <MoreVertical className="h-3 w-3" />
                  </Button>

                  {showActions && (
                    <div className="absolute right-0 top-full mt-1 w-40 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                      <div className="py-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            onLeadClick?.(conversation)
                            setShowActions(false)
                          }}
                          className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                        >
                          <ExternalLink className="h-3 w-3" />
                          View Lead
                        </button>

                        {conversation.lead_phone && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              window.open(`tel:${conversation.lead_phone}`)
                              setShowActions(false)
                            }}
                            className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                          >
                            <Phone className="h-3 w-3" />
                            Call
                          </button>
                        )}

                        {conversation.lead_email && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              window.open(`mailto:${conversation.lead_email}`)
                              setShowActions(false)
                            }}
                            className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                          >
                            <Mail className="h-3 w-3" />
                            Email
                          </button>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Session Goal */}
            {conversation.session_goal && (
              <div className={`${compact ? 'text-xs' : 'text-sm'} text-gray-600 mb-2 truncate`}>
                Goal: {conversation.session_goal}
              </div>
            )}

            {/* Last Message Preview */}
            {conversation.last_message_content && (
              <div className={`${compact ? 'text-xs' : 'text-sm'} text-gray-500 truncate`}>
                {conversation.last_message_from === 'agent' ? '🤖 ' : '👤 '}
                {conversation.last_message_content}
              </div>
            )}

            {/* Tags */}
            <div className="flex items-center gap-2 mt-2">
              {conversation.trigger_type && (
                <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                  {conversation.trigger_type.replace('_', ' ')}
                </span>
              )}

              {conversation.priority === 'high' && (
                <span className="inline-block px-2 py-1 text-xs bg-red-100 text-red-600 rounded">
                  High Priority
                </span>
              )}

              {conversation.needsAttention && (
                <span className="inline-block px-2 py-1 text-xs bg-yellow-100 text-yellow-600 rounded">
                  Needs Attention
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Close dropdown when clicking outside */}
        {showActions && (
          <div
            className="fixed inset-0 z-40"
            onClick={(e) => {
              e.stopPropagation()
              setShowActions(false)
            }}
          />
        )}
      </CardContent>
    </Card>
  )
}

/**
 * Conversations list component with filtering and search
 * @param {Object} props
 * @param {Array} props.conversations - Array of conversation objects
 * @param {Function} props.onConversationSelect - Function called when conversation is selected
 * @param {Function} props.onLeadClick - Function called when lead is clicked
 * @param {Function} props.onAgentClick - Function called when agent is clicked
 * @param {string} props.selectedConversationId - ID of selected conversation
 * @param {boolean} props.loading - Loading state
 * @param {string} props.error - Error message
 * @param {Function} props.onRefresh - Refresh function
 * @param {boolean} props.compact - Compact display mode
 */
export function ConversationsList({
  conversations = [],
  onConversationSelect,
  onLeadClick,
  onAgentClick,
  selectedConversationId,
  loading = false,
  error = null,
  onRefresh,
  compact = false
}) {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [sortBy, setSortBy] = useState('latest')
  const [showFilters, setShowFilters] = useState(false)

  // Filter and sort conversations
  const filteredConversations = conversations
    .filter(conv => {
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase()
        return (
          (conv.lead_name || '').toLowerCase().includes(searchLower) ||
          (conv.agent_name || '').toLowerCase().includes(searchLower) ||
          (conv.session_goal || '').toLowerCase().includes(searchLower)
        )
      }
      return true
    })
    .filter(conv => {
      if (statusFilter) {
        return conv.session_status === statusFilter
      }
      return true
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'priority':
          const priorityOrder = { high: 3, medium: 2, low: 1 }
          return priorityOrder[b.priority] - priorityOrder[a.priority]
        case 'status':
          return a.session_status.localeCompare(b.session_status)
        case 'agent':
          return (a.agent_name || '').localeCompare(b.agent_name || '')
        case 'lead':
          return (a.lead_name || '').localeCompare(b.lead_name || '')
        default: // latest
          const aTime = new Date(a.last_message_at || a.created_at)
          const bTime = new Date(b.last_message_at || b.created_at)
          return bTime - aTime
      }
    })

  const priorityConversations = filteredConversations.filter(conv => conv.needsAttention)

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Conversations</h2>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter className="h-4 w-4" />
            </Button>
            {onRefresh && (
              <Button variant="outline" size="sm" onClick={onRefresh}>
                <Clock className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Search */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="flex gap-2 mb-4">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="escalated">Escalated</option>
              <option value="completed">Completed</option>
            </select>

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="latest">Latest Activity</option>
              <option value="priority">Priority</option>
              <option value="status">Status</option>
              <option value="agent">Agent</option>
              <option value="lead">Lead Name</option>
            </select>
          </div>
        )}

        {/* Stats */}
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span>{filteredConversations.length} conversations</span>
          {priorityConversations.length > 0 && (
            <span className="text-red-600">
              {priorityConversations.length} need attention
            </span>
          )}
        </div>
      </div>

      {/* Priority Conversations */}
      {priorityConversations.length > 0 && (
        <div className="p-4 bg-yellow-50 border-b border-yellow-200">
          <h3 className="text-sm font-medium text-yellow-800 mb-2 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            Needs Attention ({priorityConversations.length})
          </h3>
          <div className="space-y-2">
            {priorityConversations.slice(0, 3).map(conversation => (
              <ConversationCard
                key={conversation.session_id}
                conversation={conversation}
                onSelect={onConversationSelect}
                onLeadClick={onLeadClick}
                onAgentClick={onAgentClick}
                isSelected={selectedConversationId === conversation.session_id}
                compact={true}
              />
            ))}
          </div>
        </div>
      )}

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : error ? (
          <div className="p-4 text-center text-red-600">
            {error}
          </div>
        ) : filteredConversations.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <MessageCircle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No conversations found
            </h3>
            <p className="text-gray-500">
              {searchTerm || statusFilter
                ? 'Try adjusting your search or filters'
                : 'Conversations will appear here once leads start engaging with your agents'
              }
            </p>
          </div>
        ) : (
          <div className="p-4 space-y-3">
            {filteredConversations.map(conversation => (
              <ConversationCard
                key={conversation.session_id}
                conversation={conversation}
                onSelect={onConversationSelect}
                onLeadClick={onLeadClick}
                onAgentClick={onAgentClick}
                isSelected={selectedConversationId === conversation.session_id}
                compact={compact}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}