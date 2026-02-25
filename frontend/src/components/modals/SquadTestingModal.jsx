import { useState, useEffect, useRef } from 'react'
import { X, Send, ArrowRight, Zap, MessageCircle, Terminal, ChevronDown, Network } from 'lucide-react'
import api from '../../lib/api'

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
      "My name is James Rodriguez, my number is 555-123-4567",
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
      "I'm calling to complain about a service your technician did last week",
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
    id: 'job_inquiry_flow',
    name: 'Job Status Inquiry',
    icon: '🔍',
    description: 'Existing customer checks on their job status',
    messages: [
      "Hi, I want to check on the status of my existing pest control job",
      "My name is Sarah Johnson, the address is 456 Elm Street"
    ]
  },
  {
    id: 'intent_switch_midcall',
    name: 'Mid-Call Intent Switch',
    icon: '🔄',
    description: 'Caller switches from booking to complaint mid-call',
    messages: [
      "I need to schedule a follow-up treatment",
      "My name is Tom, phone is 555-999-8888",
      "Actually wait, the last technician was really rude and I want to file a complaint"
    ]
  }
]

// --- Helper functions ---

function extractName(text) {
  // Match patterns: "name is X", "I'm X", "this is X", "my name's X"
  const patterns = [
    /(?:my name is|name's|I'm|I am|this is|it's)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)/i,
    /(?:call me)\s+([A-Za-z]+)/i,
  ]
  for (const p of patterns) {
    const m = text.match(p)
    if (m) return m[1].trim()
  }
  return null
}

function extractPhone(text) {
  const m = text.match(/(\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})/)
  return m ? m[1] : null
}

function extractAddress(text) {
  const m = text.match(/(\d+\s+[A-Za-z]+(?:\s+[A-Za-z]+)*(?:\s+(?:Street|St|Avenue|Ave|Drive|Dr|Road|Rd|Lane|Ln|Boulevard|Blvd|Way|Court|Ct|Circle|Cir))(?:,?\s*[A-Za-z\s]+)?)/i)
  return m ? m[1] : null
}

