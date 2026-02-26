import { useState, useEffect, useRef } from 'react'
import { X, Send, ArrowRight, Zap, MessageCircle, Terminal, Network, Database, Clock } from 'lucide-react'
import api from '../../lib/api'

// =============================================================================
// CONSTANTS
// =============================================================================

const AGENT_COLORS = {
  router:      { bg: 'bg-blue-100',   text: 'text-blue-700',   border: 'border-blue-400',  dot: 'bg-blue-500'   },
  booking:     { bg: 'bg-green-100',  text: 'text-green-700',  border: 'border-green-400', dot: 'bg-green-500'  },
  job_inquiry: { bg: 'bg-purple-100', text: 'text-purple-700', border: 'border-purple-400',dot: 'bg-purple-500' },
  complaint:   { bg: 'bg-red-100',    text: 'text-red-700',    border: 'border-red-400',   dot: 'bg-red-500'    },
}
const DEFAULT_COLOR = { bg: 'bg-gray-100', text: 'text-gray-700', border: 'border-gray-400', dot: 'bg-gray-500' }

const LOG_COLORS = {
  SESSION_START:       'text-blue-600',
  INTENT_CLASSIFIED:   'text-cyan-600',
  HANDOFF_TRIGGERED:   'text-green-600',
  AGENT_ACTIVATED:     'text-green-700',
  TOOL_CALLED:         'text-indigo-600',
  TURN_COUNT:          'text-gray-500',
  DETERMINISTIC_ROUTE: 'text-yellow-600',
  DERIVED_DATA:        'text-teal-500',
  CONDITIONAL_PROMPT:  'text-orange-500',
  ESCALATION:          'text-red-600',
  ERROR:               'text-red-500',
}

const SQUAD_SCENARIOS = [
  {
    id: 'new_service_north',
    name: 'New Booking (North)',
    icon: '📅',
    description: 'Customer in North region books service — see region pricing',
    messages: [
      "Hi, I need pest control for a termite problem",
      "James Rodriguez, 555-123-4567",
      "123 Oak Street, Springfield",
      "Thursday morning works great",
      "Yes, please book that slot"
    ]
  },
  {
    id: 'new_service_south',
    name: 'New Booking (South)',
    icon: '🌴',
    description: 'Customer in South region — different pricing injected',
    messages: [
      "I need someone to handle a roach problem",
      "Maria Santos, 555-987-6543",
      "45 Palm Avenue, Ogdenville",
      "Any day this week works"
    ]
  },
  {
    id: 'job_inquiry_flow',
    name: 'Job Status Inquiry',
    icon: '🔍',
    description: 'Existing customer checks on their job status',
    messages: [
      "Hi, I want to check on the status of my existing pest control job",
      "Sarah Johnson, 456 Elm Street, Springfield"
    ]
  },
  {
    id: 'complaint_escalation',
    name: 'Complaint → Escalation',
    icon: '😤',
    description: 'Complaint that escalates to human',
    messages: [
      "I'm calling to complain about a service your technician did last week",
      "My name is Tom, the treatment didn't work at all",
      "This is unacceptable, I want to speak to a manager"
    ]
  },
  {
    id: 'billing_hard_transfer',
    name: 'Billing Transfer',
    icon: '💳',
    description: 'Billing intent → deterministic hard transfer',
    messages: [
      "Hi, I have a question about my last invoice"
    ]
  },
  {
    id: 'intent_switch',
    name: 'Mid-Call Switch',
    icon: '🔄',
    description: 'Booking → realizes they already have a job',
    messages: [
      "I need to schedule a follow-up treatment",
      "Tom, 555-999-8888",
      "Actually wait, I think I already have a booking from last week"
    ]
  }
]

// =============================================================================
// CORE DATA FRAMEWORK (Chrysalis Building Block 1)
// Structured conversation state with deterministic derivation.
// The LLM never computes these — code does.
// =============================================================================

// City/area → service region
const REGION_MAP = {
  'springfield': 'north', 'shelbyville': 'north', 'capital city': 'north',
  'ogdenville': 'south', 'north haverbrook': 'south', 'brockway': 'south',
  'cypress creek': 'east', 'westfield': 'west',
}
// Street name fallbacks
const REGION_KEYWORDS = {
  north: ['oak', 'maple', 'elm', 'pine', 'birch', 'main', 'cedar'],
  south: ['palm', 'magnolia', 'peach', 'bayou', 'hibiscus'],
  east:  ['harbor', 'shore', 'coast', 'bay', 'lighthouse'],
  west:  ['mesa', 'canyon', 'desert', 'ridge', 'cactus'],
}

// Region → pricing + technician assignment (deterministic)
const REGION_CONFIG = {
  north: { base: 149, emergency: 249, techs: 'Dave or Marcus',  dispatch_center: 'Springfield HQ' },
  south: { base: 129, emergency: 219, techs: 'Patricia or Ramon', dispatch_center: 'Ogdenville South' },
  east:  { base: 159, emergency: 269, techs: 'Jim or Anika',     dispatch_center: 'Harbor Office' },
  west:  { base: 139, emergency: 229, techs: 'Carlos or Mei',    dispatch_center: 'Mesa West' },
}

function deriveRegion(address) {
  if (!address) return null
  const lower = address.toLowerCase()
  for (const [city, region] of Object.entries(REGION_MAP)) {
    if (lower.includes(city)) return region
  }
  for (const [region, keywords] of Object.entries(REGION_KEYWORDS)) {
    if (keywords.some(kw => lower.includes(kw))) return region
  }
  return 'north' // default
}

