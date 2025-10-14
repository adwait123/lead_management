import React, { createContext, useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const HatchWizardContext = createContext();

export const useHatchWizard = () => {
  const context = useContext(HatchWizardContext);
  if (!context) {
    throw new Error('useHatchWizard must be used within a HatchWizardProvider');
  }
  return context;
};

export const HatchWizardProvider = ({ children }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [configStep, setConfigStep] = useState(1);

  // Load wizard data from localStorage if available
  const loadWizardDataFromStorage = () => {
    try {
      const storedWizardData = localStorage.getItem('wizardData');
      if (storedWizardData) {
        const parsedData = JSON.parse(storedWizardData);
        console.log('🔄 Loading wizard data from localStorage:', parsedData);
        return parsedData;
      }
    } catch (error) {
      console.error('❌ Error loading wizard data from localStorage:', error);
    }
    return null;
  };

  const [wizardData, setWizardData] = useState(() => {
    const storedData = loadWizardDataFromStorage();
    return storedData || {
    // Step 1: Agent Type
    agentType: null, // 'inbound', 'outbound', 'custom'

    // Step 2: Industry
    industry: null, // 'home_services', 'healthcare', etc.

    // Step 3: Use Case
    useCase: null, // 'speed_to_lead', 'appointment_confirmation', etc.
    selectedTemplate: null,

    // Agent Configuration (after template selection)
    businessProfile: {
      businessName: '',
      category: '',
      serviceArea: '',
      businessHours: '',
      servicesOffered: '',
      pricingInfo: '',
      emergencyPolicy: '',
      faqs: []
    },

    persona: {
      agentName: '',
      traits: [],
      communicationMode: 'both', // 'voice', 'text', 'both'
      additionalInstructions: ''
    },

    instructions: {
      systemPrompt: '',
      templateName: '',
      tools: [],
      workflows: []
    },

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
    },

    scheduling: {
      enabled: false,
      calendarSource: 'built_in',
      appointmentTypes: [],
      minimumNotice: '24_hours',
      maxAdvanceBooking: '1_month',
      businessHoursOnly: true,
      confirmations: {
        sendSMS: true,
        sendEmail: true,
        addToCalendar: true
      }
    },

    followUp: {
      retryAttempts: 3,
      retryDelay: '1_day',
      messageTemplate: '',
      finalAction: 'bailout'
    },

    // Workflow Configuration
    workflows: {
      triggers: {},
      followUps: {
        noResponse: {
          enabled: false,
          delayHours: 48,
          sequence: []
        },
        appointmentReminder: { enabled: false, hoursBefore: 24 },
        reEngagement: { enabled: false, delayDays: 7 }
      },
      leadFiltering: {
        mode: 'all', // 'all' or 'filtered'
        sources: []
      }
    },

    // Tool Configurations
    tools: {
      appointment: {
        enabled: false,
        configured: false,
        calendarIntegration: null,
        appointmentTypes: [],
        availabilityRules: {},
        confirmationMessages: {},
        testStatus: 'not_tested'
      },
      bailout: {
        enabled: false,
        configured: false,
        dispositions: [
          'Appointment set',
          'Bailout',
          'Discard',
          'Schedule follow-up',
          'Success/Completed',
          'Transfer'
        ],
        customDispositions: [],
        endMessages: {},
        crmMapping: {},
        testStatus: 'not_tested'
      },
      transfer: {
        enabled: false,
        configured: false,
        teams: [],
        transferMessages: {},
        availabilityRules: {},
        escalationRules: {},
        testStatus: 'not_tested'
      },
      knowledge: {
        enabled: false,
        configured: false,
        sources: [],
        searchLogic: {},
        presentationFormat: 'contextual',
        updateRules: {},
        testStatus: 'not_tested'
      }
    }
    };
  });

  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const updateWizardData = (updates) => {
    setWizardData(prev => ({
      ...prev,
      ...updates
    }));
  };

  const updateNestedData = (path, value) => {
    setWizardData(prev => {
      const keys = path.split('.');
      const newData = { ...prev };
      let current = newData;

      for (let i = 0; i < keys.length - 1; i++) {
        current[keys[i]] = { ...current[keys[i]] };
        current = current[keys[i]];
      }

      current[keys[keys.length - 1]] = value;
      return newData;
    });
  };

  const nextStep = () => {
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const goToStep = (step) => {
    if (step >= 1 && step <= 3) {
      setCurrentStep(step);
    }
  };

  // Transform Hatch wizard data to backend agent format
  const transformToAgentData = () => {
    const { persona, businessProfile, instructions, selectedTemplate, agentType, industry, faq, tools, workflows } = wizardData;
    console.log('=== TRANSFORMATION DEBUG ===');
    console.log('Extracted persona:', persona);
    console.log('Extracted businessProfile:', businessProfile);
    console.log('Extracted instructions:', instructions);
    console.log('Extracted selectedTemplate:', selectedTemplate);
    console.log('Extracted agentType:', agentType);
    console.log('Extracted industry:', industry);
    console.log('Extracted faq:', faq);
    console.log('Extracted tools from root:', tools);
    console.log('Extracted workflows:', workflows);

    // Build agent name - use persona name or template title as fallback
    const agentName = persona?.agentName || selectedTemplate?.title || 'Unnamed Agent';
    console.log('agentName computed as:', agentName);

    // Build description from business profile and template
    let description = '';
    if (businessProfile?.company_name) {
      description = `AI agent for ${businessProfile.company_name}`;
      if (businessProfile.service_area) {
        description += ` serving ${businessProfile.service_area}`;
      }
    } else if (selectedTemplate?.description) {
      description = selectedTemplate.description;
    } else {
      description = `${agentType} agent for ${industry?.replace('_', ' ')} industry`;
    }
    console.log('description computed as:', description);

    // Map personality style - check for lowercase trait names
    const personalityStyle = persona?.traits?.includes('professional') ? 'professional' :
                            persona?.traits?.includes('friendly') ? 'friendly' :
                            persona?.traits?.includes('enthusiastic') ? 'enthusiastic' :
                            persona?.traits?.includes('Professional') ? 'professional' :
                            persona?.traits?.includes('Friendly') ? 'friendly' :
                            persona?.traits?.includes('Enthusiastic') ? 'enthusiastic' :
                            'professional'; // default
    console.log('personalityStyle computed as:', personalityStyle);
    console.log('persona.traits array:', persona?.traits);

    // Determine response length based on communication style
    const responseLength = persona?.communicationMode === 'voice' ? 'brief' : 'moderate';
    console.log('responseLength computed as:', responseLength);
    console.log('persona.communicationMode:', persona?.communicationMode);

    // Build prompt template from instructions or use template
    const promptTemplate = instructions?.systemPrompt ||
                          selectedTemplate?.promptTemplate ||
                          `You are ${agentName}, a helpful AI assistant. Be ${personalityStyle} and assist customers with their needs.`;
    console.log('promptTemplate computed as:', promptTemplate);

    // Map enabled tools - check both instructions.tools and wizardData.tools
    const toolsFromInstructions = instructions?.tools || [];
    const toolsFromWizard = wizardData.tools || {};
    const enabledTools = toolsFromInstructions.length > 0
      ? toolsFromInstructions.map(tool => tool.name)
      : Object.keys(toolsFromWizard).filter(key => toolsFromWizard[key]?.enabled);
    console.log('enabledTools computed as:', enabledTools);
    console.log('toolsFromInstructions:', toolsFromInstructions);
    console.log('toolsFromWizard:', toolsFromWizard);

    // Build conversation settings
    const conversationSettings = {
      voice_enabled: persona.communicationMode === 'voice' || persona.communicationMode === 'both',
      text_enabled: persona.communicationMode === 'text' || persona.communicationMode === 'both',
      response_time: 'normal',
      language: 'en'
    };

    // Build workflow triggers from user configuration
    const triggers = [];

    // Add immediate triggers based on user selection
    if (workflows?.triggers) {
      Object.entries(workflows.triggers).forEach(([triggerEvent, config]) => {
        if (config.enabled) {
          const trigger = {
            event: triggerEvent,
            condition: 'any'
          };

          // Add source filtering if enabled
          if (workflows.leadFiltering?.mode === 'filtered' && workflows.leadFiltering?.sources?.length > 0) {
            trigger.sources = workflows.leadFiltering.sources;
          }

          triggers.push(trigger);
        }
      });
    }

    // Add default triggers if none selected (fallback to original behavior)
    if (triggers.length === 0) {
      if (agentType === 'inbound') {
        triggers.push({ event: 'new_lead', condition: 'any' });
        triggers.push({ event: 'chat_initiated', condition: 'any' });
      }
      if (agentType === 'outbound') {
        triggers.push({ event: 'follow_up_due', condition: 'any' });
        triggers.push({ event: 'lead_status_change', condition: 'contacted' });
      }
    }

    // Build actions based on conversation rules
    const actions = [];
    if (wizardData.rules?.success?.action) {
      actions.push({
        type: 'update_lead_status',
        status: wizardData.rules.success.action,
        assignTo: wizardData.rules.success.assignTo
      });
    }

    // Build workflow steps for follow-up automation
    const workflowSteps = [];
    if (workflows?.followUps) {
      // No response follow-up sequence
      if (workflows.followUps.noResponse?.enabled) {
        if (workflows.followUps.noResponse.sequence && workflows.followUps.noResponse.sequence.length > 0) {
          // Use sequence configuration
          workflows.followUps.noResponse.sequence.forEach((step, index) => {
            // Convert time units to minutes for consistent backend processing
            let delayInMinutes;
            switch (step.unit) {
              case 'minutes':
                delayInMinutes = step.delay;
                break;
              case 'hours':
                delayInMinutes = step.delay * 60;
                break;
              case 'days':
                delayInMinutes = step.delay * 60 * 24;
                break;
              default:
                delayInMinutes = step.delay * 60; // default to hours
            }

            workflowSteps.push({
              id: `no_response_sequence_${index + 1}`,
              type: 'time_based_trigger',
              sequence_position: index + 1,
              trigger: {
                event: 'no_response',
                delay_minutes: delayInMinutes,
                original_delay: step.delay,
                original_unit: step.unit
              },
              action: {
                type: 'send_message',
                template: step.message || `Follow-up message ${index + 1}`,
                template_type: 'no_response_sequence'
              }
            });
          });
        } else {
          // Use legacy single follow-up configuration
          workflowSteps.push({
            id: 'no_response_followup',
            type: 'time_based_trigger',
            trigger: {
              event: 'no_response',
              delay_minutes: (workflows.followUps.noResponse.delayHours || 48) * 60
            },
            action: {
              type: 'send_message',
              template: 'followup_no_response',
              template_type: 'no_response_single'
            }
          });
        }
      }

      // Appointment reminder
      if (workflows.followUps.appointmentReminder?.enabled) {
        workflowSteps.push({
          id: 'appointment_reminder',
          type: 'time_based_trigger',
          trigger: {
            event: 'appointment_scheduled',
            delay_minutes: -workflows.followUps.appointmentReminder.hoursBefore * 60,
            original_delay: workflows.followUps.appointmentReminder.hoursBefore,
            original_unit: 'hours'
          },
          action: {
            type: 'send_message',
            template: 'appointment_reminder',
            template_type: 'appointment_reminder'
          }
        });
      }

      // Re-engagement sequence
      if (workflows.followUps.reEngagement?.enabled) {
        workflowSteps.push({
          id: 'reengagement_sequence',
          type: 'time_based_trigger',
          trigger: {
            event: 'lead_inactive',
            delay_minutes: workflows.followUps.reEngagement.delayDays * 60 * 24,
            original_delay: workflows.followUps.reEngagement.delayDays,
            original_unit: 'days'
          },
          action: {
            type: 'send_message',
            template: 'reengagement',
            template_type: 'reengagement'
          }
        });
      }
    }

    const finalAgentData = {
      // Basic Information
      name: agentName,
      description: description,
      type: agentType || 'conversational',
      use_case: selectedTemplate?.useCase || 'general_sales',

      // Personality & Prompt
      prompt_template: promptTemplate,
      prompt_template_name: selectedTemplate?.name || null,
      personality_traits: persona?.traits || [],
      personality_style: personalityStyle,
      response_length: responseLength,
      custom_personality_instructions: persona?.additionalInstructions || '',

      // Model settings - use sensible defaults
      model: 'gpt-3.5-turbo',
      temperature: '0.7',
      max_tokens: 500,

      // Configuration
      enabled_tools: enabledTools,
      tool_configs: {},
      conversation_settings: conversationSettings,

      // Workflow
      triggers: triggers,
      actions: actions,
      workflow_steps: workflowSteps,
      integrations: [],

      // Status
      is_active: true,
      is_public: false,
      created_by: 'user',

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
      ],
      sample_conversations: []
    };

    console.log('Final agent data being returned from transform:', finalAgentData);
    console.log('===============================');

    return finalAgentData;
  };

  // Deploy agent to backend
  const deployAgent = async () => {
    console.log('deployAgent called - starting deployment process');
    console.log('=== DEBUGGING FIELD SAVING ISSUE ===');
    console.log('Raw wizardData at deployment time:', JSON.stringify(wizardData, null, 2));
    console.log('wizardData.persona:', wizardData.persona);
    console.log('wizardData.businessProfile:', wizardData.businessProfile);
    console.log('wizardData.instructions:', wizardData.instructions);
    console.log('wizardData.selectedTemplate:', wizardData.selectedTemplate);
    console.log('wizardData.agentType:', wizardData.agentType);
    console.log('wizardData.industry:', wizardData.industry);
    console.log('wizardData.rules:', wizardData.rules);
    console.log('=====================================');

    setIsLoading(true);
    setErrors({});

    try {
      // Transform wizard data to agent format
      const agentData = transformToAgentData();
      console.log('Transformed agent data:', JSON.stringify(agentData, null, 2));

      // Validate required fields
      if (!agentData.name?.trim()) {
        throw new Error('Agent name is required');
      }
      if (!agentData.description?.trim()) {
        throw new Error('Agent description is required');
      }
      if (!agentData.prompt_template?.trim()) {
        throw new Error('Prompt template is required');
      }

      const apiUrl = 'https://lead-management-staging-backend.onrender.com';
      const deployUrl = `${apiUrl}/api/agents/`;
      console.log('Making deployment request to:', deployUrl);

      // Make API call to create agent
      const response = await fetch(deployUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(agentData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to deploy agent');
      }

      const createdAgent = await response.json();
      console.log('Agent deployed successfully:', createdAgent);

      // Success! Show confirmation and redirect to agents page
      alert(`🚀 Agent "${createdAgent.name}" deployed successfully! Your AI assistant is now live and ready to handle customer interactions.`);

      // Reset wizard and redirect to agents page
      resetWizard();

      // Navigate to agents page to see the new agent
      setTimeout(() => {
        if (typeof window !== 'undefined') {
          window.location.replace('/agents');
        }
      }, 2000);

      return createdAgent;

    } catch (error) {
      console.error('Error deploying agent:', error);
      setErrors({ deploy: error.message });
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const resetWizard = () => {
    setCurrentStep(1);
    setConfigStep(1);
    setWizardData({
      agentType: null,
      industry: null,
      useCase: null,
      selectedTemplate: null,
      businessProfile: {
        businessName: '',
        category: '',
        serviceArea: '',
        businessHours: '',
        servicesOffered: '',
        pricingInfo: '',
        emergencyPolicy: '',
        faqs: []
      },
      persona: {
        agentName: '',
        traits: [],
        communicationMode: 'both',
        additionalInstructions: ''
      },
      instructions: {
        systemPrompt: '',
        templateName: '',
        tools: [],
        workflows: []
      },
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
      },
      scheduling: {
        enabled: false,
        calendarSource: 'built_in',
        appointmentTypes: [],
        minimumNotice: '24_hours',
        maxAdvanceBooking: '1_month',
        businessHoursOnly: true,
        confirmations: {
          sendSMS: true,
          sendEmail: true,
          addToCalendar: true
        }
      },
      followUp: {
        retryAttempts: 3,
        retryDelay: '1_day',
        messageTemplate: '',
        finalAction: 'bailout'
      },

      // Workflow Configuration
      workflows: {
        triggers: {},
        followUps: {
          noResponse: {
            enabled: false,
            delayHours: 48,
            sequence: []
          },
          appointmentReminder: { enabled: false, hoursBefore: 24 },
          reEngagement: { enabled: false, delayDays: 7 }
        },
        leadFiltering: {
          mode: 'all',
          sources: []
        }
      },

      // Tool Configurations
      tools: {
        appointment: {
          enabled: false,
          configured: false,
          calendarIntegration: null,
          appointmentTypes: [],
          availabilityRules: {},
          confirmationMessages: {},
          testStatus: 'not_tested'
        },
        bailout: {
          enabled: false,
          configured: false,
          dispositions: [
            'Appointment set',
            'Bailout',
            'Discard',
            'Schedule follow-up',
            'Success/Completed',
            'Transfer'
          ],
          customDispositions: [],
          endMessages: {},
          crmMapping: {},
          testStatus: 'not_tested'
        },
        transfer: {
          enabled: false,
          configured: false,
          teams: [],
          transferMessages: {},
          availabilityRules: {},
          escalationRules: {},
          testStatus: 'not_tested'
        },
        knowledge: {
          enabled: false,
          configured: false,
          sources: [],
          searchLogic: {},
          presentationFormat: 'contextual',
          updateRules: {},
          testStatus: 'not_tested'
        }
      }
    });
    setErrors({});
  };

  const value = {
    currentStep,
    configStep,
    wizardData,
    isLoading,
    errors,
    setCurrentStep,
    setConfigStep,
    updateWizardData,
    updateNestedData,
    nextStep,
    prevStep,
    goToStep,
    resetWizard,
    setIsLoading,
    setErrors,
    deployAgent
  };

  return (
    <HatchWizardContext.Provider value={value}>
      {children}
    </HatchWizardContext.Provider>
  );
};