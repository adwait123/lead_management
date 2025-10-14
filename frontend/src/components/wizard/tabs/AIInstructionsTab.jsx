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
  const [isLoadingPrompt, setIsLoadingPrompt] = useState(false);
  const textareaRef = useRef(null);

  // Debug component mounting and wizard data (development only)
  if (process.env.NODE_ENV === 'development') {
    console.log(`🏗️ AIInstructionsTab mounted/updated`);
    console.log(`📊 Component wizard data:`, wizardData);
  }

  // Check for useCase in URL params or localStorage as fallback
  const urlParams = new URLSearchParams(window.location.search);
  const urlUseCase = urlParams.get('useCase');

  // Check multiple localStorage sources
  let storedUseCase = localStorage.getItem('useCase'); // Direct storage
  let storedTemplate = null;
  let storedWizardData = null;

  // Try to get from stored template
  try {
    const templateStr = localStorage.getItem('selectedTemplate');
    if (templateStr) {
      storedTemplate = JSON.parse(templateStr);
      if (!storedUseCase) storedUseCase = storedTemplate.id;
    }
  } catch (e) {
    console.log('Could not parse stored template');
  }

  // Try to get from stored wizard data
  try {
    const wizardStr = localStorage.getItem('wizardData');
    if (wizardStr) {
      storedWizardData = JSON.parse(wizardStr);
      if (!storedUseCase) storedUseCase = storedWizardData.useCase;
    }
  } catch (e) {
    console.log('Could not parse stored wizard data');
  }

  console.log(`🔍 Alternative useCase sources:`, {
    url: urlUseCase,
    localStorageUseCase: localStorage.getItem('useCase'),
    localStorageTemplate: storedTemplate?.id,
    localStorageWizardData: storedWizardData?.useCase
  });

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
      console.log(`🔍 Fetching template: ${templateId} for use case: ${useCase}`);

      // Use the same API URL pattern as rest of the application
      const url = `https://lead-management-staging-backend.onrender.com/api/prompt-templates/${templateId}`;
      console.log(`📡 API URL: ${url}`);

      const response = await fetch(url);
      console.log(`📊 Response status: ${response.status}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch template: ${response.status}`);
      }
      const template = await response.json();
      console.log(`✅ Template fetched successfully, length: ${template.prompt.length}`);
      return template.prompt;
    } catch (error) {
      console.error('❌ Error fetching prompt template:', error);
      // Fall back to original hardcoded prompt if API fails
      return null; // Return null to trigger fallback
    }
  };

  // Generate starter prompt with explicit useCase parameter
  const generateStarterPromptWithUseCase = async (useCase) => {
    console.log(`🚀 generateStarterPromptWithUseCase called with useCase: ${useCase}`);

    if (useCase) {
      console.log(`📋 Fetching API template for useCase: ${useCase}`);
      // Fetch from API based on use case
      const apiPrompt = await fetchPromptTemplate(useCase);
      if (apiPrompt) {
        console.log(`✅ Using API prompt, length: ${apiPrompt.length}`);
        return apiPrompt;
      } else {
        console.log(`⚠️ API prompt failed, falling back to hardcoded`);
      }
    } else {
      console.log(`⚠️ No useCase provided, using fallback`);
    }

    // Fallback to original logic if no use case or API fails
    const fallback = generateFallbackPrompt();
    console.log(`🔄 Using fallback prompt, length: ${fallback.length}`);
    return fallback;
  };

  // Generate starter prompt based on wizard data (legacy function for button)
  const generateStarterPrompt = async () => {
    const useCase = wizardData.useCase;
    return await generateStarterPromptWithUseCase(useCase);
  };

  // Generate outbound calling prompt template
  const generateOutboundPrompt = () => {
    const persona = wizardData.persona || {};
    const agentName = persona.agentName || '[Agent Name]';

    return `You are ${agentName}, the Torkin Home Services Assistant, an expert in helping potential clients schedule their Free In-Home Design Consultation. Your primary role is to validate the user's request, confirm appointment details, and secure a booking for a professional design consultant.

IMPORTANT: This is an outbound voice call. You are calling the customer who submitted a web form. Keep responses professional, confident, friendly, and persuasive. Use a clear, warm, and inviting tone suitable for a premium home services brand.

CRITICAL BEHAVIOR RULES:
- Be Proactive and Direct: Your goal is to move the user quickly and smoothly to a confirmed appointment
- Present Steps One at a Time: For any multi-step process, present information ONE step at a time
- Always Wait for User Confirmation: Never proceed without explicit verbal confirmation from the user
- REPEAT BACK UNCLEAR RESPONSES: If customer response seems unclear or contradictory, repeat what you heard: "I heard you say [X], is that correct?"
- CONFIRM BEFORE BOOKING: Always confirm appointment selection clearly: "Just to confirm, you chose [DATE] at [TIME], is that right?"
- CONFIRM EVERY NEW INFORMATION: After receiving ANY new information from the customer (address changes, project details, preferences), immediately confirm by repeating it back: "Got it, so that's [INFORMATION], is that correct?"
- SPELL OUT ALL NUMBERS: For ZIP codes, phone numbers, and addresses, spell out each digit individually. Say "six-two-seven-one" instead of "six thousand two hundred seventy-one"
- Be Crisp and Confident: Maintain an expert tone suitable for a high-quality service
- Keep Responses Suitable for Speech: Use conversational language with no special formatting
- Use Brand Language: Use terms like "Free In-Home Design Consultation," "design consultant," and "Torkin Home Services"

SALES & SCHEDULING WORKFLOW:
1. Opening and Lead Validation:
   Begin immediately: "Hi, this is ${agentName} from Torkin Home Services. I see you recently submitted a request on our website. Is that right, and do you still have a few minutes to confirm your appointment details?"
   WAIT for confirmation.

2. Information Confirmation:
   Confirm address: "Great. I have your consultation address as [ADDRESS]. Is that correct?"
   WAIT for confirmation. If customer provides corrections, immediately repeat back: "Got it, so the correct address is [NEW ADDRESS], is that right?"
   Confirm project: "And this consultation is for [PROJECT_TYPE]? That will help our consultant prepare."
   WAIT for confirmation. If customer provides new details, immediately repeat back: "Perfect, so this is for [NEW PROJECT_TYPE], correct?"

3. Appointment Scheduling:
   Present exactly TWO options initially: "Fantastic. We have a design consultant available to visit you on [DATE_1] at [TIME_1], or [DATE_2] at [TIME_2]. Which works better for you?"
   ONLY provide additional options if customer asks for more choices.
   WAIT for their selection. Immediately confirm their choice: "Perfect, so you've chosen [SELECTED_DATE] at [SELECTED_TIME], is that correct?"

4. Confirmation and Wrap-Up:
   Provide summary: "Excellent. I have secured your Free In-Home Design Consultation for [DAY], [DATE] at [TIME] at [ADDRESS]. Your consultant will be arriving with hundreds of samples."
   Conclude: "You'll receive a confirmation text message with all these details in the next 15-20 minutes. Is there anything else I can help you with today?"

EXCEPTION HANDLING:
- No Available Slots: "I apologize, those exact times didn't work. I can have our local scheduling manager call you back within the next hour to personally secure a time that works best. Would that be helpful?"
- User No Longer Interested: "I understand. Thank you for letting us know. If you change your mind, you can always reach us directly. We appreciate your time."
- Incorrect Information: "Not a problem, I can quickly update that. What is the correct [DETAIL]?" Continue from step 2.

Available tools:
- /appointment - Use when customer agrees to schedule consultation
- /bailout - Use when customer is no longer interested or wants to end the call
- /transfer: Sales Team - Use if customer wants to speak with someone else

Remember: You are representing a premium home services brand. Be confident, helpful, and focused on booking appointments while maintaining a warm, professional demeanor.`;
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
      const response = await fetch('https://lead-management-staging-backend.onrender.com/api/agents/generate-prompt', {
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

      const response = await fetch('https://lead-management-staging-backend.onrender.com/api/agents/generate-scenario-prompt', {
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
    console.log(`🔄 useEffect triggered - prompt: ${prompt ? 'exists' : 'empty'}, agentName: ${wizardData.persona?.agentName}, useCase: ${wizardData.useCase}`);

    try {
      const useCase = wizardData.useCase || wizardData.selectedTemplate?.id || urlUseCase || storedUseCase;
      console.log(`🎲 Resolved useCase: ${useCase}`);

      if (!prompt && (wizardData.persona?.agentName || useCase)) {
        console.log(`✅ Conditions met, loading prompt...`);
        const loadPrompt = async () => {
          setIsLoadingPrompt(true);
          try {
            // Check if this is an outbound voice agent
            if (wizardData.agentType === 'outbound' && wizardData.persona?.communicationMode === 'voice') {
              console.log(`🎯 Using outbound calling prompt template`);
              const outboundPrompt = generateOutboundPrompt();
              setPrompt(outboundPrompt);
              updateWizardData({ instructions: { ...wizardData.instructions, systemPrompt: outboundPrompt } });
            } else {
              console.log(`🎯 Using useCase for prompt generation: ${useCase}`);
              const starter = await generateStarterPromptWithUseCase(useCase);
              console.log(`📝 Setting prompt in state and wizard data...`);
              setPrompt(starter);
              updateWizardData({ instructions: { ...wizardData.instructions, systemPrompt: starter } });
            }
          } catch (error) {
            console.error('❌ Error in loadPrompt:', error);
            // Fallback to simple prompt on error
            const fallbackPrompt = generateFallbackPrompt();
            setPrompt(fallbackPrompt);
            updateWizardData({ instructions: { ...wizardData.instructions, systemPrompt: fallbackPrompt } });
          } finally {
            setIsLoadingPrompt(false);
          }
        };
        loadPrompt();
      } else {
        console.log(`❌ Conditions not met for loading prompt`);
      }
    } catch (error) {
      console.error('❌ Error in useEffect:', error);
    }
  }, [wizardData.persona?.agentName, wizardData.useCase, wizardData.selectedTemplate?.id, wizardData.agentType, wizardData.persona?.communicationMode]); // Watch both paths

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

  // Show loading spinner if loading prompt
  if (isLoadingPrompt) {
    return (
      <div className="space-y-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            AI Instructions
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Create the prompt that defines how your AI agent behaves. Use slash commands to add interactive tools.
          </p>
        </div>
        <div className="flex justify-center items-center py-12">
          <div className="flex items-center space-x-3">
            <svg className="animate-spin w-6 h-6 text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="text-gray-600">Loading prompt template...</span>
          </div>
        </div>
      </div>
    );
  }

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
            {wizardData.agentType === 'outbound' && wizardData.persona?.communicationMode === 'voice' && (
              <Button
                variant="outline"
                onClick={() => {
                  const outboundPrompt = generateOutboundPrompt();
                  handlePromptChange(outboundPrompt);
                }}
                className="text-orange-600 border-orange-200 hover:bg-orange-50"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
                Use Outbound Template
              </Button>
            )}
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

      {/* Advanced Voice Configuration (Outbound Only) */}
      {wizardData.agentType === 'outbound' && wizardData.persona?.communicationMode === 'voice' && (
        <Card className="border-0 shadow-lg bg-gradient-to-r from-orange-50 to-red-50">
          <CardHeader>
            <CardTitle className="flex items-center">
              <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center mr-3">
                <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              </div>
              Advanced Voice Configuration
              <span className="ml-2 px-2 py-1 bg-orange-200 text-orange-800 text-xs rounded-full">Preview</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

              {/* Call Flow Settings */}
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-900 mb-3">Call Flow & Timing</h3>

                <div className="bg-white rounded-lg p-4 border">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Call Duration
                  </label>
                  <select className="w-full p-2 border border-gray-300 rounded-md text-sm" disabled>
                    <option>15 minutes (Recommended)</option>
                    <option>10 minutes</option>
                    <option>20 minutes</option>
                    <option>30 minutes</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">Auto-end calls after this duration</p>
                </div>

                <div className="bg-white rounded-lg p-4 border">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Response Timeout
                  </label>
                  <div className="flex items-center space-x-2">
                    <input type="range" min="3" max="15" defaultValue="8" className="flex-1" disabled />
                    <span className="text-sm text-gray-600 w-12">8 sec</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Wait time before prompting customer</p>
                </div>

                <div className="bg-white rounded-lg p-4 border">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Retry Strategy
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input type="checkbox" defaultChecked disabled className="mr-2" />
                      <span className="text-sm">Auto-retry busy numbers (2 attempts)</span>
                    </label>
                    <label className="flex items-center">
                      <input type="checkbox" defaultChecked disabled className="mr-2" />
                      <span className="text-sm">Leave voicemail if no answer</span>
                    </label>
                    <label className="flex items-center">
                      <input type="checkbox" disabled className="mr-2" />
                      <span className="text-sm">Schedule callback for missed calls</span>
                    </label>
                  </div>
                </div>
              </div>

              {/* Advanced Voice Features */}
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-900 mb-3">Voice Intelligence</h3>

                <div className="bg-white rounded-lg p-4 border">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Sentiment Analysis
                  </label>
                  <select className="w-full p-2 border border-gray-300 rounded-md text-sm" disabled>
                    <option>Real-time sentiment detection</option>
                    <option>End-of-call analysis only</option>
                    <option>Disabled</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">Adjust tone based on customer mood</p>
                </div>

                <div className="bg-white rounded-lg p-4 border">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Interruption Handling
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input type="radio" name="interruption" defaultChecked disabled className="mr-2" />
                      <span className="text-sm">Allow polite interruptions</span>
                    </label>
                    <label className="flex items-center">
                      <input type="radio" name="interruption" disabled className="mr-2" />
                      <span className="text-sm">Finish speaking before responding</span>
                    </label>
                    <label className="flex items-center">
                      <input type="radio" name="interruption" disabled className="mr-2" />
                      <span className="text-sm">Immediate response to any sound</span>
                    </label>
                  </div>
                </div>

                <div className="bg-white rounded-lg p-4 border">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Background Noise Filtering
                  </label>
                  <select className="w-full p-2 border border-gray-300 rounded-md text-sm" disabled>
                    <option>Aggressive noise cancellation</option>
                    <option>Standard filtering</option>
                    <option>Minimal processing</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">Handle construction sites, traffic, etc.</p>
                </div>
              </div>

              {/* Call Routing & Escalation */}
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-900 mb-3">Smart Routing</h3>

                <div className="bg-white rounded-lg p-4 border">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Escalation Triggers
                  </label>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Customer asks for manager</span>
                      <select className="text-xs p-1 border rounded" disabled>
                        <option>Immediate transfer</option>
                        <option>Attempt resolution first</option>
                      </select>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">High-value lead detected</span>
                      <select className="text-xs p-1 border rounded" disabled>
                        <option>Flag for sales team</option>
                        <option>Immediate transfer</option>
                      </select>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Negative sentiment detected</span>
                      <select className="text-xs p-1 border rounded" disabled>
                        <option>Supervisor notification</option>
                        <option>Continue with care</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-lg p-4 border">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Time-based Routing
                  </label>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Business hours (9AM-5PM)</span>
                      <span className="text-xs text-green-600">Live agents available</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">After hours</span>
                      <span className="text-xs text-orange-600">AI-only mode</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Weekends</span>
                      <span className="text-xs text-blue-600">Emergency appointments</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Analytics & Reporting */}
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-900 mb-3">Analytics & Insights</h3>

                <div className="bg-white rounded-lg p-4 border">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Real-time Monitoring
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input type="checkbox" defaultChecked disabled className="mr-2" />
                      <span className="text-sm">Live call transcription</span>
                    </label>
                    <label className="flex items-center">
                      <input type="checkbox" defaultChecked disabled className="mr-2" />
                      <span className="text-sm">Keyword detection alerts</span>
                    </label>
                    <label className="flex items-center">
                      <input type="checkbox" disabled className="mr-2" />
                      <span className="text-sm">Supervisor whisper mode</span>
                    </label>
                    <label className="flex items-center">
                      <input type="checkbox" defaultChecked disabled className="mr-2" />
                      <span className="text-sm">Call recording & storage</span>
                    </label>
                  </div>
                </div>

                <div className="bg-white rounded-lg p-4 border">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Performance Metrics
                  </label>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2 bg-blue-50 rounded">
                      <div className="font-medium text-blue-900">Conversion Rate</div>
                      <div className="text-blue-700">24.3% this week</div>
                    </div>
                    <div className="p-2 bg-green-50 rounded">
                      <div className="font-medium text-green-900">Avg Call Duration</div>
                      <div className="text-green-700">4m 32s</div>
                    </div>
                    <div className="p-2 bg-purple-50 rounded">
                      <div className="font-medium text-purple-900">Connect Rate</div>
                      <div className="text-purple-700">68.9%</div>
                    </div>
                    <div className="p-2 bg-orange-50 rounded">
                      <div className="font-medium text-orange-900">Customer Satisfaction</div>
                      <div className="text-orange-700">4.2/5 ⭐</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Feature Notice */}
            <div className="mt-6 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h4 className="text-sm font-medium text-blue-900">Advanced Features Preview</h4>
                  <p className="text-sm text-blue-800 mt-1">
                    These advanced voice configurations showcase the full potential of AI-powered outbound calling.
                    Current demo includes basic calling functionality with working TTS/STT integration.
                  </p>
                  <div className="mt-2 text-xs text-blue-700">
                    <strong>Available Now:</strong> Voice calls, sentiment detection, call recording, basic routing<br/>
                    <strong>Coming Soon:</strong> Advanced analytics, supervisor tools, custom voice training
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

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