function detectIntent(text) {
  const lower = text.toLowerCase()
  if (/billing|invoice|payment|charge|bill\b/i.test(lower)) return { intent: 'billing', confidence: 0.95 }
  if (/complain|complaint|rude|unacceptable|terrible|awful|angry|frustrated|didn'?t work|speak to.*(manager|supervisor)/i.test(lower)) return { intent: 'complaint', confidence: 0.92 }
  if (/status|existing|check on|follow.?up|my job|my service|last service|previous/i.test(lower)) return { intent: 'job_inquiry', confidence: 0.88 }
  if (/schedule|book|appointment|need.*service|pest|termite|ant|roach|rodent|rat|mouse|bug|insect|spider|bee|wasp/i.test(lower)) return { intent: 'new_service', confidence: 0.90 }
  return null
}

function detectToolCall(text) {
  const toolPatterns = [
    { pattern: /available.*slot|time slot|availability|checking.*schedule/i, tool: 'generate_appointment_slots' },
    { pattern: /booked|confirmed|confirmation.*number|appointment.*set/i, tool: 'book_appointment' },
    { pattern: /callback.*schedul|manager.*will.*call|we'?ll call you back/i, tool: 'raise_callback_request' },
    { pattern: /looking up|found your|job.*number|your records|JOB-/i, tool: 'confirm_lead_details' },
    { pattern: /transfer|connecting.*with|hold.*while|department/i, tool: 'transfer_to_team' },
  ]
  for (const { pattern, tool } of toolPatterns) {
    if (pattern.test(text)) return tool
  }
  return null
}

function timestamp() {
  return new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function formatPrompt(prompt, context) {
  let result = prompt
  try {
    result = result.replace(/\{customer_name\}/g, context.customer_name || 'Caller')
    result = result.replace(/\{phone\}/g, context.phone || '')
    result = result.replace(/\{address\}/g, context.address || '')
  } catch {}
  return result
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
  const [pendingIntent, setPendingIntent] = useState(null) // track detected intent, handoff after router collects info

  const messagesEndRef = useRef(null)
  const logEndRef = useRef(null)

  const agents = squad.agents || {}
  const agentsList = Array.isArray(agents) ? agents : Object.values(agents)
  const agentsMap = Array.isArray(agents)
    ? agents.reduce((m, a) => ({ ...m, [a.key]: a }), {})
    : agents

  useEffect(() => {
    if (isOpen) resetSession()
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
    setPendingIntent(null)
    setMessages([])
    setOrchestrationLog([{
      time: timestamp(),
      type: 'SESSION_START',
      message: `Entry agent: ${agentsMap[entryKey]?.name || entryKey}`,
      details: { shared_context: {} }
    }])

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

  const executeHandoff = (fromKey, targetKey, context, reason) => {
    addLog('HANDOFF_TRIGGERED', `${agentsMap[fromKey]?.name} → ${agentsMap[targetKey]?.name}`, {
      from: fromKey,
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
    setPendingIntent(null)

    const targetAgent = agentsMap[targetKey]
    addLog('AGENT_ACTIVATED', `Agent: ${targetAgent?.name}`, {
      tools: targetAgent?.tools || [],
      prompt_preview: targetAgent?.prompt?.substring(0, 100) + '...'
    })

    setMessages(prev => [...prev, {
      id: Date.now() + 1,
      text: `${agentsMap[fromKey]?.name || fromKey} → ${targetAgent?.name || targetKey}`,
      sender: 'handoff',
      timestamp: new Date()
    }])

    return newContext
  }

  // Build conversation_history with current agent's prompt as system message
  const buildApiPayload = (userMsg, agentKey, history, context) => {
    const agent = agentsMap[agentKey]
    const prompt = formatPrompt(agent?.prompt || '', context)

    const conversation_history = [
      { role: 'system', content: prompt }
    ]

    // Add context injection
    if (Object.keys(context).length > 0) {
      conversation_history.push({
        role: 'system',
        content: `Caller context: ${JSON.stringify(context)}`
      })
    }

    // Add prior chat turns (within this agent only)
    for (const msg of history) {
      conversation_history.push(msg)
    }

    return {
      message: userMsg,
      conversation_history,
      model: 'gpt-4o-mini',
      temperature: 0.7
    }
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isTyping) return

    const userMsg = inputMessage.trim()
    setInputMessage('')

    // Add user message to UI
    setMessages(prev => [...prev, {
      id: Date.now(),
      text: userMsg,
      sender: 'user',
      timestamp: new Date()
    }])

    const newTurn = turnCount + 1
    setTurnCount(newTurn)
    addLog('TURN_COUNT', `Turn ${newTurn}/${agentsMap[currentAgentKey]?.max_turns || 10} for ${agentsMap[currentAgentKey]?.name}`)

    // Extract info from user message (always, regardless of agent)
    const extractedName = extractName(userMsg)
    const extractedPhone = extractPhone(userMsg)
    const extractedAddress = extractAddress(userMsg)
    const updatedContext = { ...sharedContext }
    if (extractedName) updatedContext.customer_name = extractedName
    if (extractedPhone) updatedContext.phone = extractedPhone
    if (extractedAddress) updatedContext.address = extractedAddress
    if (Object.keys(updatedContext).length !== Object.keys(sharedContext).length ||
        JSON.stringify(updatedContext) !== JSON.stringify(sharedContext)) {
      setSharedContext(updatedContext)
    }

    // --- Router agent: detect intent + collect info before handoff ---
    if (currentAgentKey === 'router') {
      const intentResult = detectIntent(userMsg)

      // Check for deterministic billing route immediately
      if (intentResult?.intent === 'billing') {
        addLog('INTENT_CLASSIFIED', `intent: "billing"`, { confidence: 0.95 })
        addLog('DETERMINISTIC_ROUTE', 'Billing detected — bypassing LLM, hard transfer', {
          action: 'transfer_to_team', department: 'billing'
        })

        setMessages(prev => [...prev, {
          id: Date.now() + 2,
          text: "I'll connect you with our Billing & Accounts Team right away. Please hold — your reference number is REF-" +
            Math.floor(1000 + Math.random() * 9000) + ". Estimated wait: 3-7 minutes.",
          sender: 'agent',
          agentKey: 'router',
          timestamp: new Date(),
          toolUsed: 'transfer_to_team'
        }])
        addLog('TOOL_CALLED', 'transfer_to_team', { department: 'billing', result: 'Hard transfer initiated' })
        return
      }

      // Track intent
      if (intentResult && !pendingIntent) {
        setPendingIntent(intentResult)
        addLog('INTENT_CLASSIFIED', `intent: "${intentResult.intent}"`, { confidence: intentResult.confidence })
      }

      // Determine if we have enough info to hand off
      const currentIntent = intentResult || pendingIntent
      const hasName = !!updatedContext.customer_name
      const readyToHandoff = currentIntent && (hasName || newTurn >= 3)

      if (readyToHandoff) {
        const intentToAgent = {
          new_service: 'booking',
          job_inquiry: 'job_inquiry',
          complaint: 'complaint'
        }
        const targetKey = intentToAgent[currentIntent.intent]

        if (targetKey && agentsMap[targetKey]) {
          // Get LLM response as router first (transition message)
          setIsTyping(true)
          try {
            const newHistory = [...chatHistory, { role: 'user', content: userMsg }]
            const payload = buildApiPayload(userMsg, 'router', newHistory, updatedContext)
            const response = await api.post('/api/agents/1/chat', payload)
            const reply = response.data?.response || "Great, let me connect you with the right specialist."

            setMessages(prev => [...prev, {
              id: Date.now() + 3,
              text: reply,
              sender: 'agent',
              agentKey: 'router',
              timestamp: new Date()
            }])
          } catch {
            setMessages(prev => [...prev, {
              id: Date.now() + 3,
              text: "Great, let me connect you with the right specialist to help with that.",
              sender: 'agent',
              agentKey: 'router',
              timestamp: new Date()
            }])
          }
          setIsTyping(false)

          // Execute handoff
          updatedContext.intent = currentIntent.intent
          executeHandoff('router', targetKey, updatedContext, `Intent: ${currentIntent.intent}`)
          return
        }
      }
    }

    // --- Any non-router agent: check for intent mismatch / mid-call re-routing ---
    if (currentAgentKey !== 'router') {
      const intentResult = detectIntent(userMsg)
      if (intentResult) {
        const intentToAgent = {
          new_service: 'booking',
          job_inquiry: 'job_inquiry',
          complaint: 'complaint',
        }
        const correctAgent = intentToAgent[intentResult.intent]

        // Re-route if the detected intent maps to a DIFFERENT agent than current
        if (correctAgent && correctAgent !== currentAgentKey) {
          const currentAllowed = agentsMap[currentAgentKey]?.allowed_handoffs || []
          // Check if direct handoff is allowed, otherwise go back through router
          const targetKey = currentAllowed.includes(correctAgent) ? correctAgent : 'router'

          addLog('INTENT_CLASSIFIED', `intent: "${intentResult.intent}" (mid-call re-route)`, { confidence: intentResult.confidence })

          const transitionMessages = {
            complaint: "I understand you'd like to address a concern. Let me connect you with someone who can help with that right away.",
            job_inquiry: "It sounds like you'd like to check on an existing service. Let me get the right person to help you with that.",
            booking: "Let me connect you with our scheduling team to help with that.",
            router: "Let me get you to the right person for that."
          }

          setMessages(prev => [...prev, {
            id: Date.now() + 4,
            text: transitionMessages[targetKey] || transitionMessages.router,
            sender: 'agent',
            agentKey: currentAgentKey,
            timestamp: new Date()
          }])

          const handoffContext = { ...updatedContext, intent: intentResult.intent }
          if (intentResult.intent === 'complaint') handoffContext.complaint_summary = userMsg
          executeHandoff(currentAgentKey, targetKey, handoffContext, `Mid-call re-route: ${currentAgentKey} → ${targetKey} (intent: ${intentResult.intent})`)
          return
        }
      }
    }

    // --- Normal LLM call with current agent's prompt ---
    setIsTyping(true)
    try {
      const newHistory = [...chatHistory, { role: 'user', content: userMsg }]
      setChatHistory(newHistory)

      const payload = buildApiPayload(userMsg, currentAgentKey, newHistory, updatedContext)
      const response = await api.post('/api/agents/1/chat', payload)
      let agentReply = response.data?.response || "I'm sorry, could you repeat that?"

      // Detect tool usage from response
      const toolUsed = detectToolCall(agentReply)
      if (toolUsed) {
        addLog('TOOL_CALLED', toolUsed, { result: 'Detected in response' })
      }

      setMessages(prev => [...prev, {
        id: Date.now() + 5,
        text: agentReply,
        sender: 'agent',
        agentKey: currentAgentKey,
        timestamp: new Date(),
        toolUsed
      }])

      setChatHistory(prev => [...prev, { role: 'assistant', content: agentReply }])

    } catch (err) {
      console.error('Chat error:', err)
      const fallbackResponses = {
        router: "I'd be happy to help you with that. Could you tell me your name and what you're calling about?",
        booking: "I can help you book an appointment. What's the address for the service?",
        job_inquiry: "Let me look that up for you. Can you provide your job number or the address on file?",
        complaint: "I'm truly sorry about your experience. That's not the standard we hold ourselves to. Can you tell me more about what happened?"
      }
      setMessages(prev => [...prev, {
        id: Date.now() + 5,
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

                    {agent.tools?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-1.5">
                        {agent.tools.map(t => (
                          <span key={t} className="px-1.5 py-0.5 bg-white rounded text-[9px] text-gray-500 border">
                            {t.replace(/_/g, ' ')}
                          </span>
                        ))}
                      </div>
                    )}

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
