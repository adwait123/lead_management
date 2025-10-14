import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ChatContainer } from '../components/chat/ChatContainer'
import { leadsAPI, chatAPI } from '../lib/api'
import {
  ArrowLeft,
  ExternalLink,
  Phone,
  Mail,
  Building2,
  Calendar,
  User,
  Settings,
  AlertCircle
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'

/**
 * Individual lead chat page
 */
export function LeadChat() {
  const { leadId } = useParams()
  const navigate = useNavigate()

  const [lead, setLead] = useState(null)
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [businessOwnerMode, setBusinessOwnerMode] = useState(false)
  const [showLeadDetails, setShowLeadDetails] = useState(false)

  /**
   * Load lead and session data
   */
  useEffect(() => {
    const loadData = async () => {
      if (!leadId) return

      try {
        setLoading(true)

        // Load lead details
        const leadResponse = await leadsAPI.getById(leadId)
        const leadData = leadResponse.data
        setLead(leadData)

        // Load active session for this lead
        try {
          const sessionResponse = await chatAPI.getLeadActiveSession(leadId)
          if (sessionResponse.data.has_active_session) {
            setSession(sessionResponse.data.session)
          }
        } catch (sessionError) {
          console.warn('No active session found for lead:', leadId)
        }

      } catch (err) {
        console.error('Error loading lead data:', err)
        setError('Failed to load lead information')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [leadId])

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

  /**
   * Handle lead profile click
   */
  const handleLeadClick = () => {
    setShowLeadDetails(true)
  }

  /**
   * Handle agent profile click
   */
  const handleAgentClick = () => {
    if (session?.agent?.id) {
      navigate(`/agents/edit/${session.agent.id}`)
    }
  }

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-500">Loading conversation...</p>
        </div>
      </div>
    )
  }

  if (error || !lead) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Unable to Load Conversation
          </h3>
          <p className="text-gray-500 mb-4">
            {error || 'The requested lead could not be found.'}
          </p>
          <Button onClick={() => navigate('/conversations')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Conversations
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/conversations')}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>

            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                Chat with {lead.name}
              </h1>
              <p className="text-sm text-gray-500">
                {lead.service_requested} • {lead.source}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleLeadClick}
            >
              <User className="h-4 w-4 mr-2" />
              Lead Details
            </Button>

            {session?.agent && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleAgentClick}
              >
                <Settings className="h-4 w-4 mr-2" />
                Agent Settings
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Interface */}
        <div className={`${showLeadDetails ? 'flex-1' : 'w-full'} flex flex-col h-full transition-all duration-300`}>
          <ChatContainer
            leadId={lead.id}
            leadInfo={lead}
            sessionInfo={session}
            businessOwnerMode={businessOwnerMode}
            onTakeOver={handleTakeOver}
            onReleaseControl={handleReleaseControl}
            onLeadClick={handleLeadClick}
            onAgentClick={handleAgentClick}
            quickReplies={[
              "Thanks for your interest!",
              "Can you provide more details?",
              "I'll get back to you within 24 hours.",
              "Let me transfer you to a specialist.",
              "Would you like to schedule a consultation?"
            ]}
          />
        </div>

        {/* Lead Details Sidebar */}
        {showLeadDetails && (
          <div className="w-80 border-l border-gray-200 bg-white overflow-y-auto">
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Lead Details</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowLeadDetails(false)}
                >
                  ×
                </Button>
              </div>

              {/* Lead Information */}
              <Card className="mb-4">
                <CardHeader>
                  <CardTitle className="text-sm">Contact Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-gray-400" />
                    <span className="font-medium">{lead.name}</span>
                  </div>

                  {lead.email && (
                    <div className="flex items-center gap-2">
                      <Mail className="h-4 w-4 text-gray-400" />
                      <a
                        href={`mailto:${lead.email}`}
                        className="text-blue-600 hover:underline"
                      >
                        {lead.email}
                      </a>
                    </div>
                  )}

                  {lead.phone && (
                    <div className="flex items-center gap-2">
                      <Phone className="h-4 w-4 text-gray-400" />
                      <a
                        href={`tel:${lead.phone}`}
                        className="text-blue-600 hover:underline"
                      >
                        {lead.phone}
                      </a>
                    </div>
                  )}

                  {lead.company && (
                    <div className="flex items-center gap-2">
                      <Building2 className="h-4 w-4 text-gray-400" />
                      <span>{lead.company}</span>
                    </div>
                  )}

                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-gray-400" />
                    <span>Created {new Date(lead.created_at).toLocaleDateString()}</span>
                  </div>
                </CardContent>
              </Card>

              {/* Lead Status */}
              <Card className="mb-4">
                <CardHeader>
                  <CardTitle className="text-sm">Lead Status</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Status:</span>
                    <span className="capitalize font-medium">{lead.status}</span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-gray-600">Source:</span>
                    <span className="font-medium">{lead.source}</span>
                  </div>

                  {lead.service_requested && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Service:</span>
                      <span className="font-medium">{lead.service_requested}</span>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Session Information */}
              {session && (
                <Card className="mb-4">
                  <CardHeader>
                    <CardTitle className="text-sm">Active Session</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Agent:</span>
                      <span className="font-medium">{session.agent?.name}</span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-gray-600">Status:</span>
                      <span className="capitalize font-medium">{session.session_status}</span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-gray-600">Messages:</span>
                      <span className="font-medium">{session.message_count || 0}</span>
                    </div>

                    {session.session_goal && (
                      <div>
                        <span className="text-gray-600 block mb-1">Goal:</span>
                        <span className="text-sm">{session.session_goal}</span>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Notes */}
              {lead.notes && lead.notes.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Notes</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {lead.notes.map((note, index) => (
                        <div key={index} className="border-l-2 border-gray-200 pl-3">
                          <div className="text-sm text-gray-600 mb-1">
                            {note.author} • {new Date(note.timestamp).toLocaleDateString()}
                          </div>
                          <div className="text-sm">{note.content}</div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Actions */}
              <div className="mt-6 space-y-2">
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => navigate(`/leads?highlight=${lead.id}`)}
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View in Leads
                </Button>

                {lead.phone && (
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => window.open(`tel:${lead.phone}`)}
                  >
                    <Phone className="h-4 w-4 mr-2" />
                    Call Lead
                  </Button>
                )}

                {lead.email && (
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => window.open(`mailto:${lead.email}`)}
                  >
                    <Mail className="h-4 w-4 mr-2" />
                    Email Lead
                  </Button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default LeadChat