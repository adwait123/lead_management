import { useState, useEffect, useRef } from 'react'
import { X, Send, ArrowRight, Zap, MessageCircle, Terminal, ChevronDown, Network } from 'lucide-react'
import { agentsAPI } from '../../lib/api'

// --- Constants ---

const AGENT_COLORS = {
  router:      { bg: 'bg-blue-100',   text: 'text-blue-700',   border: 'border-blue-400',  dot: 'bg-blue-500',   ring: 'ring-blue-400'   },
  booking:     { bg: 'bg-green-100',  text: 'text-green-700',  border: 'border-green-400', dot: 'bg-green-500',  ring: 'ring-green-400'  },
  job_inquiry: { bg: 'bg-purple-100', text: 'text-purple-700', border: 'border-purple-400',dot: 'bg-purple-500', ring: 'ring-purple-400' },
  complaint:   { bg: 'bg-red-100',    text: 'text-red-700',    border: 'border-red-400',   dot: 'bg-red-500',    ring: 'ring-red-400'    },
}
const DEFAULT_COLOR = { bg: 'bg-gray-100', text: 'text-gray-700', border: 'border-gray-400', dot: 'bg-gray-500', ring: 'ring-gray-400' }

const LOG_COLORS = {
  SESSION_START:       'text-blue-600',
  INTENT_CLASSIFIED:   'text-cyan-600',
  HANDOFF_TRIGGERED:   'text-green-600',
  AGENT_ACTIVATED:     'text-green-700',
  TOOL_CALLED:         'text-indigo-600',
  TURN_COUNT:          'text-gray-500',
  DETERMINISTIC_ROUTE: 'text-yellow-600',
  ESCALATION:          'text-red-600',
  ERROR:               'text-red-500',
}

const SQUAD_SCENARIOS = [
  {
    id: 'new_service_booking',
    name: 'New Service Booking',
    icon: '📅',
    description: 'New customer books pest control service',
    messages: [
      "Hi, I need someone to come look at a termite problem",
      "My name is James Rodriguez",
      "123 Oak Street, Springfield",
      "Yes, Thursday morning works great",
      "Yes, please book that slot"
    ]
  },
  {
    id: 'complaint_escalation',
    name: 'Complaint Escalation',
    icon: '😤',
    description: 'Unsatisfied customer triggers 2-exchange escalation',
    messages: [
      "I'm calling about a service your technician did last week",
      "The treatment didn't work at all, I still have ants everywhere",
      "This is unacceptable, I want to speak to a manager"
    ]
  },
  {
    id: 'billing_hard_transfer',
    name: 'Billing Transfer',
    icon: '💳',
    description: 'Billing intent triggers deterministic hard transfer',
    messages: [
      "Hi, I have a question about my last invoice"
    ]
  },
  {
    id: 'intent_switch_midcall',
    name: 'Mid-Call Intent Switch',
    icon: '🔄',
    description: 'Caller switches from booking to complaint mid-call',
    messages: [
      "I need to schedule a follow-up treatment",
      "Actually wait, the last technician was really rude and I want to file a complaint"
    ]
  }
]

// --- Handoff detection ---

function detectHandoff(text, agents) {
  // Look for handoff signals in LLM response
  const handoffMatch = text.match(/\[HANDOFF:(\w+):(\{.*?\})\]/s)
  if (handoffMatch) {
    return { target: handoffMatch[1], context: tryParse(handoffMatch[2]) }
  }

  // Heuristic: check if the response mentions transferring or handing off
  const agentKeys = Object.keys(agents)
  for (const key of agentKeys) {
    const patterns = [
      `hand off to ${key}`,
      `transfer to ${key}`,
      `handing off to ${agents[key].name?.toLowerCase()}`,
      `connect you with ${agents[key].name?.toLowerCase()}`
    ]
    for (const p of patterns) {
      if (text.toLowerCase().includes(p)) {
        return { target: key, context: {} }
      }
    }
  }

  return null
}

function detectToolCall(text) {
  const toolPatterns = [
    { pattern: /generate_appointment_slots|checking availability|let me check.*slots/i, tool: 'generate_appointment_slots' },
    { pattern: /book_appointment|booking.*confirmed|appointment.*booked/i, tool: 'book_appointment' },
    { pattern: /raise_callback|callback.*scheduled|manager.*call.*back/i, tool: 'raise_callback_request' },
    { pattern: /confirm_lead|looking up.*job|checking.*records/i, tool: 'confirm_lead_details' },
    { pattern: /transfer_to_team|transferring.*to|connecting.*with/i, tool: 'transfer_to_team' },
  ]
  for (const { pattern, tool } of toolPatterns) {
    if (pattern.test(text)) return tool
  }
  return null
}

