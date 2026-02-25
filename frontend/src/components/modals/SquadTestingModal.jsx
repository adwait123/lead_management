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
  CONTEXT_UPDATE:      'text-teal-500',
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

// --- LLM signal instructions ---
// All context extraction and routing is done by the LLM via structured signals.
// The frontend only parses these signals — no regex intent detection or data extraction.

const CONTEXT_SIGNAL_INSTRUCTIONS = `

CONTEXT TRACKING: You are responsible for extracting caller data. Whenever the caller provides their name, phone number, or address, you MUST include this signal on its own line at the end of your response (BEFORE any HANDOFF signal):

[CONTEXT:name=<name>,phone=<phone>,address=<address>]

RULES for CONTEXT:
- Only include fields that were actually provided.
- If the user says "Adi", include [CONTEXT:name=Adi]. 
- If the user says "2 park street", include [CONTEXT:address=2 park street].
- CRITICAL: Do not extract names from sentences describing feelings (e.g., "I am not getting support" does NOT mean the name is "Not Getting").
- This signal is stripped from the display. The caller never sees it.`

const ROUTER_HANDOFF_INSTRUCTIONS = `

When you have identified the caller's intent AND have their name, respond naturally to the caller AND include this exact signal at the very end of your response on its own line:

[HANDOFF:booking] — for new service requests
[HANDOFF:job_inquiry] — for existing jobs or history
[HANDOFF:complaint] — for complaints
[HANDOFF:billing] — for billing/invoices
[HANDOFF:escalation] — if they demand a human/manager immediately

Do NOT hand off until you have the name. If you're unsure of intent, ask a clarifying question.
IMPORTANT: Do NOT say "one moment" or "let me transfer you". Just respond naturally and append the signal. The routing happens instantly in the background.`

const AGENT_HANDOFF_INSTRUCTIONS = `

If the caller changes their mind, respond naturally AND include this signal at the very end:

[HANDOFF:booking] | [HANDOFF:job_inquiry] | [HANDOFF:complaint] | [HANDOFF:billing] | [HANDOFF:escalation]

IMPORTANT: Do NOT say "one moment" or "let me look that up" unless you are actually providing results. If you are using a tool, the system will provide the data to you in the next turn.`

const SIMULATED_TOOL_RESULTS = {
  generate_appointment_slots: "SYSTEM: I found two openings: tomorrow at 9:00 AM or Friday at 1:00 PM with our senior tech, Dave.",
  confirm_lead_details: "SYSTEM: I've located the account. There is an active pest control job (#T-992) at this address. The last technician was Marcus on Jan 15th.",
  book_appointment: "SYSTEM: Success! The appointment is scheduled for tomorrow at 9:00 AM. Confirmation number is TORK-123.",
  raise_callback_request: "SYSTEM: I have scheduled a priority callback from our area manager, Sarah. She will call this number within 2 hours.",
  transfer_to_team: "SYSTEM: Connecting to the specialized department now."
}

// --- Helper functions ---

function detectToolCall(text) {
  const toolPatterns = [
    { pattern: /available.*slot|time slot|availability|checking.*schedule/i, tool: 'generate_appointment_slots' },
    { pattern: /booked|confirmed|confirmation.*number|appointment.*set/i, tool: 'book_appointment' },
    { pattern: /callback.*schedul|manager.*will.*call|we'?ll call you back/i, tool: 'raise_callback_request' },
    { pattern: /looking up|found your|job.*number|your records|JOB-|locat.*account/i, tool: 'confirm_lead_details' },
  ]
  for (const { pattern, tool } of toolPatterns) {
    if (pattern.test(text)) return tool
  }
  return null
}

function parseContextSignal(text) {
  const match = text.match(/\[CONTEXT:([^\]]+)\]/)
  if (!match) return { context: null, cleanText: text }
  const context = {}
  match[1].split(',').forEach(pair => {
    const eqIdx = pair.indexOf('=')
    if (eqIdx > 0) {
      const key = pair.substring(0, eqIdx).trim()
      const val = pair.substring(eqIdx + 1).trim()
      if (val) context[key] = val
    }
  })
  const cleanText = text.replace(/\n?\[CONTEXT:[^\]]+\]/g, '').trim()
  return { context: Object.keys(context).length > 0 ? context : null, cleanText }
}