function deriveBusinessHours() {
  const now = new Date()
  const hour = now.getHours()
  const day = now.getDay()
  const isWeekday = day >= 1 && day <= 5
  return {
    is_business_hours: isWeekday && hour >= 8 && hour < 18,
    is_after_hours: !(isWeekday && hour >= 8 && hour < 18),
    current_time: now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
  }
}

function validatePhone(phone) {
  if (!phone) return null
  const digits = phone.replace(/\D/g, '')
  if (digits.length >= 7 && digits.length <= 11) {
    const formatted = digits.length === 10
      ? digits.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3')
      : digits
    return { valid: true, formatted }
  }
  return { valid: false, formatted: phone }
}

// Run all deterministic derivations. Returns { newData, derivationLogs[] }
function runDerivations(data) {
  const newData = { ...data }
  const logs = []

  // Derive region from address
  if (newData.address && !newData.service_region) {
    const region = deriveRegion(newData.address)
    if (region) {
      newData.service_region = region
      const config = REGION_CONFIG[region]
      newData.pricing_base = config.base
      newData.pricing_emergency = config.emergency
      newData.assigned_techs = config.techs
      newData.dispatch_center = config.dispatch_center
      logs.push({
        type: 'DERIVED_DATA',
        message: `address → region: "${region}"`,
        details: {
          source: 'Core Data: deterministic mapping',
          input: newData.address,
          derived: `region=${region}, base=$${config.base}, emergency=$${config.emergency}, techs=${config.techs}`
        }
      })
    }
  }

  // Validate phone
  if (newData.phone && newData.phone_valid === undefined) {
    const result = validatePhone(newData.phone)
    if (result) {
      newData.phone_valid = result.valid
      newData.phone_formatted = result.formatted
      if (!result.valid) {
        logs.push({
          type: 'DERIVED_DATA',
          message: `phone validation: INVALID`,
          details: { source: 'Core Data: validation', input: newData.phone }
        })
      }
    }
  }

  // Business hours
  const hours = deriveBusinessHours()
  newData.is_business_hours = hours.is_business_hours
  newData.is_after_hours = hours.is_after_hours

  return { newData, logs }
}

// =============================================================================
// CONDITIONAL PROMPTING (Chrysalis Building Block 3)
// Prompt sections activated/deactivated by core data state.
// The LLM receives only the relevant sections — not all possible branches.
// =============================================================================

function buildConditionalSections(agentKey, data) {
  const sections = []
  const triggers = []

  // After-hours mode (any agent)
  if (data.is_after_hours) {
    sections.push(`[AFTER-HOURS MODE] It is currently outside business hours (Mon–Fri 8 AM–6 PM). You CAN still book appointments for future dates (tomorrow onwards) — use generate_appointment_slots as normal and confirm the slot. You may NOT offer same-day or immediate service. If the caller needs urgent same-day help, use raise_callback_request so a team member calls them back during business hours.`)
    triggers.push('is_after_hours = true')
  }

  // Region-specific pricing (booking agent)
  if (agentKey === 'booking' && data.service_region) {
    const c = REGION_CONFIG[data.service_region] || REGION_CONFIG.north
    sections.push(`[REGION: ${data.service_region.toUpperCase()}] Service area: ${c.dispatch_center}. Standard treatment: $${c.base}. Emergency/same-day: $${c.emergency}. Assigned technicians: ${c.techs}. Quote these exact prices when asked about cost. Do not estimate or guess different prices.`)
    triggers.push(`service_region = "${data.service_region}"`)
  }

  // Region info for job inquiry
  if (agentKey === 'job_inquiry' && data.service_region) {
    const c = REGION_CONFIG[data.service_region] || REGION_CONFIG.north
    sections.push(`[REGION: ${data.service_region.toUpperCase()}] Technicians in this area: ${c.techs}. Dispatch center: ${c.dispatch_center}. Reference these details when discussing the caller's service history.`)
    triggers.push(`service_region = "${data.service_region}"`)
  }

  // Complaint with known region — assign area manager
  if (agentKey === 'complaint' && data.service_region) {
    const managers = { north: 'Sarah Chen', south: 'Diego Morales', east: 'Priya Patel', west: 'Ryan O\'Brien' }
    const mgr = managers[data.service_region] || 'our area manager'
    sections.push(`[ESCALATION PATH] Area manager for ${data.service_region} region: ${mgr}. If escalation is needed, reference this manager by name.`)
    triggers.push(`service_region = "${data.service_region}" (complaint)`)
  }

  // Invalid phone warning
  if (data.phone_valid === false) {
    sections.push(`[DATA QUALITY] The phone number provided (${data.phone}) appears invalid. Politely ask the caller to confirm their phone number.`)
    triggers.push('phone_valid = false')
  }

  return { sections, triggers }
}

// =============================================================================
// LLM HANDOFF SIGNALS
// The only LLM-driven decision: when to route to a different agent.
// Everything else (pricing, region, hours) is deterministic.
// =============================================================================

// Appended to ALL agents — instructs them to emit [CONTEXT] signals when they
// collect key data. These are parsed client-side to populate coreData and run
// deterministic derivations (region → pricing, phone validation, etc.)
const CONTEXT_EXTRACTION_INSTRUCTIONS = `

DATA SIGNALS: When the caller provides key information, silently append a [CONTEXT] signal at the very end of your response. The caller cannot see these.

[CONTEXT:customer_name=John Smith]               — when you learn their name
[CONTEXT:phone=555-123-4567]                     — when you learn their phone number
[CONTEXT:address=123 Oak St, Springfield]        — when you learn their service address

Combine multiple fields with |: [CONTEXT:customer_name=Jane|phone=555-9876]

CRITICAL TIMING RULES:
- Emit [CONTEXT] in the SAME response where you first receive the data — not a later turn.
- If you are about to call a tool AND you just collected data, emit [CONTEXT] in that same response.
- Do not repeat fields already emitted in prior turns.

EXAMPLES (follow these exactly):
- Caller says "I'm James, my number is 555-1234" → end your response with: [CONTEXT:customer_name=James|phone=555-1234]
- Caller says "123 Oak Street, Springfield" → end your response with: [CONTEXT:address=123 Oak Street, Springfield]
- Caller says "I'm at 45 Palm Avenue, Ogdenville" → end your response with: [CONTEXT:address=45 Palm Avenue, Ogdenville]`

