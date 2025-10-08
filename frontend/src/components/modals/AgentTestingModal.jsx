import React, { useState, useEffect, useRef } from 'react';
import { Button } from '../ui/Button';

export function AgentTestingModal({ isOpen, onClose, agentConfig, wizardData }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [testMode, setTestMode] = useState('chat'); // 'chat' or 'call'
  const [isCallActive, setIsCallActive] = useState(false);
  const [callDuration, setCallDuration] = useState(0);
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [sidebarSection, setSidebarSection] = useState('prompt'); // 'prompt' or 'scenarios'
  const messagesEndRef = useRef(null);
  const callIntervalRef = useRef(null);

  // Predefined test scenarios
  const testScenarios = [
    {
      id: 'appointment_booking',
      name: 'Appointment Booking',
      description: 'Customer wants to schedule a service appointment',
      initialMessage: "Hi, I'd like to schedule an appointment for a plumbing repair at my home.",
      icon: '📅'
    },
    {
      id: 'pricing_inquiry',
      name: 'Pricing Inquiry',
      description: 'Customer asking about service pricing',
      initialMessage: "What are your rates for HVAC installation?",
      icon: '💰'
    },
    {
      id: 'emergency_service',
      name: 'Emergency Service',
      description: 'Urgent service request outside business hours',
      initialMessage: "Help! My water heater is leaking all over the floor. Can someone come out tonight?",
      icon: '🚨'
    },
    {
      id: 'general_inquiry',
      name: 'General Questions',
      description: 'Customer has questions about services',
      initialMessage: "Do you service my area? I'm located in downtown.",
      icon: '❓'
    },
    {
      id: 'difficult_customer',
      name: 'Difficult Customer',
      description: 'Challenging interaction requiring transfer',
      initialMessage: "Your prices are ridiculous! I've been waiting for 3 hours and nobody showed up!",
      icon: '😤'
    }
  ];

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      // Initialize with agent greeting
      const agentName = wizardData?.persona?.agentName || 'AI Assistant';
      const businessName = wizardData?.businessProfile?.businessName || 'our company';

      setMessages([{
        id: Date.now(),
        text: `Hi! I'm ${agentName} from ${businessName}. How can I help you today?`,
        sender: 'agent',
        timestamp: new Date(),
        toolsUsed: []
      }]);
    }
  }, [isOpen, wizardData]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isCallActive) {
      callIntervalRef.current = setInterval(() => {
        setCallDuration(prev => prev + 1);
      }, 1000);
    } else {
      if (callIntervalRef.current) {
        clearInterval(callIntervalRef.current);
      }
    }

    return () => {
      if (callIntervalRef.current) {
        clearInterval(callIntervalRef.current);
      }
    };
  }, [isCallActive]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatCallDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const simulateAgentResponse = async (userMessage) => {
    setIsTyping(true);

    try {
      // Get conversation history for context
      const conversationHistory = messages
        .filter(msg => msg.sender !== 'system')
        .map(msg => ({
          role: msg.sender === 'user' ? 'user' : 'assistant',
          content: msg.text
        }));

      // Try to get real OpenAI response first
      const apiUrl = 'https://lead-management-staging-backend.onrender.com';
      const response = await fetch(`${apiUrl}/api/agents/1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          conversation_history: conversationHistory,
          model: 'gpt-3.5-turbo',
          temperature: 0.7
        })
      });

      let agentResponse = '';
      let toolsUsed = [];
      let isRealAI = false;

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.response) {
          agentResponse = data.response;
          isRealAI = true;
        }
      }

      // Fallback to mock response if OpenAI fails
      if (!agentResponse) {
        agentResponse = getFallbackResponse(userMessage);
      }

      // Analyze message for tool usage (always use mock tool data)
      toolsUsed = analyzeForToolUsage(userMessage);

      setIsTyping(false);
      setMessages(prev => [...prev, {
        id: Date.now(),
        text: agentResponse,
        sender: 'agent',
        timestamp: new Date(),
        toolsUsed,
        isRealAI,
        aiType: isRealAI ? '🤖 OpenAI Response' : '💬 Fallback Response'
      }]);

    } catch (error) {
      console.error('Error getting AI response:', error);

      // Fallback to mock response on error
      const agentResponse = getFallbackResponse(userMessage);
      const toolsUsed = analyzeForToolUsage(userMessage);

      setIsTyping(false);
      setMessages(prev => [...prev, {
        id: Date.now(),
        text: agentResponse,
        sender: 'agent',
        timestamp: new Date(),
        toolsUsed,
        isRealAI: false,
        aiType: '💬 Fallback Response'
      }]);
    }
  };

  const getFallbackResponse = (userMessage) => {
    const messageLower = userMessage.toLowerCase();

    if (messageLower.includes('appointment') || messageLower.includes('schedule')) {
      return "I'd be happy to help you schedule an appointment! Let me check our availability. What type of service do you need, and what's your preferred date?";
    } else if (messageLower.includes('price') || messageLower.includes('cost') || messageLower.includes('rate')) {
      return "I can help you with pricing information. Our rates vary depending on the type of service and complexity of the job. For a detailed quote, I'd recommend scheduling a consultation.";
    } else if (messageLower.includes('emergency') || messageLower.includes('urgent') || messageLower.includes('help')) {
      return "I understand this is urgent! Let me connect you with our emergency service team right away. They should be able to assist you within the hour.";
    } else if (messageLower.includes('ridiculous') || messageLower.includes('waiting') || messageLower.includes('angry')) {
      return "I sincerely apologize for the inconvenience and frustration you've experienced. Let me transfer you to a manager who can address your concerns immediately and make this right.";
    } else {
      return "Thank you for reaching out! I'm here to help you with any questions about our services. How can I assist you today?";
    }
  };

  const analyzeForToolUsage = (userMessage) => {
    const messageLower = userMessage.toLowerCase();
    const toolsUsed = [];

    if (messageLower.includes('appointment') || messageLower.includes('schedule')) {
      if (wizardData?.tools?.appointment?.enabled) {
        toolsUsed.push({
          tool: '/appointment',
          action: 'Checking calendar availability',
          configured: wizardData.tools.appointment.configured
        });
      }
    }

    if (messageLower.includes('price') || messageLower.includes('cost') || messageLower.includes('rate')) {
      if (wizardData?.tools?.knowledge?.enabled) {
        toolsUsed.push({
          tool: '/knowledge',
          action: 'Searching pricing information',
          configured: wizardData.tools.knowledge.configured
        });
      }
    }

    if (messageLower.includes('emergency') || messageLower.includes('urgent') || messageLower.includes('help')) {
      if (wizardData?.tools?.transfer?.enabled) {
        toolsUsed.push({
          tool: '/transfer',
          action: 'Transferring to emergency team',
          configured: wizardData.tools.transfer.configured
        });
      }
    }

    if (messageLower.includes('ridiculous') || messageLower.includes('waiting') || messageLower.includes('angry')) {
      if (wizardData?.tools?.bailout?.enabled) {
        toolsUsed.push({
          tool: '/bailout',
          action: 'Escalating to manager',
          configured: wizardData.tools.bailout.configured
        });
      }
    }

    if (toolsUsed.length === 0 && wizardData?.tools?.knowledge?.enabled) {
      toolsUsed.push({
        tool: '/knowledge',
        action: 'Searching general information',
        configured: wizardData.tools.knowledge.configured
      });
    }

    return toolsUsed;
  };

  const handleSendMessage = () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: inputMessage.trim(),
      sender: 'user',
      timestamp: new Date(),
      toolsUsed: []
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');

    // Simulate agent response
    simulateAgentResponse(userMessage.text);
  };

  const handleScenarioSelect = (scenario) => {
    setSelectedScenario(scenario);
    setInputMessage(scenario.initialMessage);
  };

  const startCall = () => {
    setIsCallActive(true);
    setCallDuration(0);
    setTestMode('call');

    // Add call start message
    setMessages(prev => [...prev, {
      id: Date.now(),
      text: "📞 Call started - You can now speak or type to test the voice interface",
      sender: 'system',
      timestamp: new Date(),
      toolsUsed: []
    }]);
  };

  const endCall = () => {
    setIsCallActive(false);

    // Add call end message
    setMessages(prev => [...prev, {
      id: Date.now(),
      text: `📞 Call ended - Duration: ${formatCallDuration(callDuration)}`,
      sender: 'system',
      timestamp: new Date(),
      toolsUsed: []
    }]);
  };

  const clearChat = () => {
    setMessages([]);
    setSelectedScenario(null);
    // Re-initialize with greeting
    const agentName = wizardData?.persona?.agentName || 'AI Assistant';
    const businessName = wizardData?.businessProfile?.businessName || 'our company';

    setTimeout(() => {
      setMessages([{
        id: Date.now(),
        text: `Hi! I'm ${agentName} from ${businessName}. How can I help you today?`,
        sender: 'agent',
        timestamp: new Date(),
        toolsUsed: []
      }]);
    }, 100);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Test Your AI Agent</h2>
              <p className="text-sm text-gray-600">
                {wizardData?.persona?.agentName || 'AI Agent'} • {wizardData?.businessProfile?.businessName || 'Your Business'}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {/* Mode Toggle */}
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setTestMode('chat')}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  testMode === 'chat' ? 'bg-white text-blue-600 shadow' : 'text-gray-600'
                }`}
              >
                💬 Chat
              </button>
              <button
                onClick={() => setTestMode('call')}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  testMode === 'call' ? 'bg-white text-green-600 shadow' : 'text-gray-600'
                }`}
              >
                📞 Call
              </button>
            </div>

            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar with Tabs */}
          <div className="w-80 border-r bg-gray-50 flex flex-col">
            {/* Tab Headers */}
            <div className="border-b">
              <div className="flex">
                <button
                  onClick={() => setSidebarSection('prompt')}
                  className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                    sidebarSection === 'prompt'
                      ? 'bg-white text-blue-600 border-b-2 border-blue-600'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  📝 Prompt Preview
                </button>
                <button
                  onClick={() => setSidebarSection('scenarios')}
                  className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                    sidebarSection === 'scenarios'
                      ? 'bg-white text-blue-600 border-b-2 border-blue-600'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  🎭 Test Scenarios
                </button>
              </div>
            </div>

            {/* Tab Content */}
            {sidebarSection === 'prompt' ? (
              <div className="flex-1 flex flex-col">
                <div className="p-4 border-b">
                  <h3 className="font-semibold text-gray-900 mb-2">Agent Prompt</h3>
                  <p className="text-sm text-gray-600">Current prompt that defines your AI agent's behavior</p>
                </div>

                <div className="flex-1 overflow-y-auto p-4">
                  <div className="bg-white rounded-lg border p-4">
                    <div className="text-sm leading-relaxed whitespace-pre-wrap max-h-96 overflow-y-auto">
                      {agentConfig?.prompt || 'No prompt configured yet. Go to AI Instructions to set up your agent prompt.'}
                    </div>
                  </div>

                  {agentConfig?.prompt && (
                    <div className="mt-4 text-xs text-gray-500 space-y-1">
                      <div>Characters: {agentConfig.prompt.length}</div>
                      <div>Lines: {agentConfig.prompt.split('\n').length}</div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex-1 flex flex-col">
                <div className="p-4 border-b">
                  <h3 className="font-semibold text-gray-900 mb-2">Test Scenarios</h3>
                  <p className="text-sm text-gray-600">Choose a scenario to test your agent's responses</p>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                  {testScenarios.map((scenario) => (
                    <div
                      key={scenario.id}
                      onClick={() => handleScenarioSelect(scenario)}
                      className={`p-3 rounded-lg border cursor-pointer transition-all ${
                        selectedScenario?.id === scenario.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300 bg-white hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center mb-2">
                        <span className="text-lg mr-2">{scenario.icon}</span>
                        <h4 className="font-medium text-gray-900">{scenario.name}</h4>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{scenario.description}</p>
                      <p className="text-xs text-gray-500 italic">"{scenario.initialMessage}"</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Bottom Actions */}
            <div className="p-4 border-t space-y-2">
              <Button
                onClick={clearChat}
                variant="outline"
                className="w-full"
              >
                Clear Chat
              </Button>
              {testMode === 'call' && (
                <Button
                  onClick={isCallActive ? endCall : startCall}
                  className={`w-full ${
                    isCallActive
                      ? 'bg-red-600 hover:bg-red-700'
                      : 'bg-green-600 hover:bg-green-700'
                  }`}
                >
                  {isCallActive ? `End Call (${formatCallDuration(callDuration)})` : 'Start Call'}
                </Button>
              )}
            </div>
          </div>

          {/* Main Chat Area */}
          <div className="flex-1 flex flex-col">
            {/* Call Status (if in call mode) */}
            {testMode === 'call' && isCallActive && (
              <div className="bg-green-50 border-b px-6 py-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse mr-3"></div>
                    <span className="text-green-800 font-medium">Call Active</span>
                  </div>
                  <span className="text-green-700 font-mono">{formatCallDuration(callDuration)}</span>
                </div>
              </div>
            )}

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-xs lg:max-w-md xl:max-w-lg ${
                    message.sender === 'user'
                      ? 'bg-blue-600 text-white rounded-lg rounded-br-none'
                      : message.sender === 'system'
                      ? 'bg-gray-100 text-gray-800 rounded-lg border'
                      : 'bg-gray-100 text-gray-800 rounded-lg rounded-bl-none'
                  } px-4 py-2`}>
                    <p className="text-sm">{message.text}</p>

                    {/* AI Type Indicator */}
                    {message.sender === 'agent' && message.aiType && (
                      <div className="mt-2">
                        <span className={`text-xs px-2 py-1 rounded ${
                          message.isRealAI ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
                        }`}>
                          {message.aiType}
                        </span>
                      </div>
                    )}

                    {/* Tool Usage Indicators */}
                    {message.toolsUsed && message.toolsUsed.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {message.toolsUsed.map((tool, index) => (
                          <div key={index} className="flex items-center text-xs">
                            <div className={`w-2 h-2 rounded-full mr-2 ${
                              tool.configured ? 'bg-green-500' : 'bg-yellow-500'
                            }`}></div>
                            <span className="text-gray-600">
                              ⚙️ {tool.tool}: {tool.action}
                              {!tool.configured && ' (not configured)'}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}

                    <p className="text-xs mt-1 opacity-70">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}

              {/* Typing Indicator */}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 text-gray-800 rounded-lg rounded-bl-none px-4 py-2 max-w-xs">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t p-4">
              <div className="flex space-x-3">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder={testMode === 'call' ? "Type your message or speak..." : "Type your message..."}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isTyping}
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim() || isTyping}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  Send
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}