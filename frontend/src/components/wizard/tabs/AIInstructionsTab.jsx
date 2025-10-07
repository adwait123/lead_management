import React, { useState, useRef, useEffect } from 'react';
import { useHatchWizard } from '../HatchWizardContext';
import { Card, CardHeader, CardTitle, CardContent } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { AppointmentConfigModal } from '../../modals/AppointmentConfigModal';
import { BailoutConfigModal } from '../../modals/BailoutConfigModal';
import { TransferConfigModal } from '../../modals/TransferConfigModal';
import { KnowledgeConfigModal } from '../../modals/KnowledgeConfigModal';
import { AgentTestingModal } from '../../modals/AgentTestingModal';

export function AIInstructionsTab() {
  const { wizardData, updateWizardData } = useHatchWizard();
  const [prompt, setPrompt] = useState(wizardData.instructions?.systemPrompt || '');
  const [showCalendarModal, setShowCalendarModal] = useState(false);
  const [activeConfigModal, setActiveConfigModal] = useState(null);
  const [showTestingModal, setShowTestingModal] = useState(false);
  const [showPromptGenerator, setShowPromptGenerator] = useState(false);
  const [promptGenerationMode, setPromptGenerationMode] = useState('summary'); // 'summary' or 'scenario'
  const [generationInput, setGenerationInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const textareaRef = useRef(null);

  // Get tool configurations from wizard data
  const toolConfigs = wizardData.tools || {};

  // Available slash commands with configuration status
  const slashCommands = [
    {
      command: '/appointment',
      label: 'Book Appointment',
      description: 'Schedule customer appointments',
      color: 'bg-blue-100 text-blue-800',
      usage: '/appointment',
      configurable: true,
      configured: toolConfigs.appointment?.configured || false,
      testStatus: toolConfigs.appointment?.testStatus || 'not_tested'
    },
    {
      command: '/bailout',
      label: 'End Conversation',
      description: 'Politely end the call',
      color: 'bg-red-100 text-red-800',
      usage: '/bailout',
      configurable: true,
      configured: toolConfigs.bailout?.configured || false,
      testStatus: toolConfigs.bailout?.testStatus || 'not_tested'
    },
    {
      command: '/transfer',
      label: 'Transfer Call',
      description: 'Hand off to human agent',
      color: 'bg-purple-100 text-purple-800',
      usage: '/transfer: Sales Team',
      configurable: true,
      configured: toolConfigs.transfer?.configured || false,
      testStatus: toolConfigs.transfer?.testStatus || 'not_tested'
    },
    {
      command: '/knowledge',
      label: 'Reference Knowledge',
      description: 'Use business info/FAQs',
      color: 'bg-green-100 text-green-800',
      usage: '/knowledge: Business Profile',
      configurable: true,
      configured: toolConfigs.knowledge?.configured || false,
      testStatus: toolConfigs.knowledge?.testStatus || 'not_tested'
    }
  ];

  // Map use case to prompt template ID
  const getTemplateIdFromUseCase = (useCase) => {
    const mapping = {
      'speed_to_lead': 'lead_qualification',
      'appointment_confirmation': 'booking_scheduling',
      'appointment_reminders': 'booking_scheduling',
      'recurring_services': 'customer_support',
      'estimate_followup': 'follow_up_nurture',
      'join_membership': 'general_sales'
    };
    return mapping[useCase] || 'lead_qualification'; // Default to lead_qualification
  };

  // Fetch prompt template from API based on use case
  const fetchPromptTemplate = async (useCase) => {
    try {
      const templateId = getTemplateIdFromUseCase(useCase);
      // Use the same API URL pattern as rest of the application
      const response = await fetch(`https://lead-management-j828.onrender.com/api/prompt-templates/${templateId}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch template: ${response.status}`);
      }
      const template = await response.json();
      return template.prompt;
    } catch (error) {
      console.error('Error fetching prompt template:', error);
      // Fall back to original hardcoded prompt if API fails
      return null; // Return null to trigger fallback
    }
  };

  // Generate starter prompt based on wizard data (now fetches from API)
  const generateStarterPrompt = async () => {
    const useCase = wizardData.useCase;

    if (useCase) {
      // Fetch from API based on use case
      const apiPrompt = await fetchPromptTemplate(useCase);
      if (apiPrompt) {
        return apiPrompt;
      }
    }

    // Fallback to original logic if no use case or API fails
    return generateFallbackPrompt();
  };

  // Original hardcoded prompt generation as fallback
  const generateFallbackPrompt = () => {
    const persona = wizardData.persona || {};
    const hasBusinessInfo = Object.keys(wizardData.businessProfile || {}).some(key => wizardData.businessProfile[key]);
    const hasFaqs = (wizardData.faq || []).length > 0;

    let starterPrompt = `You are ${persona.agentName || '[Agent Name]'}, a customer service representative for `;

    if (hasBusinessInfo && wizardData.businessProfile?.company_name) {
      starterPrompt += `${wizardData.businessProfile.company_name}`;
    } else {
      starterPrompt += `[Company Name]`;
    }

    starterPrompt += `. Your goal is to quickly and accurately gather information from potential customers, qualify their needs, and guide them toward scheduling an appointment—all while providing a warm, human-like experience.\n\n`;

    if (persona.traits && persona.traits.length > 0) {
      const traitLabels = {
        professional: 'Professional',
        friendly: 'Friendly',
        helpful: 'Helpful',
        efficient: 'Efficient'
      };
      starterPrompt += `**Personality:** You are ${persona.traits.map(t => traitLabels[t]).join(', ').toLowerCase()}\n`;
    }

    if (persona.communicationMode) {
      const modeText = {
        voice: 'phone conversations only',
        text: 'text/chat only',
        both: 'all communication channels (voice and text)'
      };
      starterPrompt += `**Communication:** Handle ${modeText[persona.communicationMode] || 'customer interactions'}\n\n`;
    }

    if (hasBusinessInfo || hasFaqs) {
      starterPrompt += `**Available Tools:**\n`;
      if (hasBusinessInfo) {
        starterPrompt += `- /knowledge: Business Profile - Use company information, hours, services\n`;
      }
      if (hasFaqs) {
        starterPrompt += `- /knowledge: FAQ - Reference frequently asked questions\n`;
      }
      starterPrompt += `- /appointment - Book appointments when customer is ready\n`;
      starterPrompt += `- /transfer: Sales Team - Hand off qualified leads\n`;
      starterPrompt += `- /bailout - Politely end conversations when appropriate\n\n`;
    }

    starterPrompt += `**Guidelines:**\n`;
    starterPrompt += `- Ask only one question at a time\n`;
    starterPrompt += `- If the customer wants to speak to a human, use /transfer: Sales Team\n`;
    starterPrompt += `- When ready to schedule, use /appointment\n`;
    starterPrompt += `- If customer is not interested after helping, use /bailout\n`;
    starterPrompt += `- Always stay in character and provide helpful responses\n\n`;

    starterPrompt += `**Example Conversation Flow:**\n`;
    starterPrompt += `1. Greet customer and ask how you can help\n`;
    starterPrompt += `2. Understand their specific needs\n`;
    starterPrompt += `3. Provide relevant information using /knowledge if needed\n`;
    starterPrompt += `4. When they're interested, guide them to /appointment\n`;
    starterPrompt += `5. If they need to speak with someone else, use /transfer: Sales Team`;

    return starterPrompt;
  };

  // Handle tool configuration
  const openToolConfig = (command) => {
    if (command.command === '/appointment') {
      setActiveConfigModal('appointment');
    } else if (command.command === '/bailout') {
      setActiveConfigModal('bailout');
    } else if (command.command === '/transfer') {
      setActiveConfigModal('transfer');
    } else if (command.command === '/knowledge') {
      setActiveConfigModal('knowledge');
    }
  };

  const handleToolConfigSave = (toolType, config) => {
    const updatedTools = {
      ...wizardData.tools,
      [toolType]: config
    };
    updateWizardData({ tools: updatedTools });
    setActiveConfigModal(null);
  };

  // Insert slash command at cursor position
  const insertSlashCommand = (command) => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = prompt;
    const before = text.substring(0, start);
    const after = text.substring(end);

    const newText = before + command.usage + after;
    setPrompt(newText);
    updateWizardData({ instructions: { ...wizardData.instructions, systemPrompt: newText } });

    // Set cursor position after inserted command
    setTimeout(() => {
      textarea.focus();
      const newCursorPos = start + command.usage.length;
      textarea.setSelectionRange(newCursorPos, newCursorPos);
    }, 0);
  };

  // Handle prompt changes
  const handlePromptChange = (value) => {
    setPrompt(value);
    updateWizardData({ instructions: { ...wizardData.instructions, systemPrompt: value } });
  };

  // Prompt generation functions
  const generatePromptFromSummary = async () => {
    if (!generationInput.trim()) return;

    setIsGenerating(true);
    try {
      const response = await fetch('https://lead-management-j828.onrender.com/api/agents/generate-prompt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          summary: generationInput,
          agent_type: wizardData?.agentType || 'customer_service',
          industry: wizardData?.industry || 'general',
          model: 'gpt-3.5-turbo'
        })
      });

      const data = await response.json();

      if (data.success && data.generated_prompt) {
        setPrompt(data.generated_prompt);
        updateWizardData({
          instructions: {
            ...wizardData.instructions,
            systemPrompt: data.generated_prompt
          }
        });
        setShowPromptGenerator(false);
        setGenerationInput('');
      } else {
        alert('Failed to generate prompt: ' + (data.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error generating prompt:', error);
      alert('Failed to generate prompt. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const generatePromptFromScenario = async () => {
    if (!generationInput.trim()) return;

    setIsGenerating(true);
    try {
      const businessContext = {
        name: wizardData?.businessProfile?.businessName || '',
        industry: wizardData?.industry || 'general',
        services: wizardData?.businessProfile?.servicesOffered || '',
        target_customers: 'General customers'
      };

      const response = await fetch('https://lead-management-j828.onrender.com/api/agents/generate-scenario-prompt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          scenario_description: generationInput,
          business_context: businessContext,
          model: 'gpt-3.5-turbo'
        })
      });

      const data = await response.json();

      if (data.success && data.generated_data?.system_prompt) {
        const generatedPrompt = data.generated_data.system_prompt;
        setPrompt(generatedPrompt);
        updateWizardData({
          instructions: {
            ...wizardData.instructions,
            systemPrompt: generatedPrompt
          }
        });

        // Optionally update other fields if available
        if (data.generated_data.personality_traits) {
          updateWizardData({
            persona: {
              ...wizardData.persona,
              traits: data.generated_data.personality_traits
            }
          });
        }

        if (data.generated_data.communication_mode) {
          updateWizardData({
            persona: {
              ...wizardData.persona,
              communicationMode: data.generated_data.communication_mode
            }
          });
        }

        setShowPromptGenerator(false);
        setGenerationInput('');
      } else {
        alert('Failed to generate prompt: ' + (data.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error generating scenario prompt:', error);
      alert('Failed to generate prompt. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGeneratePrompt = () => {
    if (promptGenerationMode === 'summary') {
      generatePromptFromSummary();
    } else {
      generatePromptFromScenario();
    }
  };

  // Load starter prompt if empty
  useEffect(() => {
    if (!prompt && wizardData.persona?.agentName) {
      const loadPrompt = async () => {
        const starter = await generateStarterPrompt();
        setPrompt(starter);
        updateWizardData({ instructions: { ...wizardData.instructions, systemPrompt: starter } });
      };
      loadPrompt();
    }
  }, [wizardData.persona?.agentName, wizardData.useCase]); // Add useCase as dependency

  // Render slash commands with special styling in the preview
  const renderPromptPreview = () => {
    if (!prompt) return null;

    const parts = prompt.split(/(\/)([a-zA-Z]+(?::\s*[^\n]*)?)/g);
    const rendered = [];

    for (let i = 0; i < parts.length; i++) {
      if (parts[i] === '/' && parts[i + 1]) {
        const command = parts[i + 1];
        const matchedCommand = slashCommands.find(cmd => command.startsWith(cmd.command.slice(1)));
        if (matchedCommand) {
          rendered.push(
            <span key={i} className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${matchedCommand.color} mr-1`}>
              /{command}
            </span>
          );
          i++; // Skip the next part since we consumed it
        } else {
          rendered.push(parts[i]);
        }
      } else if (parts[i] !== undefined && !parts[i - 1]?.endsWith('/')) {
        rendered.push(parts[i]);
      }
    }

    return rendered;
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          AI Instructions
        </h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Create the prompt that defines how your AI agent behaves. Use slash commands to add interactive tools.
        </p>
      </div>

      {/* Slash Commands Toolbar */}
      <Card className="border-0 shadow-lg bg-gradient-to-r from-purple-50 to-indigo-50">
        <CardHeader>
          <CardTitle className="flex items-center">
            <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center mr-3">
              <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </div>
            Available Tools & Commands
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600 mb-4">Configure tools and insert them into your prompt:</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {slashCommands.map((command) => (
              <div
                key={command.command}
                className="bg-white rounded-lg p-4 border border-gray-200 hover:border-purple-300 hover:shadow-md transition-all duration-200"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${command.color}`}>
                    {command.command}
                  </span>
                  <div className="flex items-center space-x-2">
                    {/* Configuration Status */}
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      command.configured
                        ? 'text-green-600 bg-green-100'
                        : 'text-yellow-600 bg-yellow-100'
                    }`}>
                      {command.configured ? 'Configured' : 'Not Configured'}
                    </span>
                    {/* Test Status */}
                    {command.configured && (
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        command.testStatus === 'passed' ? 'text-green-600 bg-green-100' :
                        command.testStatus === 'failed' ? 'text-red-600 bg-red-100' :
                        command.testStatus === 'testing' ? 'text-yellow-600 bg-yellow-100' :
                        'text-gray-600 bg-gray-100'
                      }`}>
                        {command.testStatus === 'passed' ? '✓ Tested' :
                         command.testStatus === 'failed' ? '✗ Failed' :
                         command.testStatus === 'testing' ? 'Testing...' :
                         'Not Tested'}
                      </span>
                    )}
                  </div>
                </div>
                <h4 className="font-medium text-gray-900 text-sm">{command.label}</h4>
                <p className="text-xs text-gray-600 mt-1 mb-3">{command.description}</p>

                {/* Action Buttons */}
                <div className="flex items-center space-x-2">
                  {command.configurable && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openToolConfig(command)}
                      className={`text-xs ${
                        command.configured
                          ? 'text-blue-600 border-blue-200 hover:bg-blue-50'
                          : 'text-orange-600 border-orange-200 hover:bg-orange-50'
                      }`}
                    >
                      {command.configured ? 'Edit Config' : 'Configure'}
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => insertSlashCommand(command)}
                    className="text-xs text-purple-600 border-purple-200 hover:bg-purple-50"
                  >
                    Insert
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Prompt Editor */}
      <Card className="border-0 shadow-lg">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </div>
            Agent Prompt
          </CardTitle>
          <div className="flex space-x-3">
            <Button
              variant="outline"
              onClick={() => setShowTestingModal(true)}
              className="text-green-600 border-green-200 hover:bg-green-50"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              Test Agent
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setPromptGenerationMode('summary');
                setShowPromptGenerator(true);
              }}
              className="text-blue-600 border-blue-200 hover:bg-blue-50"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Generate from Summary
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setPromptGenerationMode('scenario');
                setShowPromptGenerator(true);
              }}
              className="text-indigo-600 border-indigo-200 hover:bg-indigo-50"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              Create from Scenario
            </Button>
            <Button
              variant="outline"
              onClick={async () => {
                const starter = await generateStarterPrompt();
                handlePromptChange(starter);
              }}
              className="text-purple-600 border-purple-200 hover:bg-purple-50"
            >
              Generate Starter
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <textarea
              ref={textareaRef}
              value={prompt}
              onChange={(e) => handlePromptChange(e.target.value)}
              placeholder="Enter your AI agent instructions here. Use slash commands like /appointment, /transfer, /bailout to add interactive tools..."
              rows={20}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors font-mono text-sm"
            />

            {/* Prompt Stats */}
            <div className="flex justify-between items-center text-sm text-gray-500">
              <span>{prompt.length} characters</span>
              <span>{prompt.split('\n').length} lines</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Live Preview */}
      {prompt && (
        <Card className="border-0 shadow-lg bg-gradient-to-r from-gray-50 to-blue-50">
          <CardHeader>
            <CardTitle className="flex items-center">
              <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center mr-3">
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </div>
              Live Preview
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-white rounded-lg p-4 border max-h-96 overflow-y-auto">
              <div className="text-sm leading-relaxed whitespace-pre-wrap">
                {renderPromptPreview()}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tool Configuration Modals */}
      <AppointmentConfigModal
        isOpen={activeConfigModal === 'appointment'}
        onClose={() => setActiveConfigModal(null)}
        onSave={(config) => handleToolConfigSave('appointment', config)}
        config={toolConfigs.appointment}
        onConfigChange={() => {}}
      />

      <BailoutConfigModal
        isOpen={activeConfigModal === 'bailout'}
        onClose={() => setActiveConfigModal(null)}
        onSave={(config) => handleToolConfigSave('bailout', config)}
        config={toolConfigs.bailout}
        onConfigChange={() => {}}
      />

      <TransferConfigModal
        isOpen={activeConfigModal === 'transfer'}
        onClose={() => setActiveConfigModal(null)}
        onSave={(config) => handleToolConfigSave('transfer', config)}
        config={toolConfigs.transfer}
        onConfigChange={() => {}}
      />

      <KnowledgeConfigModal
        isOpen={activeConfigModal === 'knowledge'}
        onClose={() => setActiveConfigModal(null)}
        onSave={(config) => handleToolConfigSave('knowledge', config)}
        config={toolConfigs.knowledge}
        onConfigChange={() => {}}
      />

      <AgentTestingModal
        isOpen={showTestingModal}
        onClose={() => setShowTestingModal(false)}
        agentConfig={{
          prompt: prompt,
          tools: toolConfigs
        }}
        wizardData={wizardData}
      />

      {/* Prompt Generator Modal */}
      {showPromptGenerator && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-900">
                {promptGenerationMode === 'summary' ? 'Generate Prompt from Summary' : 'Create Prompt from Scenario'}
              </h3>
              <button
                onClick={() => {
                  setShowPromptGenerator(false);
                  setGenerationInput('');
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {promptGenerationMode === 'summary'
                      ? 'Brief Summary'
                      : 'Scenario Description'
                    }
                  </label>
                  <div className="text-sm text-gray-600 mb-3">
                    {promptGenerationMode === 'summary'
                      ? 'Provide a brief summary of what you want your AI agent to do. For example: "Handle customer inquiries for a plumbing company and book appointments"'
                      : 'Describe the specific scenario or use case. For example: "Customer calls asking about emergency plumbing services at 2 AM and needs immediate help"'
                    }
                  </div>
                  <textarea
                    value={generationInput}
                    onChange={(e) => setGenerationInput(e.target.value)}
                    placeholder={promptGenerationMode === 'summary'
                      ? 'Enter a brief summary of your agent\'s purpose...'
                      : 'Describe the specific scenario your agent should handle...'
                    }
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {promptGenerationMode === 'scenario' && (
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h4 className="text-sm font-medium text-blue-900 mb-2">Business Context</h4>
                    <div className="text-xs text-blue-700 space-y-1">
                      <div><strong>Business:</strong> {wizardData?.businessProfile?.businessName || 'Not specified'}</div>
                      <div><strong>Industry:</strong> {wizardData?.industry || 'General'}</div>
                      <div><strong>Services:</strong> {wizardData?.businessProfile?.servicesOffered || 'Not specified'}</div>
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between pt-4">
                  <div className="text-sm text-gray-500">
                    {generationInput.length} characters
                  </div>
                  <div className="flex space-x-3">
                    <Button
                      variant="outline"
                      onClick={() => {
                        setShowPromptGenerator(false);
                        setGenerationInput('');
                      }}
                      disabled={isGenerating}
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={handleGeneratePrompt}
                      disabled={!generationInput.trim() || isGenerating}
                      className="bg-blue-600 hover:bg-blue-700 text-white"
                    >
                      {isGenerating ? (
                        <>
                          <svg className="animate-spin w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Generating...
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                          Generate Prompt
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}