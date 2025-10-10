import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ConversationsList } from '../components/chat/ConversationsList'
import { ChatContainer } from '../components/chat/ChatContainer'
import { useConversations } from '../hooks/useConversations'
import { leadsAPI } from '../lib/api'
import {
  MessageCircle,
  Users,
  Clock,
  AlertTriangle,
  BarChart3,
  Eye,
  ExternalLink,
  Settings
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'

/**
 * Main conversations page with dashboard and chat interface
 */
export function Conversations() {
  const navigate = useNavigate()
  const [selectedConversation, setSelectedConversation] = useState(null)
  const [selectedLead, setSelectedLead] = useState(null)
  const [loadingLead, setLoadingLead] = useState(false)
  const [businessOwnerMode, setBusinessOwnerMode] = useState(false)
  const [showChat, setShowChat] = useState(false)

  // Use conversations hook
  const {
    conversations,
    loading,
    error,
    stats,
    refreshConversations,
    getConversationsNeedingAttention,
    getHighPriorityConversations
  } = useConversations({
    limit: 50,
    pollInterval: 10000,
    autoRefresh: true
  })

  /**
   * Handle conversation selection
   */
  const handleConversationSelect = async (conversation) => {
    if (selectedConversation?.session_id === conversation.session_id) {
      setShowChat(true)
      return
    }
    
    setSelectedConversation(conversation)
    setShowChat(true)
    setSelectedLead(null)
    setLoadingLead(true)

    try {
      const leadResponse = await leadsAPI.getById(conversation.lead_id)
      setSelectedLead(leadResponse.data)
    } catch (err) {
      console.error('Error loading lead details:', err)
      setSelectedLead(null)
    } finally {
      setLoadingLead(false)
    }
  }

  /**
   * Handle lead profile click
   */
  const handleLeadClick = (conversation) => {
    if (conversation.lead_id) {
      navigate(`/leads?highlight=${conversation.lead_id}`)
    }
  }

  /**
   * Handle agent profile click
   */
  const handleAgentClick = (conversation) => {
    if (conversation.agent_id) {
      navigate(`/agents?highlight=${conversation.agent_id}`)
    }
  }

  /**
   * Handle taking over conversation
   */
  const handleTakeOver = () => {
    setBusinessOwnerMode(true)
  }

  /**
   * Handle releasing control
   */
  const handleReleaseControl = () => {
    setBusinessOwnerMode(false)
  }

  const needsAttentionConversations = getConversationsNeedingAttention()
  const highPriorityConversations = getHighPriorityConversations()

  return (
    <div className="h-screen flex flex-col">
      {/* Page Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Conversations</h1>
            <p className="text-gray-500 mt-1">Monitor and manage lead conversations</p>
          </div>

          <div className="flex items-center gap-3">
            {/* Stats Cards */}
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <MessageCircle className="h-4 w-4 text-blue-500" />
                <span className="font-medium">{stats.active}</span>
                <span className="text-gray-500">Active</span>
              </div>

              {stats.needsAttention > 0 && (
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                  <span className="font-medium text-red-600">{stats.needsAttention}</span>
                  <span className="text-gray-500">Need Attention</span>
                </div>
              )}

              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-gray-400" />
                <span className="font-medium">{stats.total}</span>
                <span className="text-gray-500">Total</span>
              </div>
            </div>

            <Button
              variant="outline"
              onClick={refreshConversations}
              disabled={loading}
            >
              <Clock className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Conversations Sidebar */}
        <div className={`
          ${showChat ? 'w-80' : 'w-full max-w-4xl mx-auto'}
          border-r border-gray-200 bg-white flex flex-col transition-all duration-300
        `}>
          <ConversationsList
            conversations={conversations}
            onConversationSelect={handleConversationSelect}
            onLeadClick={handleLeadClick}
            onAgentClick={handleAgentClick}
            selectedConversationId={selectedConversation?.session_id}
            loading={loading}
            error={error}
            onRefresh={refreshConversations}
          />
        </div>

        {/* Chat Interface */}
        {showChat && selectedConversation && (
          <div className="flex-1 flex flex-col">
            {loadingLead && (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-500">Loading conversation...</p>
                </div>
              </div>
            )}
            {!loadingLead && selectedLead && (
              <ChatContainer
                leadExternalId={selectedLead.external_id}
                leadInfo={selectedLead}
                sessionInfo={selectedConversation}
                businessOwnerMode={businessOwnerMode}
                onTakeOver={handleTakeOver}
                onReleaseControl={handleReleaseControl}
                onLeadClick={() => handleLeadClick(selectedConversation)}
                onAgentClick={() => handleAgentClick(selectedConversation)}
                quickReplies={[
                  "Thanks for your interest!",
                  "Can you provide more details?",
                  "I'll get back to you within 24 hours.",
                  "Let me transfer you to a specialist.",
                  "Would you like to schedule a consultation?"
                ]}
              />
            )}
            {!loadingLead && !selectedLead && (
                <div className="h-full flex items-center justify-center">
                    <div className="text-center max-w-md">
                        <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">
                            Could not load lead details
                        </h3>
                        <p className="text-gray-500">
                            There was an issue fetching the details for this conversation.
                        </p>
                    </div>
                </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!showChat && (
          <div className="flex-1 flex items-center justify-center bg-gray-50">
            <div className="text-center max-w-md">
              <MessageCircle className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Select a Conversation
              </h3>
              <p className="text-gray-500 mb-6">
                Choose a conversation from the sidebar to start viewing and managing the chat.
              </p>

              {/* Quick Stats */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <Card>
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold text-blue-600 mb-1">
                      {stats.active}
                    </div>
                    <div className="text-gray-600">Active Chats</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4 text-center">
                    <div className="text-2xl font-bold text-red-600 mb-1">
                      {stats.needsAttention}
                    </div>
                    <div className="text-gray-600">Need Attention</div>
                  </CardContent>
                </Card>
              </div>

              {/* Quick Actions */}
              {needsAttentionConversations.length > 0 && (
                <div className="mt-6">
                  <h4 className="text-sm font-medium text-gray-900 mb-3">
                    Priority Actions
                  </h4>
                  <div className="space-y-2">
                    {needsAttentionConversations.slice(0, 3).map(conv => (
                      <button
                        key={conv.session_id}
                        onClick={() => handleConversationSelect(conv)}
                        className="w-full p-3 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 text-left"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium text-gray-900">
                              {conv.lead_name}
                            </div>
                            <div className="text-sm text-gray-500">
                              {conv.session_goal}
                            </div>
                          </div>
                          <AlertTriangle className="h-4 w-4 text-red-500" />
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Conversations