function parseHandoffSignal(text) {
  const match = text.match(/\[HANDOFF:(booking|job_inquiry|complaint|billing|router|escalation)\]/)
  if (!match) return null
  const cleanText = text.replace(/\n?\[HANDOFF:(?:booking|job_inquiry|complaint|billing|router|escalation)\].*$/s, '').trim()
  return { target: match[1], cleanText }
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
    setChatHistory([])

    const targetAgent = agentsMap[targetKey]
    addLog('AGENT_ACTIVATED', `Agent: ${targetAgent?.name}`, {
      tools: targetAgent?.tools || [],
      prompt_preview: targetAgent?.prompt?.substring(0, 100) + '...'
    })

    return newContext
  }

  const buildApiPayload = (userMsg, agentKey, history, context) => {
    const agent = agentsMap[agentKey]
    let prompt = formatPrompt(agent?.prompt || '', context)

    // Append LLM signal instructions
    prompt += CONTEXT_SIGNAL_INSTRUCTIONS
    if (agentKey === 'router') {
      prompt += ROUTER_HANDOFF_INSTRUCTIONS
    } else {
      prompt += AGENT_HANDOFF_INSTRUCTIONS
    }

    const conversation_history = [
      { role: 'system', content: prompt }
    ]

    // Natural language context injection
    if (Object.keys(context).length > 0) {
      conversation_history.push({
        role: 'system',
        content: `IMPORTANT: The following has ALREADY been collected. Do NOT ask again:
- Caller name: ${context.customer_name || 'not yet collected'}
- Phone: ${context.phone || 'not yet collected'}
- Address: ${context.address || 'not yet collected'}
- Intent: ${context.intent || 'not yet determined'}
Use this information naturally. Never re-ask for anything listed above.`
      })
    }

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

    // Call LLM with current agent's prompt
    setIsTyping(true)
    try {
      const newHistory = [...chatHistory, { role: 'user', content: userMsg }]
      setChatHistory(newHistory)

      const payload = buildApiPayload(userMsg, currentAgentKey, newHistory, sharedContext)
      const response = await api.post('/api/agents/1/chat', payload)
      let agentReply = response.data?.response || "I'm sorry, could you repeat that?"

      // 1. Parse and apply context signal (name/phone/address extracted by LLM)
      const { context: llmContext, cleanText: afterContext } = parseContextSignal(agentReply)
      let updatedContext = { ...sharedContext }
      if (llmContext) {
        if (llmContext.name) updatedContext.customer_name = llmContext.name
        if (llmContext.phone) updatedContext.phone = llmContext.phone
        if (llmContext.address) updatedContext.address = llmContext.address
        setSharedContext(updatedContext)
        addLog('CONTEXT_UPDATE', 'LLM extracted caller info', llmContext)
      }

      // 2. Parse handoff signal
      const handoff = parseHandoffSignal(afterContext)

      if (handoff) {
        // Escalation — caller wants a human
        if (handoff.target === 'escalation') {
          addLog('ESCALATION', 'Caller requested human agent', { from: currentAgentKey })

          const displayText = handoff.cleanText || "I understand. Let me get a manager on the line for you right away."
          setMessages(prev => [...prev, {
            id: Date.now() + 2,
            text: displayText,
            sender: 'agent',
            agentKey: currentAgentKey,
            timestamp: new Date(),
            toolUsed: 'raise_callback_request'
          }])
          addLog('TOOL_CALLED', 'raise_callback_request', { result: 'Escalation to human initiated' })
          return
        }

        // Deterministic billing hard transfer
        if (handoff.target === 'billing') {
          addLog('INTENT_CLASSIFIED', 'intent: "billing"', { source: 'LLM handoff signal' })
          addLog('DETERMINISTIC_ROUTE', 'Billing detected — hard transfer', {
            action: 'transfer_to_team', department: 'billing'
          })

          const billingMsg = handoff.cleanText ||
            "I'll connect you with our Billing & Accounts Team right away. Please hold — your reference number is REF-" +
            Math.floor(1000 + Math.random() * 9000) + ". Estimated wait: 3-7 minutes."

          setMessages(prev => [...prev, {
            id: Date.now() + 2,
            text: billingMsg,
            sender: 'agent',
            agentKey: currentAgentKey,
            timestamp: new Date(),
            toolUsed: 'transfer_to_team'
          }])
          addLog('TOOL_CALLED', 'transfer_to_team', { department: 'billing', result: 'Hard transfer initiated' })
          return
        }

        // LLM-driven handoff to another agent
        const displayText = handoff.cleanText
        addLog('INTENT_CLASSIFIED', `intent: "${handoff.target}" (LLM handoff signal)`, { from: currentAgentKey })

        if (displayText) {
          setMessages(prev => [...prev, {
            id: Date.now() + 3,
            text: displayText,
            sender: 'agent',
            agentKey: currentAgentKey,
            timestamp: new Date()
          }])
        }

        const handoffContext = { ...updatedContext, intent: handoff.target }
        executeHandoff(currentAgentKey, handoff.target, handoffContext, `LLM handoff signal: ${currentAgentKey} → ${handoff.target}`)
        return
      }

      // 3. No handoff — normal response (use text with context signal stripped)
      const displayReply = afterContext
      const toolUsed = detectToolCall(displayReply)
      
      setMessages(prev => [...prev, {
        id: Date.now() + 5,
        text: displayReply,
        sender: 'agent',
        agentKey: currentAgentKey,
        timestamp: new Date(),
        toolUsed
      }])

      const updatedHistory = [...newHistory, { role: 'assistant', content: displayReply }]
      setChatHistory(updatedHistory)

      // 4. If a tool was used, simulate a result and trigger a follow-up response automatically
      if (toolUsed && SIMULATED_TOOL_RESULTS[toolUsed]) {
        const toolResult = SIMULATED_TOOL_RESULTS[toolUsed]
        addLog('TOOL_CALLED', toolUsed, { result: 'Detected and simulated' })
        
        // Wait a beat, then send the system result to the LLM
        setTimeout(async () => {
          setIsTyping(true)
          try {
            const systemHistory = [...updatedHistory, { role: 'system', content: toolResult }]
            setChatHistory(systemHistory)
            
            const followUpPayload = buildApiPayload("Please provide the results to the user.", currentAgentKey, systemHistory, updatedContext)
            // Note: We use a special instruction as the "user" message for the follow-up
            const followUpResponse = await api.post('/api/agents/1/chat', {
              ...followUpPayload,
              message: "Continue based on the system result provided."
            })
            
            const followUpReply = followUpResponse.data?.response || ""
            const { context: fContext, cleanText: fCleanText } = parseContextSignal(followUpReply)
            
            if (fContext) {
              setSharedContext(prev => ({ ...prev, ...fContext }))
            }
            
            setMessages(prev => [...prev, {
              id: Date.now() + 10,
              text: fCleanText,
              sender: 'agent',
              agentKey: currentAgentKey,
              timestamp: new Date()
            }])
            setChatHistory(prev => [...prev, { role: 'assistant', content: fCleanText }])
          } catch (err) {
            console.error('Follow-up error:', err)
          } finally {
            setIsTyping(false)
          }
        }, 800)
      }

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
                const isUser = msg.sender === 'user'

                return (
                  <div key={msg.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-md ${
                      isUser
                        ? 'bg-blue-600 text-white rounded-lg rounded-br-none'
                        : 'bg-gray-100 text-gray-800 rounded-lg rounded-bl-none'
                    } px-4 py-2.5`}>
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
