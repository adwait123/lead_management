import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { HatchWizardProvider, useHatchWizard } from './HatchWizardContext';
import { Card } from '../ui/Card';

// Import tab components
import { AgentBasicsTab } from './tabs/AgentBasicsTab';
import { KnowledgeBaseTab } from './tabs/KnowledgeBaseTab';
import { AIInstructionsTab } from './tabs/AIInstructionsTab';

const configTabs = [
  { id: 'basics', title: 'Agent Basics', component: AgentBasicsTab },
  { id: 'knowledge', title: 'Knowledge', component: KnowledgeBaseTab },
  { id: 'instructions', title: 'AI Instructions', component: AIInstructionsTab },
  { id: 'test', title: 'Test Agent', component: null } // We'll render test section inline
];

function HatchEditContent() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { wizardData, updateWizardData, deployAgent, isLoading, errors } = useHatchWizard();
  const [activeTab, setActiveTab] = useState('basics');
  const [loadingAgent, setLoadingAgent] = useState(true);
  const [agent, setAgent] = useState(null);
  const [testMessage, setTestMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [testing, setTesting] = useState(false);

  // Load agent data when component mounts
  useEffect(() => {
    if (id) {
      loadAgentData(id);
    }
  }, [id]);

  const loadAgentData = async (agentId) => {
    try {
      setLoadingAgent(true);
      const response = await fetch(`https://lead-management-j828.onrender.com/api/agents/${agentId}`);

      if (!response.ok) {
        throw new Error('Failed to load agent');
      }

      const agentData = await response.json();
      setAgent(agentData);

      console.log('=== LOADING AGENT FOR EDIT ===');
      console.log('Raw agent data from backend:', JSON.stringify(agentData, null, 2));

      // Transform agent data back to wizard format
      const wizardFormat = {
        agentType: agentData.type || 'conversational',
        industry: 'general', // Default since we don't store this
        useCase: agentData.use_case,
        selectedTemplate: {
          title: agentData.name,
          description: agentData.description,
          useCase: agentData.use_case
        },
        businessProfile: (() => {
          // Extract business profile from knowledge array
          const businessKnowledge = agentData.knowledge?.find(k => k.type === 'business_profile');
          return businessKnowledge?.content || {};
        })(),
        faq: (() => {
          // Extract FAQ from knowledge array
          const faqKnowledge = agentData.knowledge?.find(k => k.type === 'faq');
          return faqKnowledge?.content || [];
        })(),
        persona: {
          agentName: agentData.name,
          traits: agentData.personality_traits || [],
          communicationMode: agentData.conversation_settings?.voice_enabled && agentData.conversation_settings?.text_enabled ? 'both' :
                           agentData.conversation_settings?.voice_enabled ? 'voice' : 'text',
          additionalInstructions: agentData.custom_personality_instructions || ''
        },
        instructions: {
          systemPrompt: agentData.prompt_template,
          templateName: agentData.prompt_template_name || '',
          tools: agentData.enabled_tools?.map(tool => ({ name: tool })) || [],
          workflows: []
        },
        // Also store tools in the root wizardData.tools format for compatibility
        tools: (() => {
          const toolsObj = {};
          if (agentData.enabled_tools) {
            agentData.enabled_tools.forEach(toolName => {
              toolsObj[toolName] = { enabled: true };
            });
          }
          return toolsObj;
        })(),
        rules: {
          success: {
            action: 'move_to_scheduled',
            assignTo: 'sales_team',
            message: ''
          },
          bailout: {
            action: 'move_to_needs_attention',
            assignTo: 'front_desk',
            message: ''
          },
          discard: {
            action: 'move_to_disqualified',
            message: ''
          }
        }
      };

      console.log('Transformed wizard format for editing:', JSON.stringify(wizardFormat, null, 2));
      console.log('================================');

      updateWizardData(wizardFormat);
    } catch (error) {
      console.error('Error loading agent:', error);
      alert('Failed to load agent data');
      navigate('/agents');
    } finally {
      setLoadingAgent(false);
    }
  };

  const handleUpdate = async () => {
    try {
      // Use the existing deployAgent logic but make it update instead
      const agentData = transformToUpdateData();

      const response = await fetch(`https://lead-management-j828.onrender.com/api/agents/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(agentData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update agent');
      }

      const updatedAgent = await response.json();
      setAgent(updatedAgent); // Update local agent state
      alert(`✅ Agent "${updatedAgent.name}" updated successfully!`);
      navigate('/agents');
    } catch (error) {
      console.error('Error updating agent:', error);
      alert('Failed to update agent: ' + error.message);
    }
  };

  const handleTestAgent = async () => {
    if (!testMessage.trim()) return;

    const userMessage = testMessage.trim();
    setTestMessage(''); // Clear input immediately

    // Add user message to chat history
    setChatHistory(prev => [...prev, { type: 'user', message: userMessage, timestamp: new Date() }]);

    setTesting(true);
    try {
      // First, temporarily update the agent with current form data for testing
      const currentFormData = transformToUpdateData();

      // Update the agent temporarily for testing (without saving)
      const tempUpdateResponse = await fetch(`https://lead-management-j828.onrender.com/api/agents/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(currentFormData)
      });

      if (!tempUpdateResponse.ok) {
        throw new Error('Failed to update agent configuration for testing');
      }

      // Now test with the updated configuration
      const response = await fetch(`https://lead-management-j828.onrender.com/api/agents/${id}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          model: currentFormData.model,
          temperature: parseFloat(currentFormData.temperature),
          max_tokens: currentFormData.max_tokens
        })
      });

      if (!response.ok) {
        throw new Error('Failed to test agent');
      }

      const data = await response.json();

      // Add agent response to chat history
      setChatHistory(prev => [...prev, {
        type: 'agent',
        message: data.response,
        timestamp: new Date(),
        usage: data.usage,
        success: data.success
      }]);

    } catch (err) {
      console.error('Error testing agent:', err);
      // Add error message to chat history
      setChatHistory(prev => [...prev, {
        type: 'error',
        message: `Error: ${err.message}`,
        timestamp: new Date()
      }]);
    } finally {
      setTesting(false);
    }
  };

  const clearChatHistory = () => {
    setChatHistory([]);
  };

  const transformToUpdateData = () => {
    const { persona, instructions, businessProfile, faq, tools } = wizardData;

    console.log('=== UPDATE TRANSFORMATION DEBUG ===');
    console.log('wizardData for update:', JSON.stringify(wizardData, null, 2));
    console.log('Extracted persona:', persona);
    console.log('Extracted instructions:', instructions);
    console.log('Extracted businessProfile:', businessProfile);
    console.log('Extracted faq:', faq);
    console.log('Extracted tools:', tools);

    // Map enabled tools - check both instructions.tools and wizardData.tools
    const toolsFromInstructions = instructions?.tools || [];
    const toolsFromWizard = wizardData.tools || {};
    const enabledTools = toolsFromInstructions.length > 0
      ? toolsFromInstructions.map(tool => tool.name)
      : Object.keys(toolsFromWizard).filter(key => toolsFromWizard[key]?.enabled);

    console.log('enabledTools computed as:', enabledTools);

    const updateData = {
      name: persona?.agentName || agent?.name,
      description: agent?.description || `Updated agent configuration`,
      personality_traits: persona?.traits || [], // Include the actual traits array
      personality_style: persona?.traits?.includes('professional') ? 'professional' :
                        persona?.traits?.includes('friendly') ? 'friendly' :
                        persona?.traits?.includes('enthusiastic') ? 'enthusiastic' :
                        persona?.traits?.includes('Professional') ? 'professional' :
                        persona?.traits?.includes('Friendly') ? 'friendly' :
                        persona?.traits?.includes('Enthusiastic') ? 'enthusiastic' : 'professional',
      response_length: persona?.communicationMode === 'voice' ? 'brief' : 'moderate',
      prompt_template: instructions?.systemPrompt || agent?.prompt_template,
      custom_personality_instructions: persona?.additionalInstructions || '',
      model: agent?.model || 'gpt-3.5-turbo',
      temperature: agent?.temperature || '0.7',
      max_tokens: agent?.max_tokens || 500,
      enabled_tools: enabledTools,
      conversation_settings: {
        voice_enabled: persona?.communicationMode === 'voice' || persona?.communicationMode === 'both',
        text_enabled: persona?.communicationMode === 'text' || persona?.communicationMode === 'both',
        response_time: 'normal',
        language: 'en'
      },
      // Knowledge and business data
      knowledge: [
        ...(businessProfile ? [{
          type: 'business_profile',
          content: businessProfile,
          name: 'Business Profile'
        }] : []),
        ...(faq && faq.length > 0 ? [{
          type: 'faq',
          content: faq,
          name: 'FAQ'
        }] : [])
      ]
    };

    console.log('Final update data being returned:', updateData);
    console.log('=======================================');

    return updateData;
  };

  const renderTabContent = () => {
    if (activeTab === 'test') {
      return (
        <div className="space-y-6">
          <div className="text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Test Your Agent</h3>
            <p className="text-gray-600">Send a message to test how your agent responds using OpenAI</p>
          </div>

          <div className="max-w-4xl mx-auto">
            {/* Chat History */}
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm mb-4" style={{ minHeight: '400px', maxHeight: '600px' }}>
              <div className="flex items-center justify-between p-4 border-b border-gray-200">
                <h4 className="font-medium text-gray-900">Chat Conversation</h4>
                {chatHistory.length > 0 && (
                  <button
                    onClick={clearChatHistory}
                    className="text-sm text-gray-500 hover:text-gray-700"
                  >
                    Clear History
                  </button>
                )}
              </div>

              <div className="p-4 overflow-y-auto" style={{ maxHeight: '500px' }}>
                {chatHistory.length === 0 ? (
                  <div className="text-center text-gray-500 py-8">
                    <p>Start a conversation to test your agent</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {chatHistory.map((entry, index) => (
                      <div key={index} className={`flex ${entry.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                          entry.type === 'user'
                            ? 'bg-blue-600 text-white ml-auto'
                            : entry.type === 'error'
                            ? 'bg-red-100 text-red-800 border border-red-200'
                            : 'bg-gray-100 text-gray-900'
                        }`}>
                          <p className="text-sm whitespace-pre-wrap">{entry.message}</p>
                          <div className="flex items-center justify-between mt-2">
                            <span className="text-xs opacity-75">
                              {entry.timestamp.toLocaleTimeString()}
                            </span>
                            {entry.usage && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 ml-2">
                                OpenAI - {entry.usage.total_tokens} tokens
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                    {testing && (
                      <div className="flex justify-start">
                        <div className="bg-gray-100 text-gray-900 max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
                          <div className="flex items-center space-x-2">
                            <svg className="animate-spin h-4 w-4 text-gray-600" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <span className="text-sm">Agent is thinking...</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Message Input */}
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Type your message</label>
                <div className="flex space-x-2">
                  <textarea
                    value={testMessage}
                    onChange={(e) => setTestMessage(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleTestAgent();
                      }
                    }}
                    placeholder="Type a message to test the agent..."
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    rows="2"
                  />
                  <button
                    onClick={handleTestAgent}
                    disabled={!testMessage.trim() || testing}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {testing ? (
                      <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    ) : (
                      'Send'
                    )}
                  </button>
                </div>
              </div>
              <p className="text-xs text-gray-500">Press Enter to send, Shift+Enter for new line</p>
            </div>
          </div>
        </div>
      );
    }

    const tab = configTabs.find(t => t.id === activeTab);
    if (tab && tab.component) {
      const TabComponent = tab.component;
      return <TabComponent />;
    }
    return null;
  };

  if (loadingAgent) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="ml-2 text-gray-600">Loading agent data...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-500 to-blue-600 rounded-2xl mb-4 shadow-lg">
          <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        </div>
        <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent mb-3">
          Edit AI Agent
        </h1>
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 max-w-3xl mx-auto">
          <div className="flex items-center justify-center space-x-8">
            <div className="text-center">
              <div className="text-2xl mb-1">🤖</div>
              <div className="text-sm font-medium text-gray-900">{agent?.name}</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-600">Agent Type</div>
              <div className="text-sm font-medium text-gray-900 capitalize">{agent?.type?.replace('_', ' ')}</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-600">Use Case</div>
              <div className="text-sm font-medium text-gray-900 capitalize">{agent?.use_case?.replace('_', ' ')}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <Card className="mb-8 border-0 shadow-lg bg-white">
        <div className="p-6">
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
            {configTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 py-3 px-4 rounded-md text-sm font-medium transition-all duration-200 ${
                  activeTab === tab.id
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab.title}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Tab Content */}
      <Card className="border-0 shadow-xl bg-white">
        <div className="p-8">
          {renderTabContent()}
        </div>
      </Card>

      {/* Error Display */}
      {errors.deploy && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-red-800 font-medium">Update Error:</span>
          </div>
          <p className="text-red-700 mt-1">{errors.deploy}</p>
        </div>
      )}

      {/* Action Bar */}
      <div className="flex justify-between items-center bg-gray-50 rounded-2xl p-6 border border-gray-100 mt-8">
        <div className="text-sm text-gray-600">
          Modify your agent settings using the tabs above
        </div>

        <div className="flex space-x-4">
          <button
            onClick={() => navigate('/agents')}
            disabled={isLoading}
            className="px-6 py-3 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleUpdate}
            disabled={isLoading}
            className="px-8 py-3 text-sm font-medium text-white bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg hover:from-blue-600 hover:to-blue-700 shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Updating...
              </>
            ) : (
              'Save Changes'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export function HatchAgentEdit() {
  return (
    <HatchWizardProvider>
      <HatchEditContent />
    </HatchWizardProvider>
  );
}