const ROUTER_HANDOFF_INSTRUCTIONS = `

ROUTING: When you know the caller's name and intent, respond naturally and append ONE of these signals on a new line at the very end:

[HANDOFF:booking] — new service request
[HANDOFF:job_inquiry] — existing job, prior booking, checking on past service
[HANDOFF:complaint] — complaint or dissatisfaction
[HANDOFF:billing] — billing, invoice, payment
[HANDOFF:escalation] — caller demands a human/manager/supervisor

RULES:
- Do NOT hand off until you have the caller's name.
- If intent is ambiguous, ask a clarifying question instead.
- Do NOT say "let me transfer you" or "one moment". Routing is invisible to the caller.`

// Per-agent handoff instructions — explicit triggers prevent the LLM from
// keeping calls in the wrong agent when intent changes mid-conversation.
const BOOKING_HANDOFF_INSTRUCTIONS = `

ROUTING: You handle NEW service bookings only. If the caller's need changes, route immediately:

[HANDOFF:job_inquiry] — caller says they already have a booking/appointment/job scheduled, or wants to check on an existing job
[HANDOFF:billing]     — caller asks about payment methods, invoices, cost disputes, or billing
[HANDOFF:complaint]   — caller expresses dissatisfaction about a past service or technician
[HANDOFF:escalation]  — caller demands a manager, supervisor, or human agent

Append the signal on a new line at the very end of your response. Do NOT say "let me transfer you". Routing is invisible.`

const JOB_INQUIRY_HANDOFF_INSTRUCTIONS = `

ROUTING: You handle existing job lookups only. Always call confirm_lead_details first.

When caller's need changes, append ONE signal on its own line at the very end:

[HANDOFF:booking]   — new appointment needed
[HANDOFF:billing]   — payment or invoice question
[HANDOFF:complaint] — ANY unhappiness, complaint, or criticism about past service

CRITICAL RULES:
- The [HANDOFF] signal IS the transfer. It is instant and invisible to the caller.
- Do NOT say "one moment", "let me connect you", or "please hold" — just respond and append the signal.
- Do NOT use [HANDOFF:escalation] — route complaints to complaint agent first.
- Do NOT route before calling confirm_lead_details.

EXAMPLE — caller says "I'm unhappy about the technician":
  "I'm really sorry to hear that. I'll make sure this gets to our complaint team.
  [HANDOFF:complaint]"

EXAMPLE — caller says "can I book a new appointment":
  "Of course! Let me get you over to booking.
  [HANDOFF:booking]"`

const COMPLAINT_HANDOFF_INSTRUCTIONS = `

ROUTING: You handle complaints. After 2 exchanges attempting resolution, or if caller demands a manager, escalate.

[HANDOFF:escalation]  — caller demands a manager, supervisor, or human agent

CRITICAL RULES:
- The [HANDOFF] signal IS the escalation. It is instant and invisible.
- Do NOT say "one moment" or "please hold" — just respond and append the signal.

EXAMPLE — caller says "I want to speak to a manager":
  "I completely understand. Let me get our management team on the line for you right away.
  [HANDOFF:escalation]"`

function getHandoffInstructions(agentKey) {
  switch (agentKey) {
    case 'router':     return ROUTER_HANDOFF_INSTRUCTIONS
    case 'booking':    return BOOKING_HANDOFF_INSTRUCTIONS
    case 'job_inquiry': return JOB_INQUIRY_HANDOFF_INSTRUCTIONS
    case 'complaint':  return COMPLAINT_HANDOFF_INSTRUCTIONS
    default:           return BOOKING_HANDOFF_INSTRUCTIONS
  }
}

// Simulated tool results for demo
const SIMULATED_TOOL_RESULTS = {
  generate_appointment_slots: (data) => {
    const tech = data.assigned_techs || 'our next available technician'
    return `SYSTEM TOOL RESULT: Available slots — Tomorrow 9:00 AM with ${tech.split(' or ')[0]}, or Friday 1:00 PM with ${tech.split(' or ')[1] || tech.split(' or ')[0]}. Service: standard treatment at $${data.pricing_base || 149}.`
  },
  confirm_lead_details: (data) => {
    const tech = data.assigned_techs ? data.assigned_techs.split(' or ')[0] : 'a technician'
    return `SYSTEM TOOL RESULT: Account found. Active job #T-${Math.floor(100 + Math.random() * 900)} at ${data.address || 'this address'}. Last visit: ${tech} on Jan 15. Status: treatment applied, follow-up scheduled.`
  },
  book_appointment: (data) => {
    return `SYSTEM TOOL RESULT: Appointment confirmed. Ref: TORK-${Math.floor(1000 + Math.random() * 9000)}. ${data.assigned_techs ? data.assigned_techs.split(' or ')[0] : 'Technician'} will arrive at the scheduled time. Cost: $${data.pricing_base || 149}.`
  },
  raise_callback_request: (data) => {
    const managers = { north: 'Sarah Chen', south: 'Diego Morales', east: 'Priya Patel', west: 'Ryan O\'Brien' }
    const mgr = managers[data.service_region] || 'our area manager'
    return `SYSTEM TOOL RESULT: Priority callback scheduled. ${mgr} will call ${data.phone_formatted || data.phone || 'the caller'} within 2 hours.`
  },
}

