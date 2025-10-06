import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import {
  Plus,
  Bot,
  Play,
  Pause,
  Settings,
  Copy,
  Trash2,
  MessageSquare,
  TrendingUp,
  Clock,
  Users,
  Search,
  Filter,
  Zap,
  Brain,
  Target,
  Star,
  Eye,
  Edit3,
  Send
} from 'lucide-react'
import { agentsAPI } from '../lib/api'

export function Agents() {
  const navigate = useNavigate()
  const [agents, setAgents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [typeFilter, setTypeFilter] = useState('')

  const fetchAgents = async () => {
    try {
      setLoading(true)
      const params = {
        ...(searchTerm && { search: searchTerm }),
        ...(typeFilter && { type: typeFilter })
      }
      const response = await agentsAPI.getAll(params)
      setAgents(response.data.agents)
    } catch (err) {
      setError('Failed to fetch agents')
      console.error('Error fetching agents:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAgents()
  }, [searchTerm, typeFilter])

  const getAgentTypeIcon = (type) => {
    const icons = {
      'conversational': Bot,
      'lead_qualifier': Target,
      'follow_up': MessageSquare
    }
    const Icon = icons[type] || Bot
    return <Icon className="h-5 w-5" />
  }

  const getAgentTypeColor = (type) => {
    const colors = {
      'conversational': 'bg-blue-100 text-blue-800',
      'lead_qualifier': 'bg-purple-100 text-purple-800',
      'follow_up': 'bg-orange-100 text-orange-800'
    }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  const getPersonalityIcon = (personality) => {
    const icons = {
      'professional': Users,
      'friendly': Star,
      'casual': MessageSquare,
      'enthusiastic': Zap
    }
    const Icon = icons[personality] || Users
    return <Icon className="h-4 w-4" />
  }


  const formatNumber = (num) => {
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'k'
    }
    return num.toString()
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AI Agents</h1>
          <p className="text-gray-500 mt-2">Create and manage your intelligent AI agents</p>
        </div>
        <Button onClick={() => navigate('/agents/new')} className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
          <Plus className="h-4 w-4 mr-2" />
          Create Agent
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="text"
                  placeholder="Search agents by name or description..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Types</option>
                <option value="conversational">Conversational</option>
                <option value="lead_qualifier">Lead Qualifier</option>
                <option value="follow_up">Follow-up</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Agents Grid */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-gray-500 mt-2">Loading agents...</p>
        </div>
      ) : error ? (
        <div className="text-center py-12 text-red-500">
          {error}
        </div>
      ) : agents.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <Bot className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No agents found</h3>
            <p className="text-gray-500 mb-4">Create your first AI agent to get started</p>
            <Button onClick={() => navigate('/agents/new')} className="bg-gradient-to-r from-blue-600 to-purple-600">
              <Plus className="h-4 w-4 mr-2" />
              Create Your First Agent
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.map((agent) => (
            <Card key={agent.id} className="hover:shadow-lg transition-shadow duration-200 border-l-4 border-l-blue-500">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      {getAgentTypeIcon(agent.type)}
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{agent.name}</h3>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getAgentTypeColor(agent.type)}`}>
                        {agent.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className={`h-2 w-2 rounded-full ${agent.is_active ? 'bg-green-400' : 'bg-gray-400'}`}></div>
                    <span className="text-xs text-gray-500">{agent.is_active ? 'Active' : 'Inactive'}</span>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                <p className="text-sm text-gray-600 line-clamp-2">{agent.description}</p>

                {/* Agent Stats */}
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="bg-gray-50 rounded-lg p-2">
                    <div className="font-semibold text-sm text-gray-900">{formatNumber(agent.total_interactions)}</div>
                    <div className="text-xs text-gray-500">Interactions</div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-2">
                    <div className="font-semibold text-sm text-green-600">{agent.success_rate}%</div>
                    <div className="text-xs text-gray-500">Success Rate</div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-2">
                    <div className="font-semibold text-sm text-blue-600">{agent.avg_response_time}s</div>
                    <div className="text-xs text-gray-500">Avg Response</div>
                  </div>
                </div>

                {/* Agent Configuration Preview */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">Model:</span>
                    <span className="font-medium">{agent.model}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">Personality:</span>
                    <div className="flex items-center gap-1">
                      {getPersonalityIcon(agent.personality_style)}
                      <span className="font-medium capitalize">{agent.personality_style}</span>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => navigate(`/agents/edit/${agent.id}`)}
                  >
                    <Edit3 className="h-4 w-4 mr-1" />
                    Configure Agent
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}


    </div>
  )
}