import React, { useState, useEffect } from 'react';
import { useHatchWizard } from '../HatchWizardContext';
import { Card } from '../../ui/Card';

export function UseCaseStep() {
  const { wizardData, updateWizardData } = useHatchWizard();
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);

  // Use case templates with embedded tools and workflows
  const useCaseTemplates = [
    {
      id: 'speed_to_lead',
      title: 'Speed to Lead',
      description: 'Engage new leads instantly from website, Angi, and other sources',
      icon: '⚡',
      category: 'Sales',
      workflow: [
        'Qualify homeowner status and property details',
        'Assess service urgency (emergency vs planned)',
        'Collect contact information',
        'Schedule estimate appointment',
        'Confirm appointment details'
      ],
      tools: ['Check_Calendar_Availability', 'Book_Appointment', 'Transfer', 'End_Success', 'End_Bailout'],
      outcomes: {
        success: 'Appointment scheduled for estimate',
        bailout: 'Emergency or complex issue requiring human',
        discard: 'Not homeowner or outside service area'
      },
      popular: true,
      sampleConversation: `Agent: Hi! I understand you're interested in our home services. I'd love to help you get the right technician scheduled. What type of service do you need?

Customer: I have a leak under my kitchen sink.

Agent: I'm sorry to hear about the leak! That definitely needs attention. Is this an active leak that's causing water damage right now, or is it a slow drip?

Customer: It's a slow drip, but it's been getting worse.

Agent: Got it. Let me check our availability for a plumbing repair visit. Are you the homeowner at the property where the work needs to be done?

Customer: Yes, I own the house.

Agent: Perfect! I have Tuesday at 2pm, Wednesday at 10am, or Thursday at 3pm available for an estimate. Which works best for you?`
    },
    {
      id: 'appointment_confirmation',
      title: 'Appointment Confirmations',
      description: 'Request customer to confirm their upcoming appointment',
      icon: '📅',
      category: 'Operations',
      workflow: [
        'Greet customer and state purpose',
        'Confirm appointment details',
        'Handle confirmation or reschedule requests',
        'Provide any preparation instructions',
        'Send updated confirmation if needed'
      ],
      tools: ['Check_Calendar_Availability', 'Reschedule_Appointment', 'Cancel_Appointment', 'End_Success'],
      outcomes: {
        success: 'Appointment confirmed or successfully rescheduled',
        bailout: 'Customer has questions requiring human assistance',
        discard: 'Appointment cancelled by customer'
      },
      sampleConversation: `Agent: Hi John, this is Sarah from Acme Home Services. I'm calling to confirm your plumbing repair appointment tomorrow at 2pm.

Customer: Yes, that works for me.

Agent: Great! Just to confirm, our technician will be coming to 123 Oak Street for the kitchen sink leak repair. Please make sure someone is home and that our technician can access the kitchen area.

Customer: Perfect, I'll be here.

Agent: Excellent! You'll receive a text when our technician is on the way. Is there anything else I can help you with?`
    },
    {
      id: 'appointment_reminders',
      title: 'Appointment Reminders',
      description: 'Remind customers about upcoming appointments',
      icon: '🔔',
      category: 'Operations',
      workflow: [
        'Confirm customer identity',
        'Remind about upcoming appointment',
        'Verify appointment details are correct',
        'Provide preparation instructions',
        'Handle any last-minute changes'
      ],
      tools: ['Check_Calendar_Availability', 'Reschedule_Appointment', 'End_Success', 'End_Bailout'],
      outcomes: {
        success: 'Customer confirmed and prepared for appointment',
        bailout: 'Customer needs to reschedule or has questions',
        discard: 'Customer no longer needs service'
      },
      sampleConversation: `Agent: Hi Lisa, this is a reminder that you have an HVAC maintenance appointment tomorrow at 10am with Acme Home Services.

Customer: Oh, I forgot about that! Can we reschedule?

Agent: Of course! Let me check our availability. I have Friday at 2pm, Monday at 9am, or Tuesday at 1pm. Which would work better for you?

Customer: Friday at 2pm would be perfect.

Agent: Great! I've rescheduled your appointment to Friday at 2pm. You'll receive a confirmation text shortly.`
    },
    {
      id: 'recurring_services',
      title: 'Recurring Services',
      description: 'Reach out to membership customers to schedule regular service',
      icon: '🔄',
      category: 'Customer Success',
      workflow: [
        'Reference customer service history',
        'Remind about scheduled maintenance',
        'Check customer satisfaction',
        'Schedule next service appointment',
        'Upsell additional services if appropriate'
      ],
      tools: ['Check_Calendar_Availability', 'Book_Appointment', 'Update_Service_Plan', 'End_Success'],
      outcomes: {
        success: 'Next service appointment scheduled',
        bailout: 'Customer wants to modify service plan',
        discard: 'Customer wants to cancel service plan'
      },
      sampleConversation: `Agent: Hi Bob, it's time for your quarterly HVAC maintenance as part of your service plan. How has your system been running since our last visit?

Customer: It's been working great, thanks!

Agent: Wonderful! I'd like to schedule your next maintenance visit. I have next Tuesday at 11am or Wednesday at 3pm available. Which works better for you?

Customer: Tuesday at 11am is perfect.

Agent: Excellent! I've scheduled your maintenance for Tuesday at 11am. Our technician will perform the full service checklist and let you know if anything needs attention.`
    },
    {
      id: 'estimate_followup',
      title: 'Estimate Follow-Up',
      description: 'Follow up directly on estimates you provided',
      icon: '📊',
      category: 'Sales',
      workflow: [
        'Reference specific estimate provided',
        'Ask about customer questions or concerns',
        'Address objections and provide clarification',
        'Offer to schedule work if approved',
        'Provide additional options if needed'
      ],
      tools: ['Check_Calendar_Availability', 'Book_Appointment', 'Transfer', 'End_Success', 'End_Bailout'],
      outcomes: {
        success: 'Work scheduled or customer needs more time',
        bailout: 'Complex questions requiring human expertise',
        discard: 'Customer decided not to proceed'
      },
      sampleConversation: `Agent: Hi Maria, I'm following up on the bathroom remodeling estimate we provided last week. Did you have a chance to review it?

Customer: Yes, but the price seems high. Can you explain what's included?

Agent: Absolutely! The estimate includes complete tile removal, new plumbing fixtures, electrical updates for code compliance, and a 2-year warranty on all work. Would you like me to break down any specific items?

Customer: The electrical work wasn't in the original scope we discussed.

Agent: You're right to ask about that. During our inspection, we found some outdated wiring that needs updating for safety and code compliance. Let me transfer you to our project manager who can discuss options for this.`
    },
    {
      id: 'join_membership',
      title: 'Join Membership',
      description: 'Promote membership program to current customers',
      icon: '👥',
      category: 'Customer Success',
      workflow: [
        'Reference customer service history',
        'Explain membership benefits and savings',
        'Calculate potential annual savings',
        'Address questions about the program',
        'Enroll customer or schedule follow-up'
      ],
      tools: ['Calculate_Savings', 'Enroll_Membership', 'Transfer', 'End_Success', 'End_Bailout'],
      outcomes: {
        success: 'Customer enrolled in membership program',
        bailout: 'Customer wants to speak with manager',
        discard: 'Customer not interested in membership'
      },
      sampleConversation: `Agent: Hi David, I noticed you've used our services twice this year for HVAC and plumbing. Our VIP membership could save you money on future services. Would you like to hear about it?

Customer: Sure, what kind of savings are we talking about?

Agent: Based on your service history, you'd save about $200 annually with our membership. You get priority scheduling, 15% off all services, and free annual maintenance. The membership is only $99 per year.

Customer: That does sound like a good deal. How do I sign up?

Agent: I can enroll you right now! I'll also schedule your complimentary annual maintenance visit. Would next month work for that?`
    }
  ];

  useEffect(() => {
    // Set templates based on selected industry
    const filteredTemplates = useCaseTemplates.filter(template => {
      if (wizardData.industry === 'home_services' || wizardData.industry === 'home_improvement') {
        return true; // All templates are relevant for home services
      }
      // For other industries, show the most generic templates
      return ['appointment_confirmation', 'appointment_reminders', 'speed_to_lead'].includes(template.id);
    });
    setTemplates(filteredTemplates);
  }, [wizardData.industry]);

  const handleTemplateSelect = (template) => {
    setSelectedTemplate(template);
    updateWizardData({
      useCase: template.id,
      selectedTemplate: template
    });
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Choose Your Use Case
        </h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Select a pre-built template that matches your primary goal. Each template includes optimized prompts, workflows, and conversation logic.
        </p>
      </div>

      {/* Template Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {templates.map((template) => (
          <Card
            key={template.id}
            className={`cursor-pointer transition-all duration-300 border-2 hover:shadow-lg relative ${
              wizardData.useCase === template.id
                ? 'border-blue-500 bg-blue-50 shadow-lg ring-4 ring-blue-100'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => handleTemplateSelect(template)}
          >
            {/* Popular Badge */}
            {template.popular && (
              <div className="absolute -top-2 -right-2 bg-green-500 text-white text-xs font-bold px-2 py-1 rounded-full">
                Most Popular
              </div>
            )}

            <div className="p-6">
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center">
                  <div className="text-3xl mr-3">{template.icon}</div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">
                      {template.title}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {template.description}
                    </p>
                  </div>
                </div>
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                  {template.category}
                </span>
              </div>

              {/* Workflow */}
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Conversation Flow:</h4>
                <ol className="space-y-1">
                  {template.workflow.slice(0, 3).map((step, index) => (
                    <li key={index} className="flex items-start text-xs text-gray-600">
                      <span className="flex-shrink-0 w-4 h-4 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-xs font-bold mr-2 mt-0.5">
                        {index + 1}
                      </span>
                      {step}
                    </li>
                  ))}
                  {template.workflow.length > 3 && (
                    <li className="text-xs text-gray-500 ml-6">
                      +{template.workflow.length - 3} more steps
                    </li>
                  )}
                </ol>
              </div>

              {/* Tools */}
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Built-in Tools:</h4>
                <div className="flex flex-wrap gap-1">
                  {template.tools.slice(0, 4).map((tool) => (
                    <span
                      key={tool}
                      className="inline-flex items-center px-2 py-1 rounded text-xs bg-green-100 text-green-800"
                    >
                      {tool.replace('_', ' ')}
                    </span>
                  ))}
                  {template.tools.length > 4 && (
                    <span className="text-xs text-gray-500">
                      +{template.tools.length - 4} more
                    </span>
                  )}
                </div>
              </div>

              {/* Outcomes */}
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Success Outcomes:</h4>
                <div className="space-y-1">
                  <div className="flex items-start text-xs">
                    <span className="w-2 h-2 bg-green-500 rounded-full mt-1.5 mr-2 flex-shrink-0"></span>
                    <span className="text-gray-600">{template.outcomes.success}</span>
                  </div>
                </div>
              </div>

              {/* Selection Indicator */}
              {wizardData.useCase === template.id && (
                <div className="flex items-center justify-center pt-4 border-t border-gray-200">
                  <div className="flex items-center text-blue-600">
                    <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    <span className="text-sm font-medium">Selected</span>
                  </div>
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>

      {/* Sample Conversation Preview */}
      {selectedTemplate && (
        <div className="bg-gray-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            📞 Sample Conversation Preview
          </h3>
          <div className="bg-white rounded-lg border p-4 max-h-64 overflow-y-auto">
            <div className="text-sm font-mono whitespace-pre-line text-gray-700">
              {selectedTemplate.sampleConversation}
            </div>
          </div>
          <p className="text-sm text-gray-600 mt-3">
            This is just a sample. Your agent will be customized based on your business profile and preferences in the next steps.
          </p>
        </div>
      )}

      {/* Next Steps Info */}
      <div className="bg-blue-50 rounded-lg p-6">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-lg font-medium text-blue-900 mb-2">
              What happens next?
            </h3>
            <p className="text-blue-800">
              After selecting a template, you'll configure your business profile, customize the agent's personality, set up scheduling, and test everything in our sandbox before going live.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}