// =============================================================================
// HELPERS
// =============================================================================

// Agent-aware tool detection — prevents false positives (e.g. job_inquiry agent
// saying "let me check on that appointment" triggering generate_appointment_slots).
// Each agent only matches tools it actually has access to.
function detectToolCall(text, agentKey) {
  const byAgent = {
    booking: [
      { pattern: /available.*slot|time slot|checking.*availab/i, tool: 'generate_appointment_slots' },
      { pattern: /confirmed.*appoint|confirmation.*number|I'?ve (booked|scheduled)|confirm(?:ing)? (?:that )?(?:your )?booking|confirming.*appointment/i, tool: 'book_appointment' },
      { pattern: /callback.*schedul|manager.*will.*call|we'?ll call you back/i, tool: 'raise_callback_request' },
    ],
    job_inquiry: [
      { pattern: /look(?:ing)? up|checking.*(?:record|service|previous|old|history)|found.*(?:account|job)|job.*#|JOB-|pull up.*record/i, tool: 'confirm_lead_details' },
    ],
    complaint: [
      { pattern: /callback.*schedul|manager.*will.*call|we'?ll call you back/i, tool: 'raise_callback_request' },
    ],
    router: [],
  }
  const patterns = byAgent[agentKey] || byAgent.booking
  for (const { pattern, tool } of patterns) {
    if (pattern.test(text)) return tool
  }
  return null
}

// Deterministic fallback: extract key fields from agent response text when
// the LLM forgets to emit a [CONTEXT] signal. Catches agent confirmation phrases.
function extractDataFromText(text, existingData) {
  const updates = {}

  // Address — agent typically confirms with "your address as/is/at X"
  if (!existingData.address) {
    const addrPatterns = [
      /(?:your |the )?(?:service )?address\s+(?:is|as|at)\s+([0-9]+[^[\n.!?]{5,60})/i,
      /noted?\s+(?:your\s+)?address\s+(?:as|at|is)\s+([0-9]+[^[\n.!?]{5,60})/i,
      /I have\s+(?:your\s+)?address\s+(?:as|at|is)\s+([0-9]+[^[\n.!?]{5,60})/i,
    ]
    for (const p of addrPatterns) {
      const m = text.match(p)
      if (m) { updates.address = m[1].trim().replace(/[.,!?]+$/, ''); break }
    }
  }

  // Name — agent greets confirmed name: "Thank you, John!" or "Got it, Jane."
  if (!existingData.customer_name) {
    const nameMatch = text.match(/(?:Thank you|Got it|Great|Perfect|Hi|Hello),\s+([A-Z][a-z]+)(?:[!.,]|$)/m)
    if (nameMatch) updates.customer_name = nameMatch[1]
  }

  return Object.keys(updates).length > 0 ? updates : null
}

// Parses [CONTEXT:field=value|field=value] emitted by agents to populate coreData.
// Removes the signal from visible text — the caller never sees it.
function parseContextSignal(text) {
  const match = text.match(/\[CONTEXT:([^\]]+)\]/)
  if (!match) return null
  const updates = {}
  for (const pair of match[1].split('|')) {
    const eqIdx = pair.indexOf('=')
    if (eqIdx > 0) {
      const key = pair.slice(0, eqIdx).trim()
      const val = pair.slice(eqIdx + 1).trim()
      if (key && val) updates[key] = val
    }
  }
  const cleanText = text.replace(/\s*\[CONTEXT:[^\]]+\]/g, '').trim()
  return Object.keys(updates).length > 0 ? { updates, cleanText } : null
}

function parseHandoffSignal(text) {
  const match = text.match(/\[HANDOFF:(booking|job_inquiry|complaint|billing|router|escalation)\]/)
  if (!match) return null
  const cleanText = text.replace(/\n?\[HANDOFF:(?:booking|job_inquiry|complaint|billing|router|escalation)\].*$/s, '').trim()
  return { target: match[1], cleanText }
}

function ts() {
  return new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function formatPrompt(prompt, data) {
  let r = prompt
  try {
    r = r.replace(/\{customer_name\}/g, data.customer_name || 'Caller')
    r = r.replace(/\{phone\}/g, data.phone_formatted || data.phone || '')
    r = r.replace(/\{address\}/g, data.address || '')
  } catch {}
  return r
}

// =============================================================================
// COMPONENT
// =============================================================================

export function SquadTestingModal({ isOpen, onClose, squad }) {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [currentAgentKey, setCurrentAgentKey] = useState(squad.entry_agent_key)
  const [coreData, setCoreData] = useState({})
  const [turnCount, setTurnCount] = useState(0)
  const [orchestrationLog, setOrchestrationLog] = useState([])
  const [selectedScenario, setSelectedScenario] = useState(null)
  const [scenarioStep, setScenarioStep] = useState(0)
  const [chatHistory, setChatHistory] = useState([]) // SHARED across handoffs

  const messagesEndRef = useRef(null)
  const logEndRef = useRef(null)

  const agents = squad.agents || {}
  const agentsList = Array.isArray(agents) ? agents : Object.values(agents)
  const agentsMap = Array.isArray(agents)
    ? agents.reduce((m, a) => ({ ...m, [a.key]: a }), {})
    : agents

  useEffect(() => { if (isOpen) resetSession() }, [isOpen])
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])
  useEffect(() => { logEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [orchestrationLog])

  const addLog = (type, message, details = {}) => {
    setOrchestrationLog(prev => [...prev, { time: ts(), type, message, details }])
  }

  const resetSession = () => {
    const entryKey = squad.entry_agent_key
    setCurrentAgentKey(entryKey)
    const hours = deriveBusinessHours()
    setCoreData({ ...hours })
    setTurnCount(0)
    setScenarioStep(0)
    setSelectedScenario(null)
    setChatHistory([])
    setMessages([])
    setOrchestrationLog([{
      time: ts(),
      type: 'SESSION_START',
      message: `Entry: ${agentsMap[entryKey]?.name || entryKey} | ${hours.is_business_hours ? 'Business hours' : 'After hours'} (${hours.current_time})`,
      details: {}
    }])

    const greeting = "Hello, thank you for calling Torkin Pest Control. This is Mike, how can I help you today?"
    setMessages([{ id: Date.now(), text: greeting, sender: 'agent', agentKey: entryKey, timestamp: new Date() }])
    setChatHistory([{ role: 'assistant', content: greeting }])
  }

  // --- Handoff: swap system prompt, KEEP chat history ---
  const executeHandoff = (fromKey, targetKey, data, reason) => {
    addLog('HANDOFF_TRIGGERED', `${agentsMap[fromKey]?.name} → ${agentsMap[targetKey]?.name}`, {
      from: fromKey, to: targetKey, reason,
      chat_history: `PRESERVED (${chatHistory.length} turns)`,
      core_data_passed: Object.keys(data).filter(k => !k.startsWith('is_')).join(', ')
    })
    setCurrentAgentKey(targetKey)
    setTurnCount(0)
    // chatHistory NOT cleared — next agent sees the full conversation

    const targetAgent = agentsMap[targetKey]
    addLog('AGENT_ACTIVATED', `${targetAgent?.name}`, {
      tools: targetAgent?.tools || [],
    })

    // Log conditional prompts that will apply to new agent
    const { triggers } = buildConditionalSections(targetKey, data)
    if (triggers.length > 0) {
      addLog('CONDITIONAL_PROMPT', `Active conditions for ${targetAgent?.name}`, {
        triggers: triggers.join(', ')
      })
    }
  }

  // --- Build API payload: agent prompt + conditional sections + core data + full history ---
  const buildPayload = (userMsg, agentKey, history, data) => {
    const agent = agentsMap[agentKey]
    let prompt = formatPrompt(agent?.prompt || '', data)

    // Per-agent handoff instructions (explicit triggers prevent misrouting)
    prompt += getHandoffInstructions(agentKey)

    // Context extraction instructions (feeds deterministic derivation pipeline)
    prompt += CONTEXT_EXTRACTION_INSTRUCTIONS

    // Conditional prompt sections (Chrysalis)
    const { sections } = buildConditionalSections(agentKey, data)
    if (sections.length > 0) {
      prompt += '\n\n--- ACTIVE CONDITIONS ---\n' + sections.join('\n\n')
    }

    const conversation_history = [{ role: 'system', content: prompt }]

    // Core data injection — concise, authoritative
    const fields = []
    if (data.customer_name) fields.push(`Name: ${data.customer_name}`)
    if (data.phone) fields.push(`Phone: ${data.phone_formatted || data.phone}${data.phone_valid === false ? ' (INVALID — ask to confirm)' : ''}`)
    if (data.address) fields.push(`Address: ${data.address}`)
    if (data.service_region) fields.push(`Region: ${data.service_region}`)
    if (data.intent) fields.push(`Intent: ${data.intent}`)
    if (fields.length > 0) {
      conversation_history.push({
        role: 'system',
        content: `COLLECTED — do NOT re-ask:\n${fields.join('\n')}`
      })
    }

    // Full chat history (shared across agents)
    for (const msg of history) conversation_history.push(msg)

    return { message: userMsg, conversation_history, model: 'gpt-4o', temperature: 0.7 }
  }

  // --- Main send handler ---
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isTyping) return
    const userMsg = inputMessage.trim()
    setInputMessage('')

    setMessages(prev => [...prev, { id: Date.now(), text: userMsg, sender: 'user', timestamp: new Date() }])

    const newTurn = turnCount + 1
    setTurnCount(newTurn)
    addLog('TURN_COUNT', `Turn ${newTurn} for ${agentsMap[currentAgentKey]?.name}`)

    setIsTyping(true)
    try {
      const newHistory = [...chatHistory, { role: 'user', content: userMsg }]
      setChatHistory(newHistory)

      const payload = buildPayload(userMsg, currentAgentKey, newHistory, coreData)
      const response = await api.post('/api/agents/1/chat', payload)
      let agentReply = response.data?.response || "I'm sorry, could you repeat that?"

      // --- Parse and apply [CONTEXT] signals first (feeds deterministic pipeline) ---
      let latestData = coreData
      const ctx = parseContextSignal(agentReply)
      if (ctx) {
        agentReply = ctx.cleanText
        const merged = { ...coreData, ...ctx.updates }
        const { newData, logs } = runDerivations(merged)
        logs.forEach(l => addLog(l.type, l.message, l.details))
        if (logs.length > 0 || Object.keys(ctx.updates).length > 0) {
          const updatedFields = Object.keys(ctx.updates).join(', ')
          addLog('DERIVED_DATA', `Context collected: ${updatedFields}`, { source: '[CONTEXT] signal', updates: ctx.updates })
        }
        setCoreData(newData)
        latestData = newData
      }

      // --- Deterministic fallback: extract data from agent text if [CONTEXT] was missed ---
      const textExtracted = extractDataFromText(agentReply, latestData)
      if (textExtracted) {
        const merged = { ...latestData, ...textExtracted }
        const { newData, logs } = runDerivations(merged)
        logs.forEach(l => addLog(l.type, l.message, l.details))
        if (Object.keys(textExtracted).length > 0) {
          addLog('DERIVED_DATA', `Fallback extracted: ${Object.keys(textExtracted).join(', ')}`, { source: 'text pattern match', updates: textExtracted })
        }
        setCoreData(newData)
        latestData = newData
      }

      // --- Parse handoff signal ---
      const handoff = parseHandoffSignal(agentReply)

      if (handoff) {
        const displayText = handoff.cleanText

        // Escalation
        if (handoff.target === 'escalation') {
          addLog('ESCALATION', 'Caller requested human agent', { from: currentAgentKey })
          const msg = displayText || "I completely understand. Let me arrange a callback from our manager."
          setMessages(prev => [...prev, { id: Date.now() + 2, text: msg, sender: 'agent', agentKey: currentAgentKey, timestamp: new Date(), toolUsed: 'raise_callback_request' }])
          setChatHistory(prev => [...prev, { role: 'assistant', content: msg }])

          // Simulate callback tool (use latestData for region-specific manager name)
          const toolResult = SIMULATED_TOOL_RESULTS.raise_callback_request(latestData)
          addLog('TOOL_CALLED', 'raise_callback_request', { result: toolResult })

          setTimeout(async () => {
            setIsTyping(true)
            try {
              const sysHistory = [...newHistory, { role: 'assistant', content: msg }, { role: 'system', content: toolResult }]
              const followUp = await api.post('/api/agents/1/chat', buildPayload("Relay the callback confirmation to the caller.", currentAgentKey, sysHistory, latestData))
              let reply = followUp.data?.response || "A manager will call you back within 2 hours."
              const h = parseHandoffSignal(reply)
              if (h) reply = h.cleanText
              setMessages(prev => [...prev, { id: Date.now() + 10, text: reply, sender: 'agent', agentKey: currentAgentKey, timestamp: new Date() }])
              setChatHistory(prev => [...prev, { role: 'assistant', content: reply }])
            } catch {} finally { setIsTyping(false) }
          }, 800)
          return
        }

        // Billing — deterministic hard transfer
        if (handoff.target === 'billing') {
          addLog('DETERMINISTIC_ROUTE', 'Billing → hard transfer (no LLM)', { action: 'transfer_to_team' })
          const msg = displayText || `I'll connect you with our Billing team right away. Reference: REF-${Math.floor(1000 + Math.random() * 9000)}.`
          setMessages(prev => [...prev, { id: Date.now() + 2, text: msg, sender: 'agent', agentKey: currentAgentKey, timestamp: new Date(), toolUsed: 'transfer_to_team' }])
          setChatHistory(prev => [...prev, { role: 'assistant', content: msg }])
          return
        }

        // Normal handoff
        addLog('INTENT_CLASSIFIED', `"${handoff.target}" (LLM routing decision)`, { from: currentAgentKey })
        if (displayText) {
          setMessages(prev => [...prev, { id: Date.now() + 3, text: displayText, sender: 'agent', agentKey: currentAgentKey, timestamp: new Date() }])
          setChatHistory(prev => [...prev, { role: 'assistant', content: displayText }])
        }

        // latestData already has [CONTEXT] updates applied; merge intent and re-derive
        const updatedData = { ...latestData, intent: handoff.target }
        const { newData, logs } = runDerivations(updatedData)
        logs.forEach(l => addLog(l.type, l.message, l.details))
        setCoreData(newData)
        executeHandoff(currentAgentKey, handoff.target, newData, `LLM routing: ${handoff.target}`)
        return
      }

      // --- No handoff: normal response ---

      // Agent-aware tool detection (prevents cross-agent false positives)
      const toolUsed = detectToolCall(agentReply, currentAgentKey)

      setMessages(prev => [...prev, {
        id: Date.now() + 5, text: agentReply, sender: 'agent',
        agentKey: currentAgentKey, timestamp: new Date(), toolUsed
      }])
      const updatedHistory = [...newHistory, { role: 'assistant', content: agentReply }]
      setChatHistory(updatedHistory)

      // Simulate tool result and follow-up (uses latestData for region-specific results)
      if (toolUsed && SIMULATED_TOOL_RESULTS[toolUsed]) {
        const toolResultFn = SIMULATED_TOOL_RESULTS[toolUsed]
        const toolResult = typeof toolResultFn === 'function' ? toolResultFn(latestData) : toolResultFn
        addLog('TOOL_CALLED', toolUsed, { result: 'Simulated with core data' })

        setTimeout(async () => {
          setIsTyping(true)
          try {
            const sysHistory = [...updatedHistory, { role: 'system', content: toolResult }]
            setChatHistory(sysHistory)
            const followUp = await api.post('/api/agents/1/chat', buildPayload("Present the tool results to the caller naturally.", currentAgentKey, sysHistory, latestData))
            let reply = followUp.data?.response || ""
            const ctxFollowUp = parseContextSignal(reply)
            if (ctxFollowUp) { reply = ctxFollowUp.cleanText }
            const h = parseHandoffSignal(reply)
            if (h) {
              // Handoff triggered from within tool follow-up
              if (h.cleanText) {
                setMessages(prev => [...prev, { id: Date.now() + 10, text: h.cleanText, sender: 'agent', agentKey: currentAgentKey, timestamp: new Date() }])
                setChatHistory(prev => [...prev, { role: 'assistant', content: h.cleanText }])
              }
              const ud = { ...latestData, intent: h.target }
              const { newData: nd, logs: hl } = runDerivations(ud)
              hl.forEach(l => addLog(l.type, l.message, l.details))
              setCoreData(nd)
              executeHandoff(currentAgentKey, h.target, nd, `LLM routing: ${h.target}`)
            } else if (reply) {
              setMessages(prev => [...prev, { id: Date.now() + 10, text: reply, sender: 'agent', agentKey: currentAgentKey, timestamp: new Date() }])
              setChatHistory(prev => [...prev, { role: 'assistant', content: reply }])
            }
          } catch (err) { console.error('Follow-up error:', err) }
          finally { setIsTyping(false) }
        }, 800)
      } else {
        // No tool — check for "wait" phrases (agent says "one moment" but takes no action).
        // Auto-nudge the agent to complete the action so the user doesn't have to type "ok".
        const waitPhrase = /one moment|please hold|just a moment|hold on.*moment/i
        if (waitPhrase.test(agentReply)) {
          setTimeout(async () => {
            setIsTyping(true)
            try {
              const nudgeHistory = [...updatedHistory, { role: 'user', content: '[system: continue — complete the action now, do not make the caller wait]' }]
              const nudge = await api.post('/api/agents/1/chat', buildPayload("Continue and complete the action you just described.", currentAgentKey, nudgeHistory, latestData))
              let reply = nudge.data?.response || ""
              const ctxNudge = parseContextSignal(reply)
              if (ctxNudge) {
                reply = ctxNudge.cleanText
                const { newData: nd, logs } = runDerivations({ ...latestData, ...ctxNudge.updates })
                logs.forEach(l => addLog(l.type, l.message, l.details))
                setCoreData(nd)
              }
              const h = parseHandoffSignal(reply)
              if (h) {
                if (h.cleanText) {
                  setMessages(prev => [...prev, { id: Date.now() + 20, text: h.cleanText, sender: 'agent', agentKey: currentAgentKey, timestamp: new Date() }])
                  setChatHistory(prev => [...prev, { role: 'assistant', content: h.cleanText }])
                }
                const ud = { ...latestData, intent: h.target }
                const { newData: nd, logs: hl } = runDerivations(ud)
                hl.forEach(l => addLog(l.type, l.message, l.details))
                setCoreData(nd)
                executeHandoff(currentAgentKey, h.target, nd, `LLM routing: ${h.target}`)
              } else {
                const toolInNudge = detectToolCall(reply, currentAgentKey)
                if (reply) {
                  setMessages(prev => [...prev, { id: Date.now() + 20, text: reply, sender: 'agent', agentKey: currentAgentKey, timestamp: new Date(), toolUsed: toolInNudge || undefined }])
                  setChatHistory(prev => [...prev, { role: 'assistant', content: reply }])
                }
              }
            } catch (err) { console.error('Nudge error:', err) }
            finally { setIsTyping(false) }
          }, 600)
        }
      }

    } catch (err) {
      console.error('Chat error:', err)
      setMessages(prev => [...prev, {
        id: Date.now() + 5,
        text: "I apologize, I'm having a technical issue. Could you repeat that?",
        sender: 'agent', agentKey: currentAgentKey, timestamp: new Date()
      }])
    } finally {
      setIsTyping(false)
    }
  }

  // Core data is updated in two places:
  // 1. [CONTEXT] signals parsed from every agent response → runDerivations (address→region→pricing)
  // 2. On handoff: intent merged in, runDerivations runs again with full context

  const handleScenarioSelect = (s) => { resetSession(); setSelectedScenario(s); setScenarioStep(0) }
  const handleScenarioStep = () => {
    if (!selectedScenario || scenarioStep >= selectedScenario.messages.length) return
    setInputMessage(selectedScenario.messages[scenarioStep])
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
              <h2 className="text-lg font-bold text-gray-900">Squad Orchestration Demo</h2>
              <p className="text-sm text-gray-500">{squad.name} — Multi-Agent + Deterministic Data Framework</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${coreData.is_business_hours ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'}`}>
              {coreData.is_business_hours ? 'Business Hours' : 'After Hours'}
            </span>
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${currentColors.bg} ${currentColors.text}`}>
              {currentAgent?.name || currentAgentKey}
            </span>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="h-5 w-5" /></button>
          </div>
        </div>

        {/* 3-Panel Layout */}
        <div className="flex flex-1 overflow-hidden">

          {/* LEFT PANEL */}
          <div className="w-64 border-r bg-gray-50 flex flex-col overflow-y-auto">
            {/* Agent Map */}
            <div className="p-4 border-b">
              <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-1.5"><Zap className="h-4 w-4" /> Agent Map</h3>
            </div>
            <div className="p-3 space-y-2">
              {agentsList.map(agent => {
                const colors = AGENT_COLORS[agent.key] || DEFAULT_COLOR
                const isActive = agent.key === currentAgentKey
                return (
                  <div key={agent.key} className={`p-3 rounded-lg border-2 transition-all ${isActive ? `${colors.border} ${colors.bg} shadow-sm` : 'border-gray-200 bg-white'}`}>
                    <div className="flex items-center gap-2 mb-1">
                      {isActive && <span className={`w-2.5 h-2.5 rounded-full ${colors.dot} animate-pulse`}></span>}
                      <span className={`text-sm font-medium ${isActive ? colors.text : 'text-gray-700'}`}>{agent.name}</span>
                    </div>
                    {agent.tools?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {agent.tools.map(t => (
                          <span key={t} className="px-1.5 py-0.5 bg-white rounded text-[9px] text-gray-500 border">{t.replace(/_/g, ' ')}</span>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>

            {/* Core Data Panel */}
            <div className="p-3 border-t">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1">
                <Database className="h-3 w-3" /> Core Data
              </h4>
              <div className="space-y-1.5">
                {/* Primary fields */}
                {[['customer_name', 'Name'], ['phone', 'Phone'], ['address', 'Address'], ['intent', 'Intent']].map(([key, label]) => (
                  <div key={key} className="flex justify-between text-[10px]">
                    <span className="text-gray-500">{label}:</span>
                    <span className={`font-medium truncate ml-1 max-w-[100px] ${coreData[key] ? 'text-gray-700' : 'text-gray-300 italic'}`}>
                      {key === 'phone' && coreData.phone_formatted ? coreData.phone_formatted : (coreData[key] || '—')}
                    </span>
                  </div>
                ))}
                {/* Derived fields */}
                {coreData.service_region && (
                  <>
                    <div className="border-t border-dashed border-gray-300 mt-2 pt-2">
                      <p className="text-[9px] text-teal-600 uppercase tracking-wide mb-1 font-semibold">Derived (deterministic)</p>
                    </div>
                    {[
                      ['Region', coreData.service_region],
                      ['Base Price', coreData.pricing_base ? `$${coreData.pricing_base}` : null],
                      ['Emergency', coreData.pricing_emergency ? `$${coreData.pricing_emergency}` : null],
                      ['Technicians', coreData.assigned_techs],
                      ['Dispatch', coreData.dispatch_center],
                    ].filter(([,v]) => v).map(([label, val]) => (
                      <div key={label} className="flex justify-between text-[10px]">
                        <span className="text-teal-600">{label}:</span>
                        <span className="text-teal-700 font-medium truncate ml-1 max-w-[100px]">{val}</span>
                      </div>
                    ))}
                  </>
                )}
              </div>
            </div>

            {/* Scenarios */}
            <div className="p-3 border-t">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Scenarios</h4>
              <div className="space-y-1.5">
                {SQUAD_SCENARIOS.map(s => (
                  <button key={s.id} onClick={() => handleScenarioSelect(s)}
                    className={`w-full text-left px-2 py-1.5 rounded text-xs transition-colors ${selectedScenario?.id === s.id ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100 text-gray-600'}`}>
                    <span className="mr-1">{s.icon}</span> {s.name}
                  </button>
                ))}
              </div>
              {selectedScenario && scenarioStep < selectedScenario.messages.length && (
                <button onClick={handleScenarioStep}
                  className="w-full mt-2 px-2 py-1.5 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700">
                  Next ({scenarioStep + 1}/{selectedScenario.messages.length})
                </button>
              )}
            </div>
          </div>

          {/* CENTER — Conversation */}
          <div className="flex-1 flex flex-col min-w-0">
            <div className="p-3 border-b bg-white">
              <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
                <MessageCircle className="h-4 w-4" /> Caller View
                <span className="text-[10px] text-gray-400 font-normal ml-2">Caller sees one continuous conversation</span>
              </h3>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.map(msg => {
                const isUser = msg.sender === 'user'
                return (
                  <div key={msg.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-md ${isUser ? 'bg-blue-600 text-white rounded-lg rounded-br-none' : 'bg-gray-100 text-gray-800 rounded-lg rounded-bl-none'} px-4 py-2.5`}>
                      <p className="text-sm">{msg.text}</p>
                      {msg.toolUsed && (
                        <div className="mt-1.5 flex items-center gap-1 text-[10px] opacity-70">
                          <Zap className="h-3 w-3" />{msg.toolUsed}
                        </div>
                      )}
                      <p className="text-[10px] mt-1 opacity-50">{msg.timestamp.toLocaleTimeString()}</p>
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

            <div className="p-4 border-t">
              <div className="flex gap-2">
                <input type="text" value={inputMessage} onChange={e => setInputMessage(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Type a message as the caller..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                  disabled={isTyping} />
                <button onClick={handleSendMessage} disabled={!inputMessage.trim() || isTyping}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                  <Send className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>

          {/* RIGHT — Orchestration Log */}
          <div className="w-80 border-l bg-gray-900 flex flex-col overflow-hidden">
            <div className="p-3 border-b border-gray-700">
              <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-1.5">
                <Terminal className="h-4 w-4" /> Orchestration Log
                <span className="text-[10px] text-gray-500 font-normal ml-2">Operator view</span>
              </h3>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-2 font-mono text-[11px]">
              {orchestrationLog.map((entry, i) => (
                <div key={i} className="border-b border-gray-800 pb-2">
                  <div className="flex items-start gap-2">
                    <span className="text-gray-500 flex-shrink-0">[{entry.time}]</span>
                    <span className={`font-semibold ${LOG_COLORS[entry.type] || 'text-gray-400'}`}>{entry.type}</span>
                  </div>
                  <p className="text-gray-400 ml-[70px] mt-0.5">{entry.message}</p>
                  {entry.details && Object.keys(entry.details).length > 0 && (
                    <div className="ml-[70px] mt-1 text-gray-500">
                      {Object.entries(entry.details).map(([k, v]) => (
                        <div key={k}>
                          <span className="text-gray-600">{k}:</span>{' '}
                          <span className="text-gray-400">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              <div ref={logEndRef} />
            </div>

            <div className="p-3 border-t border-gray-700">
              <button onClick={resetSession}
                className="w-full px-3 py-1.5 bg-gray-700 text-gray-300 rounded text-xs font-medium hover:bg-gray-600 transition-colors">
                Reset Session
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