function detectIntent(text) {
  const lower = text.toLowerCase()
  if (/billing|invoice|payment|charge|bill/i.test(lower)) return { intent: 'billing', confidence: 0.95 }
  if (/complaint|complain|rude|unacceptable|manager|terrible|awful/i.test(lower)) return { intent: 'complaint', confidence: 0.92 }
  if (/schedule|book|appointment|need.*service|pest|termite|ant|roach|rodent/i.test(lower)) return { intent: 'new_service', confidence: 0.90 }
  if (/job|status|existing|follow.*up|check.*on|last.*service/i.test(lower)) return { intent: 'job_inquiry', confidence: 0.88 }
  return null
}

function tryParse(str) {
  try { return JSON.parse(str) } catch { return {} }
}

function timestamp() {
  return new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

// --- Component ---

export function SquadTestingModal({ isOpen, onClose, squad }) {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [currentAgentKey, setCurrentAgentKey] = useState(squad.entry_agent_key)
  const [sharedContext, setSharedContext] = useState({})
  const [turnCount, setTurnCount] = useState(0)
  const [orchestrationLog, setOrchestrationLog] = useState([])
  const [selectedScenario, setSelectedScenario] = useState(null)
  const [scenarioStep, setScenarioStep] = useState(0)
  const [chatHistory, setChatHistory] = useState([])

  const messagesEndRef = useRef(null)
  const logEndRef = useRef(null)

  const agents = squad.agents || {}
  const agentsList = Array.isArray(agents) ? agents : Object.values(agents)
  const agentsMap = Array.isArray(agents)
    ? agents.reduce((m, a) => ({ ...m, [a.key]: a }), {})
    : agents

  // Initialize
  useEffect(() => {
    if (isOpen) {
      resetSession()
    }
  }, [isOpen])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [orchestrationLog])

  const resetSession = () => {
    const entryKey = squad.entry_agent_key
    setCurrentAgentKey(entryKey)
    setSharedContext({})
    setTurnCount(0)
    setScenarioStep(0)
    setSelectedScenario(null)
    setChatHistory([])
    setMessages([])
    setOrchestrationLog([{
      time: timestamp(),
      type: 'SESSION_START',
      message: `Entry agent: ${agentsMap[entryKey]?.name || entryKey}`,
      details: { shared_context: {} }
    }])

    // Add greeting
    const greeting = "Hello, thank you for calling Torkin Pest Control. This is Mike, how can I help you today?"
    setMessages([{
      id: Date.now(),
      text: greeting,
      sender: 'agent',
      agentKey: entryKey,
      timestamp: new Date()
    }])
    setChatHistory([{ role: 'assistant', content: greeting }])
  }

  const addLog = (type, message, details = {}) => {
    setOrchestrationLog(prev => [...prev, { time: timestamp(), type, message, details }])
  }

  const executeHandoff = (targetKey, context, reason) => {
    addLog('HANDOFF_TRIGGERED', `${agentsMap[currentAgentKey]?.name} → ${agentsMap[targetKey]?.name}`, {
      from: currentAgentKey,
      to: targetKey,
      context_passed: context,
      reason,
      chat_ctx: 'WIPED (clean slate)'
    })

    const newContext = { ...sharedContext, ...context }
    setSharedContext(newContext)
    setCurrentAgentKey(targetKey)
    setTurnCount(0)
    setChatHistory([]) // Clean slate

    const targetAgent = agentsMap[targetKey]
    addLog('AGENT_ACTIVATED', `Agent: ${targetAgent?.name}`, {
      tools: targetAgent?.tools || [],
      prompt_preview: targetAgent?.prompt?.substring(0, 100) + '...'
    })

    // Add handoff divider to messages
    setMessages(prev => [...prev, {
      id: Date.now(),
      text: `${agentsMap[currentAgentKey]?.name || currentAgentKey} → ${targetAgent?.name || targetKey}`,
      sender: 'handoff',
      timestamp: new Date()
    }])
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isTyping) return

    const userMsg = inputMessage.trim()
    setInputMessage('')

    // Add user message
    setMessages(prev => [...prev, {
      id: Date.now(),
      text: userMsg,
      sender: 'user',
      timestamp: new Date()
    }])

    const newHistory = [...chatHistory, { role: 'user', content: userMsg }]
    setChatHistory(newHistory)
    setTurnCount(prev => prev + 1)

    addLog('TURN_COUNT', `Turn ${turnCount + 1}/${agentsMap[currentAgentKey]?.max_turns || 10} for ${agentsMap[currentAgentKey]?.name}`)

    // Check for deterministic billing route
    if (currentAgentKey === 'router') {
      const intentResult = detectIntent(userMsg)
      if (intentResult) {
        addLog('INTENT_CLASSIFIED', `intent: "${intentResult.intent}"`, { confidence: intentResult.confidence })

        if (intentResult.intent === 'billing') {
          addLog('DETERMINISTIC_ROUTE', 'Billing detected — bypassing LLM, hard transfer', {
            action: 'transfer_to_team',
            department: 'billing'
          })

          setMessages(prev => [...prev, {
            id: Date.now(),
            text: "I'll connect you with our Billing & Accounts Team right away. Please hold for a moment — your reference number is REF-" + Math.floor(1000 + Math.random() * 9000) + ". Estimated wait: 3-7 minutes.",
            sender: 'agent',
            agentKey: currentAgentKey,
            timestamp: new Date(),
            toolUsed: 'transfer_to_team'
          }])

          addLog('TOOL_CALLED', 'transfer_to_team', { department: 'billing', result: 'Transfer initiated' })
          return
        }
      }
    }

    // Call backend chat API
    setIsTyping(true)
    try {
      const currentAgent = agentsMap[currentAgentKey]
      const systemPrompt = currentAgent?.prompt || ''

      // Format the prompt with context
      let formattedPrompt = systemPrompt
      try {
        formattedPrompt = systemPrompt
          .replace('{customer_name}', sharedContext.customer_name || 'Caller')
      } catch {}

      // Add context injection if we have shared context
      let contextPrefix = ''
      if (Object.keys(sharedContext).length > 0) {
        contextPrefix = `Context from previous agent: ${JSON.stringify(sharedContext)}\n\n`
      }

      const response = await agentsAPI.test(1, userMsg)
      let agentReply = response.data?.response || response.data?.message || "I'm sorry, could you repeat that?"

      // Clean up any handoff signals from display text
      const cleanReply = agentReply.replace(/\[HANDOFF:\w+:\{.*?\}\]/gs, '').trim()

      // Detect tool usage
      const toolUsed = detectToolCall(agentReply)
      if (toolUsed) {
        addLog('TOOL_CALLED', toolUsed, {
          params: { context: 'auto-detected from response' },
          result: 'Mock data returned'
        })
      }

      // Check for handoff
      if (currentAgentKey === 'router') {
        const intentResult = detectIntent(userMsg)
        if (intentResult) {
          addLog('INTENT_CLASSIFIED', `intent: "${intentResult.intent}"`, { confidence: intentResult.confidence })

          const intentToAgent = {
            new_service: 'booking',
            job_inquiry: 'job_inquiry',
            complaint: 'complaint'
          }
          const targetKey = intentToAgent[intentResult.intent]
          if (targetKey && agentsMap[targetKey]) {
            // Extract name from conversation if mentioned
            const nameMatch = userMsg.match(/(?:my name is|I'm|this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)/i)
            const ctx = {
              intent: intentResult.intent,
              ...(nameMatch ? { customer_name: nameMatch[1] } : {}),
              ...(sharedContext)
            }

            // Show router's response first, then handoff
            setMessages(prev => [...prev, {
              id: Date.now(),
              text: cleanReply || "Great, let me connect you with the right specialist.",
              sender: 'agent',
              agentKey: currentAgentKey,
              timestamp: new Date()
            }])

            setTimeout(() => {
              executeHandoff(targetKey, ctx, `Intent classified: ${intentResult.intent}`)
            }, 500)

            setIsTyping(false)
            return
          }
        }
      }

      // Check for mid-call intent switch (booking/job_inquiry -> complaint)
      if (currentAgentKey !== 'router' && currentAgentKey !== 'complaint') {
        const intentResult = detectIntent(userMsg)
        if (intentResult?.intent === 'complaint') {
          setMessages(prev => [...prev, {
            id: Date.now(),
            text: "I understand you'd like to discuss a concern. Let me connect you with someone who can help with that right away.",
            sender: 'agent',
            agentKey: currentAgentKey,
            timestamp: new Date()
          }])

          setTimeout(() => {
            executeHandoff('complaint', { ...sharedContext, complaint_summary: userMsg }, 'Mid-call intent switch to complaint')
          }, 500)

          setIsTyping(false)
          return
        }
      }

      // Normal response
      setMessages(prev => [...prev, {
        id: Date.now(),
        text: cleanReply,
        sender: 'agent',
        agentKey: currentAgentKey,
        timestamp: new Date(),
        toolUsed
      }])

      setChatHistory(prev => [...prev, { role: 'assistant', content: agentReply }])

    } catch (err) {
      console.error('Chat error:', err)
      // Fallback response
      const fallbackResponses = {
        router: "I'd be happy to help you with that. Could you tell me a bit more about what you need?",
        booking: "I can help you book an appointment. What's the address for the service?",
        job_inquiry: "Let me look that up for you. Can you provide your job number or address?",
        complaint: "I'm truly sorry about your experience. Can you tell me more about what happened?"
      }
      setMessages(prev => [...prev, {
        id: Date.now(),
        text: fallbackResponses[currentAgentKey] || "How can I assist you?",
        sender: 'agent',
        agentKey: currentAgentKey,
        timestamp: new Date()
      }])
    } finally {
      setIsTyping(false)
    }
  }

  const handleScenarioSelect = (scenario) => {
    resetSession()
    setSelectedScenario(scenario)
    setScenarioStep(0)
  }

  const handleScenarioStep = () => {
    if (!selectedScenario || scenarioStep >= selectedScenario.messages.length) return
    const msg = selectedScenario.messages[scenarioStep]
    setInputMessage(msg)
    setScenarioStep(prev => prev + 1)
  }

  if (!isOpen) return null

  const currentAgent = agentsMap[currentAgentKey]
  const currentColors = AGENT_COLORS[currentAgentKey] || DEFAULT_COLOR

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-[1400px] w-full h-[85vh] overflow-hidden flex flex-col shadow-2xl">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mr-3">
              <Network className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">Squad Live Dashboard</h2>
              <p className="text-sm text-gray-500">{squad.name}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${currentColors.bg} ${currentColors.text}`}>
              Active: {currentAgent?.name || currentAgentKey}
            </span>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* 3-Panel Layout */}
        <div className="flex flex-1 overflow-hidden">

          {/* LEFT PANEL — Agent Map */}
          <div className="w-64 border-r bg-gray-50 flex flex-col overflow-y-auto">
            <div className="p-4 border-b">
              <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
                <Zap className="h-4 w-4" /> Agent Map
              </h3>
            </div>

            <div className="p-3 space-y-2">
              {agentsList.map(agent => {
                const colors = AGENT_COLORS[agent.key] || DEFAULT_COLOR
                const isActive = agent.key === currentAgentKey
                return (
                  <div
                    key={agent.key}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      isActive
                        ? `${colors.border} ${colors.bg} shadow-sm`
                        : 'border-gray-200 bg-white'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      {isActive && (
                        <span className={`w-2.5 h-2.5 rounded-full ${colors.dot} animate-pulse`}></span>
                      )}
                      <span className={`text-sm font-medium ${isActive ? colors.text : 'text-gray-700'}`}>
                        {agent.name}
                      </span>
                    </div>
                    <p className="text-[10px] text-gray-500 mb-1.5">{agent.key}</p>

                    {/* Tools */}
                    {agent.tools?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-1.5">
                        {agent.tools.map(t => (
                          <span key={t} className="px-1.5 py-0.5 bg-white rounded text-[9px] text-gray-500 border">
                            {t.replace(/_/g, ' ')}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Handoffs */}
                    {agent.allowed_handoffs?.length > 0 && (
                      <div className="flex items-center gap-1 text-[10px] text-gray-400">
                        <ArrowRight className="h-3 w-3" />
                        {agent.allowed_handoffs.join(', ')}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>

            {/* Shared Context */}
            <div className="p-3 border-t mt-auto">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Shared Context</h4>
              {Object.keys(sharedContext).length === 0 ? (
                <p className="text-[10px] text-gray-400 italic">Empty — waiting for router</p>
              ) : (
                <div className="space-y-1">
                  {Object.entries(sharedContext).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-[10px]">
                      <span className="text-gray-500 font-mono">{k}:</span>
                      <span className="text-gray-700 font-medium truncate ml-1 max-w-[100px]">{String(v)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Scenarios */}
            <div className="p-3 border-t">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Test Scenarios</h4>
              <div className="space-y-1.5">
                {SQUAD_SCENARIOS.map(s => (
                  <button
                    key={s.id}
                    onClick={() => handleScenarioSelect(s)}
                    className={`w-full text-left px-2 py-1.5 rounded text-xs transition-colors ${
                      selectedScenario?.id === s.id
                        ? 'bg-blue-100 text-blue-700'
                        : 'hover:bg-gray-100 text-gray-600'
                    }`}
                  >
                    <span className="mr-1">{s.icon}</span> {s.name}
                  </button>
                ))}
              </div>
              {selectedScenario && scenarioStep < selectedScenario.messages.length && (
                <button
                  onClick={handleScenarioStep}
                  className="w-full mt-2 px-2 py-1.5 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700"
                >
                  Next Message ({scenarioStep + 1}/{selectedScenario.messages.length})
                </button>
              )}
            </div>
          </div>

          {/* CENTER PANEL — Conversation */}
          <div className="flex-1 flex flex-col min-w-0">
            <div className="p-3 border-b bg-white">
              <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
                <MessageCircle className="h-4 w-4" /> Conversation
              </h3>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.map(msg => {
                if (msg.sender === 'handoff') {
                  return (
                    <div key={msg.id} className="flex items-center gap-2 py-2">
                      <div className="flex-1 h-px bg-gray-200"></div>
                      <span className="text-xs text-gray-400 font-medium flex items-center gap-1">
                        <ArrowRight className="h-3 w-3" /> {msg.text}
                      </span>
                      <div className="flex-1 h-px bg-gray-200"></div>
                    </div>
                  )
                }

                const isUser = msg.sender === 'user'
                const agentColors = AGENT_COLORS[msg.agentKey] || DEFAULT_COLOR

                return (
                  <div key={msg.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-md ${
                      isUser
                        ? 'bg-blue-600 text-white rounded-lg rounded-br-none'
                        : 'bg-gray-100 text-gray-800 rounded-lg rounded-bl-none'
                    } px-4 py-2.5`}>
                      {!isUser && msg.agentKey && (
                        <span className={`inline-block px-1.5 py-0.5 rounded text-[9px] font-medium mb-1 ${agentColors.bg} ${agentColors.text}`}>
                          {agentsMap[msg.agentKey]?.name || msg.agentKey}
                        </span>
                      )}
                      <p className="text-sm">{msg.text}</p>
                      {msg.toolUsed && (
                        <div className="mt-1.5 flex items-center gap-1 text-[10px] opacity-70">
                          <Zap className="h-3 w-3" />
                          {msg.toolUsed}
                        </div>
                      )}
                      <p className="text-[10px] mt-1 opacity-50">
                        {msg.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                )
              })}

              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-lg rounded-bl-none px-4 py-2.5">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={e => setInputMessage(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Type a message as the caller..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                  disabled={isTyping}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim() || isTyping}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Send className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>

          {/* RIGHT PANEL — Orchestration Log */}
          <div className="w-80 border-l bg-gray-900 flex flex-col overflow-hidden">
            <div className="p-3 border-b border-gray-700">
              <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-1.5">
                <Terminal className="h-4 w-4" /> Orchestration Log
              </h3>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-2 font-mono text-[11px]">
              {orchestrationLog.map((entry, i) => (
                <div key={i} className="border-b border-gray-800 pb-2">
                  <div className="flex items-start gap-2">
                    <span className="text-gray-500 flex-shrink-0">[{entry.time}]</span>
                    <span className={`font-semibold ${LOG_COLORS[entry.type] || 'text-gray-400'}`}>
                      {entry.type}
                    </span>
                  </div>
                  <p className="text-gray-400 ml-[70px] mt-0.5">{entry.message}</p>
                  {entry.details && Object.keys(entry.details).length > 0 && (
                    <div className="ml-[70px] mt-1 text-gray-500">
                      {Object.entries(entry.details).map(([k, v]) => (
                        <div key={k}>
                          <span className="text-gray-600">{k}:</span>{' '}
                          <span className="text-gray-400">
                            {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              <div ref={logEndRef} />
            </div>

            {/* Reset button */}
            <div className="p-3 border-t border-gray-700">
              <button
                onClick={resetSession}
                className="w-full px-3 py-1.5 bg-gray-700 text-gray-300 rounded text-xs font-medium hover:bg-gray-600 transition-colors"
              >
                Reset Session
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
