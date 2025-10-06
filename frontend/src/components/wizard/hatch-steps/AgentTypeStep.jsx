import React from 'react';
import { useHatchWizard } from '../HatchWizardContext';
import { Card } from '../../ui/Card';

export function AgentTypeStep() {
  const { wizardData, updateWizardData } = useHatchWizard();

  const agentTypes = [
    {
      id: 'inbound',
      title: 'Inbound Calls',
      description: 'Handle incoming customer calls and inquiries',
      icon: '📞',
      features: [
        'Answer incoming calls automatically',
        'Qualify leads from phone inquiries',
        'Schedule appointments and consultations',
        'Transfer to human agents when needed'
      ],
      bestFor: 'Businesses receiving regular customer calls'
    },
    {
      id: 'outbound',
      title: 'Outbound Campaigns',
      description: 'Proactive outreach to leads and customers',
      icon: '📢',
      features: [
        'Follow up with existing leads',
        'Appointment confirmations and reminders',
        'Customer satisfaction surveys',
        'Re-engagement campaigns'
      ],
      bestFor: 'Following up with leads and existing customers'
    },
    {
      id: 'custom',
      title: 'Create from Scratch',
      description: 'Build a custom agent for specific needs',
      icon: '🛠️',
      features: [
        'Fully customizable behavior',
        'Tailored conversation flows',
        'Custom integrations',
        'Advanced configuration options'
      ],
      bestFor: 'Unique use cases requiring custom solutions'
    }
  ];

  const handleTypeSelect = (typeId) => {
    updateWizardData({ agentType: typeId });
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Choose Your Agent Type
        </h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Select the type of AI agent that best fits your business needs. You can always create more agents later.
        </p>
      </div>

      {/* Agent Type Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {agentTypes.map((type) => (
          <Card
            key={type.id}
            className={`cursor-pointer transition-all duration-300 border-2 hover:shadow-xl ${
              wizardData.agentType === type.id
                ? 'border-blue-500 bg-blue-50 shadow-lg ring-4 ring-blue-100'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => handleTypeSelect(type.id)}
          >
            <div className="p-8">
              {/* Icon and Title */}
              <div className="text-center mb-6">
                <div className="text-6xl mb-4">{type.icon}</div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  {type.title}
                </h3>
                <p className="text-gray-600">
                  {type.description}
                </p>
              </div>

              {/* Features */}
              <div className="space-y-3 mb-6">
                {type.features.map((feature, index) => (
                  <div key={index} className="flex items-start">
                    <div className="flex-shrink-0 w-5 h-5 mt-0.5">
                      <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <span className="ml-3 text-sm text-gray-700">
                      {feature}
                    </span>
                  </div>
                ))}
              </div>

              {/* Best For */}
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm font-medium text-gray-900 mb-1">
                  Best for:
                </p>
                <p className="text-sm text-gray-600">
                  {type.bestFor}
                </p>
              </div>

              {/* Selection Indicator */}
              {wizardData.agentType === type.id && (
                <div className="mt-4 flex items-center justify-center">
                  <div className="flex items-center text-blue-600">
                    <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    <span className="font-medium">Selected</span>
                  </div>
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>

      {/* Additional Info */}
      <div className="bg-blue-50 rounded-lg p-6">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-lg font-medium text-blue-900 mb-2">
              💡 Pro Tip
            </h3>
            <p className="text-blue-800">
              Start with "Inbound Calls" if you're new to AI agents. It's the most popular choice and works great for most home service businesses. You can always create additional agents for outbound campaigns later.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}