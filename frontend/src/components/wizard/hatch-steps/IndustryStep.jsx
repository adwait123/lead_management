import React from 'react';
import { useHatchWizard } from '../HatchWizardContext';
import { Card } from '../../ui/Card';

export function IndustryStep() {
  const { wizardData, updateWizardData } = useHatchWizard();

  const industries = [
    {
      id: 'home_services',
      title: 'Home Services',
      description: 'Plumbing, electrical, HVAC, landscaping, and general maintenance',
      icon: '🏠',
      examples: [
        'Plumbing repairs and installations',
        'Electrical work and troubleshooting',
        'HVAC maintenance and installation',
        'Landscaping and lawn care',
        'General home maintenance',
        'Roofing and gutter services'
      ],
      popular: true
    },
    {
      id: 'home_improvement',
      title: 'Home Improvement',
      description: 'Remodeling, construction, and home renovation projects',
      icon: '🔧',
      examples: [
        'Kitchen and bathroom remodeling',
        'Flooring installation',
        'Painting and interior design',
        'Deck and patio construction',
        'Windows and door replacement',
        'Home additions and renovations'
      ]
    },
    {
      id: 'healthcare',
      title: 'Healthcare',
      description: 'Medical practices, dental offices, and healthcare services',
      icon: '❤️',
      examples: [
        'Appointment scheduling',
        'Patient intake and screening',
        'Insurance verification',
        'Follow-up care coordination',
        'Prescription reminders',
        'Telehealth coordination'
      ]
    },
    {
      id: 'professional_services',
      title: 'Professional Services',
      description: 'Legal, accounting, consulting, and business services',
      icon: '💼',
      examples: [
        'Legal consultation scheduling',
        'Client intake and screening',
        'Document collection',
        'Appointment confirmations',
        'Service explanations',
        'Follow-up communications'
      ]
    },
    {
      id: 'automotive',
      title: 'Automotive',
      description: 'Auto repair, maintenance, and automotive services',
      icon: '🚗',
      examples: [
        'Service appointment scheduling',
        'Maintenance reminders',
        'Repair estimates',
        'Parts availability checks',
        'Warranty inquiries',
        'Vehicle pickup coordination'
      ]
    },
    {
      id: 'retail',
      title: 'Retail & E-commerce',
      description: 'Online stores, customer service, and retail support',
      icon: '🛍️',
      examples: [
        'Order status inquiries',
        'Product recommendations',
        'Return and exchange support',
        'Shipping information',
        'Customer support',
        'Inventory questions'
      ]
    }
  ];

  const handleIndustrySelect = (industryId) => {
    updateWizardData({ industry: industryId });
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Select Your Industry
        </h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Choose the industry that best matches your business. This helps us customize templates and workflows specifically for your needs.
        </p>
      </div>

      {/* Industry Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {industries.map((industry) => (
          <Card
            key={industry.id}
            className={`cursor-pointer transition-all duration-300 border-2 hover:shadow-lg relative ${
              wizardData.industry === industry.id
                ? 'border-blue-500 bg-blue-50 shadow-lg ring-4 ring-blue-100'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => handleIndustrySelect(industry.id)}
          >
            {/* Popular Badge */}
            {industry.popular && (
              <div className="absolute -top-2 -right-2 bg-green-500 text-white text-xs font-bold px-2 py-1 rounded-full">
                Popular
              </div>
            )}

            <div className="p-6">
              {/* Icon and Title */}
              <div className="text-center mb-4">
                <div className="text-4xl mb-3">{industry.icon}</div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">
                  {industry.title}
                </h3>
                <p className="text-sm text-gray-600">
                  {industry.description}
                </p>
              </div>

              {/* Examples */}
              <div className="space-y-2">
                <p className="text-xs font-medium text-gray-900 mb-2">
                  Common use cases:
                </p>
                <div className="space-y-1">
                  {industry.examples.slice(0, 4).map((example, index) => (
                    <div key={index} className="flex items-start">
                      <div className="flex-shrink-0 w-3 h-3 mt-1">
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full"></div>
                      </div>
                      <span className="ml-2 text-xs text-gray-600">
                        {example}
                      </span>
                    </div>
                  ))}
                  {industry.examples.length > 4 && (
                    <div className="flex items-start">
                      <div className="flex-shrink-0 w-3 h-3 mt-1">
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full"></div>
                      </div>
                      <span className="ml-2 text-xs text-gray-500">
                        +{industry.examples.length - 4} more
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Selection Indicator */}
              {wizardData.industry === industry.id && (
                <div className="mt-4 flex items-center justify-center">
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

      {/* Additional Info */}
      <div className="bg-yellow-50 rounded-lg p-6">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-lg font-medium text-yellow-900 mb-2">
              Don't see your industry?
            </h3>
            <p className="text-yellow-800">
              Choose the closest match for now. You can fully customize your agent's behavior, prompts, and workflows in the next steps to fit your specific business needs.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}