import React from 'react';
import { useNavigate } from 'react-router-dom';
import { HatchWizardProvider, useHatchWizard } from './HatchWizardContext';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';

// Import step components
import { AgentTypeStep } from './hatch-steps/AgentTypeStep';
import { IndustryStep } from './hatch-steps/IndustryStep';
import { UseCaseStep } from './hatch-steps/UseCaseStep';

const steps = [
  { id: 1, title: 'Agent Type', description: 'Inbound, outbound, or custom' },
  { id: 2, title: 'Industry', description: 'Your business category' },
  { id: 3, title: 'Use Case', description: 'Pre-built templates' }
];

function HatchWizardContent() {
  const { currentStep, wizardData, nextStep, prevStep, isLoading } = useHatchWizard();
  const navigate = useNavigate();

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return <AgentTypeStep />;
      case 2:
        return <IndustryStep />;
      case 3:
        return <UseCaseStep />;
      default:
        return <AgentTypeStep />;
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return wizardData.agentType;
      case 2:
        return wizardData.industry;
      case 3:
        return wizardData.useCase;
      default:
        return false;
    }
  };

  const isFirstStep = currentStep === 1;
  const isLastStep = currentStep === 3;

  const handleNext = () => {
    if (canProceed()) {
      if (isLastStep) {
        // Move to configuration phase
        handleTemplateComplete();
      } else {
        nextStep();
      }
    }
  };

  const handleTemplateComplete = () => {
    // This will transition to the configuration phase
    console.log('Template selection complete:', wizardData);
    // Navigate to configuration page
    navigate('/agents/config');
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-2xl mb-4 shadow-lg">
          <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
          </svg>
        </div>
        <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent mb-3">
          Create Your AI Agent
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Get started in just 3 simple steps. Choose your agent type, industry, and use case to create a powerful AI assistant.
        </p>
      </div>

      {/* Progress Stepper */}
      <Card className="mb-8 border-0 shadow-lg bg-gradient-to-r from-white to-gray-50">
        <div className="p-6">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center">
                {/* Step Circle */}
                <div
                  className={`flex items-center justify-center w-12 h-12 rounded-full transition-all duration-300 shadow-sm border-2 ${
                    currentStep === step.id
                      ? 'bg-gradient-to-r from-purple-500 to-indigo-600 text-white shadow-purple-200 border-purple-600 ring-4 ring-purple-100 scale-110'
                      : currentStep > step.id
                      ? 'bg-gradient-to-r from-green-500 to-green-600 text-white shadow-green-200 border-green-600'
                      : 'bg-white text-gray-600 border-gray-300'
                  }`}
                >
                  {currentStep > step.id ? (
                    <svg className="w-6 h-6 animate-in zoom-in-50 duration-300" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <span className="text-sm font-bold">{step.id}</span>
                  )}
                </div>

                {/* Step Info */}
                <div className="ml-4 flex-1">
                  <div className={`text-sm font-semibold transition-colors duration-200 ${
                    currentStep === step.id ? 'text-purple-600' : currentStep > step.id ? 'text-green-600' : 'text-gray-700'
                  }`}>
                    {step.title}
                  </div>
                  <div className={`text-xs transition-colors duration-200 ${
                    currentStep >= step.id ? 'text-gray-600' : 'text-gray-500'
                  }`}>
                    {step.description}
                  </div>
                </div>

                {/* Connector Line */}
                {index < steps.length - 1 && (
                  <div className={`flex-1 h-1 mx-6 rounded-full transition-all duration-500 ${
                    currentStep > step.id
                      ? 'bg-gradient-to-r from-green-400 to-green-500 shadow-sm'
                      : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>

          {/* Progress Bar */}
          <div className="mt-6">
            <div className="flex justify-between text-sm font-medium mb-2">
              <span className="text-gray-700">Setup Progress</span>
              <span className="text-purple-600">{Math.round((currentStep / steps.length) * 100)}% Complete</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 shadow-inner">
              <div
                className="bg-gradient-to-r from-purple-500 via-purple-600 to-indigo-600 h-2 rounded-full transition-all duration-700 ease-out shadow-sm"
                style={{ width: `${(currentStep / steps.length) * 100}%` }}
              />
            </div>
          </div>
        </div>
      </Card>

      {/* Step Content */}
      <Card className="mb-8 border-0 shadow-xl bg-white">
        <div className="p-8">
          {renderStep()}
        </div>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between items-center bg-gray-50 rounded-2xl p-6 border border-gray-100">
        <Button
          variant="outline"
          onClick={prevStep}
          disabled={isFirstStep || isLoading}
          className="px-8 py-3 text-sm font-medium border-gray-300 hover:border-gray-400 hover:bg-gray-100 transition-all duration-200"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Previous
        </Button>

        <div className="flex items-center bg-white px-4 py-2 rounded-full border shadow-sm">
          <span className="text-sm font-medium text-gray-700">
            Step {currentStep} of {steps.length}
          </span>
        </div>

        <Button
          onClick={handleNext}
          disabled={!canProceed() || isLoading}
          className={`px-8 py-3 text-sm font-medium shadow-lg hover:shadow-xl transition-all duration-300 ${
            isLastStep
              ? 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700'
              : 'bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700'
          }`}
        >
          {isLoading ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Loading...
            </>
          ) : (
            <>
              {isLastStep ? 'Configure Agent' : 'Next'}
              <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isLastStep ? "M5 13l4 4L19 7" : "M9 5l7 7-7 7"} />
              </svg>
            </>
          )}
        </Button>
      </div>

      {/* Selection Summary (when steps are completed) */}
      {wizardData.agentType && wizardData.industry && wizardData.useCase && (
        <Card className="mt-8 border-0 shadow-lg bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              📋 Your Selection Summary
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white rounded-lg p-4">
                <h4 className="font-medium text-gray-900">Agent Type</h4>
                <p className="text-sm text-gray-600 capitalize">
                  {wizardData.agentType?.replace('_', ' ')}
                </p>
              </div>
              <div className="bg-white rounded-lg p-4">
                <h4 className="font-medium text-gray-900">Industry</h4>
                <p className="text-sm text-gray-600 capitalize">
                  {wizardData.industry?.replace('_', ' ')}
                </p>
              </div>
              <div className="bg-white rounded-lg p-4">
                <h4 className="font-medium text-gray-900">Use Case</h4>
                <p className="text-sm text-gray-600">
                  {wizardData.selectedTemplate?.title}
                </p>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

export function HatchAgentWizard() {
  return (
    <HatchWizardProvider>
      <HatchWizardContent />
    </HatchWizardProvider>
  );
}