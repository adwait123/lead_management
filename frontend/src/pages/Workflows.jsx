import React, { useState, useCallback, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Plus, Save, Play, Settings } from 'lucide-react'
import {
  ReactFlow,
  useNodesState,
  useEdgesState,
  addEdge,
  Background,
  Controls,
  MiniMap,
  Panel,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

// Custom node components
import TriggerNode from '../components/workflow/TriggerNode'
import AgentNode from '../components/workflow/AgentNode'

const nodeTypes = {
  trigger: TriggerNode,
  agent: AgentNode,
}

const initialNodes = [
  {
    id: 'trigger-1',
    type: 'trigger',
    position: { x: 100, y: 100 },
    data: {
      label: 'New Lead',
      triggerType: 'new_lead',
      description: 'When a new lead is created'
    }
  }
]

const initialEdges = []

export function Workflows() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const [agents, setAgents] = useState([])
  const [selectedWorkflow, setSelectedWorkflow] = useState(null)
  const [showSidebar, setShowSidebar] = useState(false)

  // Fetch available agents on component mount
  useEffect(() => {
    fetchAgents()
  }, [])

  const fetchAgents = async () => {
    try {
      const response = await fetch('https://lead-management-j828.onrender.com/api/agents/')
      if (response.ok) {
        const data = await response.json()
        setAgents(data.agents || [])
        console.log('Fetched agents for workflow:', data.agents)
      } else {
        console.error('Failed to fetch agents - response not ok:', response.status)
      }
    } catch (error) {
      console.error('Failed to fetch agents:', error)
    }
  }

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  const addTriggerNode = (triggerType) => {
    const triggerConfig = {
      new_lead: { label: 'New Lead', description: 'When a new lead is created', icon: '👤' },
      form_submission: { label: 'Form Submission', description: 'When a form is submitted', icon: '📝' },
      email_opened: { label: 'Email Opened', description: 'When an email is opened', icon: '📧' },
      website_visit: { label: 'Website Visit', description: 'When someone visits your website', icon: '🌐' },
      meeting_scheduled: { label: 'Meeting Scheduled', description: 'When a meeting is booked', icon: '📅' },
      support_ticket: { label: 'Support Ticket', description: 'When a support ticket is created', icon: '🎫' }
    }

    const config = triggerConfig[triggerType] || triggerConfig.new_lead
    const newNode = {
      id: `trigger-${Date.now()}`,
      type: 'trigger',
      position: { x: Math.random() * 400 + 50, y: Math.random() * 300 + 50 },
      data: {
        label: config.label,
        triggerType: triggerType,
        description: config.description,
        icon: config.icon
      }
    }

    setNodes((nds) => nds.concat(newNode))
  }

  const addAgentNode = (agent) => {
    const newNode = {
      id: `agent-${agent.id}-${Date.now()}`,
      type: 'agent',
      position: { x: Math.random() * 400 + 300, y: Math.random() * 300 + 50 },
      data: {
        label: agent.name,
        agentId: agent.id,
        description: agent.description,
        useCase: agent.use_case,
        type: agent.type
      }
    }

    setNodes((nds) => nds.concat(newNode))
  }

  const saveWorkflow = async () => {
    const workflowData = {
      name: `Workflow ${Date.now()}`,
      nodes: nodes,
      edges: edges,
      created_at: new Date().toISOString()
    }

    try {
      console.log('Saving workflow:', workflowData)
      // TODO: Implement API call to save workflow
      alert('Workflow saved successfully!')
    } catch (error) {
      console.error('Failed to save workflow:', error)
      alert('Failed to save workflow')
    }
  }

  const testWorkflow = async () => {
    // Find trigger nodes and their connected agents
    const triggerNodes = nodes.filter(node => node.type === 'trigger')
    const agentNodes = nodes.filter(node => node.type === 'agent')

    console.log('Testing workflow with triggers:', triggerNodes)
    console.log('Connected to agents:', agentNodes)

    // TODO: Implement workflow testing logic
    alert('Workflow test completed - check console for details')
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b bg-white">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Workflow Builder</h1>
          <p className="text-gray-500 mt-1">Design agent trigger workflows</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            onClick={() => setShowSidebar(!showSidebar)}
          >
            <Settings className="h-4 w-4 mr-2" />
            Components
          </Button>
          <Button
            variant="outline"
            onClick={testWorkflow}
          >
            <Play className="h-4 w-4 mr-2" />
            Test
          </Button>
          <Button onClick={saveWorkflow}>
            <Save className="h-4 w-4 mr-2" />
            Save Workflow
          </Button>
        </div>
      </div>

      <div className="flex-1 flex">
        {/* Sidebar */}
        {showSidebar && (
          <div className="w-80 bg-gray-50 border-r p-4 overflow-y-auto">
            <div className="space-y-6">
              {/* Trigger Components */}
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Event Triggers</h3>
                <div className="space-y-2">
                  {[
                    { type: 'new_lead', label: 'New Lead', icon: '👤' },
                    { type: 'form_submission', label: 'Form Submission', icon: '📝' },
                    { type: 'email_opened', label: 'Email Opened', icon: '📧' },
                    { type: 'website_visit', label: 'Website Visit', icon: '🌐' },
                    { type: 'meeting_scheduled', label: 'Meeting Scheduled', icon: '📅' },
                    { type: 'support_ticket', label: 'Support Ticket', icon: '🎫' }
                  ].map((trigger) => (
                    <button
                      key={trigger.type}
                      onClick={() => addTriggerNode(trigger.type)}
                      className="w-full text-left p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors"
                    >
                      <div className="flex items-center">
                        <span className="text-lg mr-3">{trigger.icon}</span>
                        <span className="font-medium text-gray-900">{trigger.label}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Agent Components */}
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Available Agents</h3>
                <div className="space-y-2">
                  {agents.length === 0 ? (
                    <p className="text-sm text-gray-500">No agents available</p>
                  ) : (
                    agents.map((agent) => (
                      <button
                        key={agent.id}
                        onClick={() => addAgentNode(agent)}
                        className="w-full text-left p-3 rounded-lg border border-gray-200 hover:border-green-300 hover:bg-green-50 transition-colors"
                      >
                        <div className="flex items-center">
                          <span className="text-lg mr-3">🤖</span>
                          <div>
                            <div className="font-medium text-gray-900">{agent.name}</div>
                            <div className="text-xs text-gray-500">{agent.use_case}</div>
                          </div>
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* React Flow Canvas */}
        <div className="flex-1 bg-gray-100">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            fitView
            className="bg-teal-50"
          >
            <Background color="#aaa" gap={16} />
            <Controls />
            <MiniMap />
            <Panel position="top-left">
              <div className="bg-white p-3 rounded-lg shadow-sm border">
                <h4 className="font-medium text-gray-900 mb-2">Instructions</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Drag triggers and agents from the sidebar</li>
                  <li>• Connect triggers to agents to create workflows</li>
                  <li>• Use Test button to validate your workflow</li>
                </ul>
              </div>
            </Panel>
          </ReactFlow>
        </div>
      </div>
    </div>
  )
}