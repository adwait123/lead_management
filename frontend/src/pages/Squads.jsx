import { useState, useEffect } from 'react'
import { Network, Plus, ChevronRight, Users, Zap, ArrowRight, Play, Pencil, Trash2 } from 'lucide-react'
import { squadsAPI } from '../lib/api'
import { SquadTestingModal } from '../components/modals/SquadTestingModal'

const AGENT_COLORS = {
  router: { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-300', dot: 'bg-blue-500' },
  booking: { bg: 'bg-green-100', text: 'text-green-700', border: 'border-green-300', dot: 'bg-green-500' },
  job_inquiry: { bg: 'bg-purple-100', text: 'text-purple-700', border: 'border-purple-300', dot: 'bg-purple-500' },
  complaint: { bg: 'bg-red-100', text: 'text-red-700', border: 'border-red-300', dot: 'bg-red-500' },
}

const DEFAULT_COLOR = { bg: 'bg-gray-100', text: 'text-gray-700', border: 'border-gray-300', dot: 'bg-gray-500' }

function AgentFlowDiagram({ agents, entryAgentKey }) {
  const entryAgent = agents.find(a => a.key === entryAgentKey)
  const otherAgents = agents.filter(a => a.key !== entryAgentKey)

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {entryAgent && (
        <AgentBadge agent={entryAgent} isEntry />
      )}
      {otherAgents.length > 0 && (
        <>
          <ArrowRight className="h-4 w-4 text-gray-400 flex-shrink-0" />
          <div className="flex gap-2 flex-wrap">
            {otherAgents.map(agent => (
              <AgentBadge key={agent.key} agent={agent} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function AgentBadge({ agent, isEntry = false }) {
  const colors = AGENT_COLORS[agent.key] || DEFAULT_COLOR
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${colors.bg} ${colors.text} ${isEntry ? 'ring-2 ring-offset-1 ring-blue-400' : ''}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${colors.dot} mr-1.5`}></span>
      {agent.name}
      {agent.tools && agent.tools.length > 0 && (
        <span className="ml-1 text-[10px] opacity-70">({agent.tools.length})</span>
      )}
    </span>
  )
}

function SquadCard({ squad, onTest, onDelete }) {
  const agentsList = squad.agents || []

  return (
    <div className="bg-white rounded-xl border border-gray-200 hover:border-gray-300 hover:shadow-md transition-all">
      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mr-3">
              <Network className="h-5 w-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{squad.name}</h3>
              <p className="text-xs text-gray-500">{agentsList.length} agents</p>
            </div>
          </div>
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
            squad.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
          }`}>
            {squad.is_active ? 'Active' : 'Inactive'}
          </span>
        </div>

        {/* Description */}
        {squad.description && (
          <p className="text-sm text-gray-600 mb-4 line-clamp-2">{squad.description}</p>
        )}

        {/* Agent Flow */}
        <div className="mb-4">
          <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Agent Flow</p>
          <AgentFlowDiagram agents={agentsList} entryAgentKey={squad.entry_agent_key} />
        </div>

        {/* Agent Details Grid */}
        <div className="grid grid-cols-2 gap-2 mb-4">
          {agentsList.map(agent => {
            const colors = AGENT_COLORS[agent.key] || DEFAULT_COLOR
            return (
              <div key={agent.key} className={`p-2 rounded-lg border ${colors.border} ${colors.bg} bg-opacity-50`}>
                <p className={`text-xs font-medium ${colors.text}`}>{agent.name}</p>
                <p className="text-[10px] text-gray-500 mt-0.5">
                  {agent.tools?.length || 0} tools | max {agent.max_turns} turns
                </p>
              </div>
            )
          })}
        </div>

        {/* Shared Context */}
        {squad.shared_context_schema && Object.keys(squad.shared_context_schema).length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">Shared Context</p>
            <div className="flex flex-wrap gap-1">
              {Object.keys(squad.shared_context_schema).map(key => (
                <span key={key} className="px-1.5 py-0.5 bg-gray-100 rounded text-[10px] text-gray-600 font-mono">
                  {key}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2 pt-3 border-t border-gray-100">
          <button
            onClick={() => onTest(squad)}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            <Play className="h-3.5 w-3.5" />
            Test Squad
          </button>
          <button
            onClick={() => onDelete(squad.id)}
            className="px-3 py-2 text-gray-400 hover:text-red-500 rounded-lg border border-gray-200 hover:border-red-200 transition-colors"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}

export function Squads() {
  const [squads, setSquads] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [testingSquad, setTestingSquad] = useState(null)

  useEffect(() => {
    fetchSquads()
  }, [])

  const fetchSquads = async () => {
    try {
      setLoading(true)
      const response = await squadsAPI.getAll()
      setSquads(response.data.squads || [])
    } catch (err) {
      console.error('Error fetching squads:', err)
      setError('Failed to load squads')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this squad?')) return
    try {
      await squadsAPI.delete(id)
      setSquads(prev => prev.filter(s => s.id !== id))
    } catch (err) {
      console.error('Error deleting squad:', err)
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Agent Squads</h1>
          <p className="text-gray-600 mt-1">Multi-agent orchestration for inbound calls. Each squad routes between specialized agents based on caller intent.</p>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-600">{error}</p>
          <button onClick={fetchSquads} className="mt-3 text-sm text-red-600 underline">Retry</button>
        </div>
      ) : squads.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <Network className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No squads configured</h3>
          <p className="text-gray-500 mb-4">Run the seed script to create the demo Torkin Pest Control squad.</p>
          <code className="bg-gray-100 px-4 py-2 rounded-lg text-sm text-gray-700 font-mono">
            python create_demo_squad.py
          </code>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {squads.map(squad => (
            <SquadCard
              key={squad.id}
              squad={squad}
              onTest={setTestingSquad}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* Testing Modal */}
      {testingSquad && (
        <SquadTestingModal
          isOpen={!!testingSquad}
          onClose={() => setTestingSquad(null)}
          squad={testingSquad}
        />
      )}
    </div>
  )
}
