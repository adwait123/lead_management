import React, { useState } from 'react';
import { HatchWizardProvider, useHatchWizard } from './HatchWizardContext';
import { Card } from '../ui/Card';

// Import tab components
import { AgentBasicsTab } from './tabs/AgentBasicsTab';
import { KnowledgeBaseTab } from './tabs/KnowledgeBaseTab';
import { AIInstructionsTab } from './tabs/AIInstructionsTab';
import { WorkflowConfigTab } from './tabs/WorkflowConfigTab';

const configTabs = [
  { id: 'basics', title: 'Agent Basics', component: AgentBasicsTab },
  { id: 'knowledge', title: 'Knowledge', component: KnowledgeBaseTab },
  { id: 'instructions', title: 'AI Instructions', component: AIInstructionsTab },
  { id: 'workflows', title: 'Workflows & Triggers', component: WorkflowConfigTab }
];

function HatchConfigSimpleContent() {
  const { wizardData, deployAgent, isLoading, errors } = useHatchWizard();
  const [activeTab, setActiveTab] = useState('basics');
  const [showPreview, setShowPreview] = useState(false);

  const renderTabContent = () => {
    const tab = configTabs.find(t => t.id === activeTab);
    if (tab && tab.component) {
      const TabComponent = tab.component;
      return <TabComponent />;
    }
    return null;
  };

  const renderWorkflowPreview = () => {
    const { workflows } = wizardData;
    if (!workflows) return null;

    const enabledTriggers = Object.entries(workflows.triggers || {})
      .filter(([_, config]) => config.enabled)
      .map(([event, _]) => event);

    const enabledFollowUps = Object.entries(workflows.followUps || {})
      .filter(([_, config]) => config.enabled)
      .map(([type, config]) => ({ type, config }));

    return (
      <div className="space-y-4">
        <h4 className="font-semibold text-gray-900">Workflow Configuration</h4>

        {/* Triggers */}
        {enabledTriggers.length > 0 && (
          <div>
            <h5 className="font-medium text-gray-700 mb-2">Active Triggers:</h5>
            <div className="flex flex-wrap gap-2">
              {enabledTriggers.map(trigger => (
                <span key={trigger} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                  {trigger.replace('_', ' ')}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Follow-ups */}
        {enabledFollowUps.length > 0 && (
          <div>
            <h5 className="font-medium text-gray-700 mb-2">Follow-up Automation:</h5>
            <div className="space-y-2">
              {enabledFollowUps.map(({ type, config }) => (
                <div key={type} className="p-2 bg-gray-50 rounded">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-700 capitalize">{type.replace(/([A-Z])/g, ' $1')}</span>
                    <span className="text-sm text-gray-600">
                      {type === 'noResponse' && config.sequence && config.sequence.length > 0 && (
                        <span className="font-mono text-xs">
                          {config.sequence.map(step => `${step.delay}${step.unit.charAt(0)}`).join(' → ')}
                        </span>
                      )}
                      {type === 'noResponse' && (!config.sequence || config.sequence.length === 0) && (
                        `After ${config.delayHours || 48}h`
                      )}
                      {type === 'appointmentReminder' && `${config.hoursBefore}h before`}
                      {type === 'reEngagement' && `After ${config.delayDays}d`}
                    </span>
                  </div>
                  {type === 'noResponse' && config.sequence && config.sequence.length > 0 && (
                    <div className="mt-1 text-xs text-gray-500">
                      {config.sequence.length} step sequence configured
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Lead Filtering */}
        {workflows.leadFiltering?.mode === 'filtered' && workflows.leadFiltering?.sources?.length > 0 && (
          <div>
            <h5 className="font-medium text-gray-700 mb-2">Lead Filtering:</h5>
            <p className="text-sm text-gray-600">
              Only handling leads from: {workflows.leadFiltering.sources.join(', ')}
            </p>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header with Template Info */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-green-500 to-green-600 rounded-2xl mb-4 shadow-lg">
          <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
        <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent mb-3">
          Configure Your AI Agent
        </h1>
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 max-w-3xl mx-auto">
          <div className="flex items-center justify-center space-x-8">
            <div className="text-center">
              <div className="text-2xl mb-1">{wizardData.selectedTemplate?.icon}</div>
              <div className="text-sm font-medium text-gray-900">{wizardData.selectedTemplate?.title}</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-600">Agent Type</div>
              <div className="text-sm font-medium text-gray-900 capitalize">{wizardData.agentType?.replace('_', ' ')}</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-600">Industry</div>
              <div className="text-sm font-medium text-gray-900 capitalize">{wizardData.industry?.replace('_', ' ')}</div>
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
                    ? 'bg-white text-purple-600 shadow-sm'
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
            <span className="text-red-800 font-medium">Deployment Error:</span>
          </div>
          <p className="text-red-700 mt-1">{errors.deploy}</p>
        </div>
      )}

      {/* Action Bar */}
      <div className="flex justify-between items-center bg-gray-50 rounded-2xl p-6 border border-gray-100 mt-8">
        <div className="text-sm text-gray-600">
          Configure your agent settings using the tabs above
        </div>

        <div className="flex space-x-4">
          <button
            onClick={() => {
              console.log('Preview Agent button clicked!');
              console.log('Current wizard data:', wizardData);
              setShowPreview(true);
            }}
            disabled={isLoading}
            className="px-6 py-3 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            Preview Agent
          </button>
          <button
            onClick={() => {
              console.log('Deploy Agent button clicked!');
              console.log('Current wizard data:', wizardData);
              console.log('Calling deployAgent...');
              deployAgent();
            }}
            disabled={isLoading}
            className="px-8 py-3 text-sm font-medium text-white bg-gradient-to-r from-green-500 to-green-600 rounded-lg hover:from-green-600 hover:to-green-700 shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Deploying...
              </>
            ) : (
              'Deploy Agent'
            )}
          </button>
        </div>
      </div>

      {/* Preview Modal */}
      {showPreview && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-bold text-gray-900">Agent Preview</h3>
                <button
                  onClick={() => setShowPreview(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Agent Basics */}
                <Card className="p-4">
                  <h4 className="font-semibold text-gray-900 mb-3">Agent Information</h4>
                  <div className="space-y-2">
                    <div>
                      <span className="text-sm font-medium text-gray-600">Name: </span>
                      <span className="text-sm text-gray-900">{wizardData.persona?.agentName || 'Unnamed Agent'}</span>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-600">Type: </span>
                      <span className="text-sm text-gray-900 capitalize">{wizardData.agentType?.replace('_', ' ') || 'Not specified'}</span>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-600">Industry: </span>
                      <span className="text-sm text-gray-900 capitalize">{wizardData.industry?.replace('_', ' ') || 'Not specified'}</span>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-600">Communication: </span>
                      <span className="text-sm text-gray-900 capitalize">{wizardData.persona?.communicationMode || 'Both'}</span>
                    </div>
                    {wizardData.persona?.traits?.length > 0 && (
                      <div>
                        <span className="text-sm font-medium text-gray-600">Traits: </span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {wizardData.persona.traits.map(trait => (
                            <span key={trait} className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs">
                              {trait}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </Card>

                {/* Workflow Configuration */}
                <Card className="p-4">
                  {renderWorkflowPreview()}
                </Card>

                {/* Business Profile */}
                {wizardData.businessProfile && (
                  <Card className="p-4 md:col-span-2">
                    <h4 className="font-semibold text-gray-900 mb-3">Business Profile</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {wizardData.businessProfile.businessName && (
                        <div>
                          <span className="text-sm font-medium text-gray-600">Business Name: </span>
                          <span className="text-sm text-gray-900">{wizardData.businessProfile.businessName}</span>
                        </div>
                      )}
                      {wizardData.businessProfile.serviceArea && (
                        <div>
                          <span className="text-sm font-medium text-gray-600">Service Area: </span>
                          <span className="text-sm text-gray-900">{wizardData.businessProfile.serviceArea}</span>
                        </div>
                      )}
                      {wizardData.businessProfile.businessHours && (
                        <div>
                          <span className="text-sm font-medium text-gray-600">Business Hours: </span>
                          <span className="text-sm text-gray-900">{wizardData.businessProfile.businessHours}</span>
                        </div>
                      )}
                      {wizardData.businessProfile.servicesOffered && (
                        <div className="md:col-span-2">
                          <span className="text-sm font-medium text-gray-600">Services: </span>
                          <p className="text-sm text-gray-900 mt-1">{wizardData.businessProfile.servicesOffered}</p>
                        </div>
                      )}
                    </div>
                  </Card>
                )}
              </div>

              <div className="flex justify-end space-x-3 mt-6 pt-6 border-t border-gray-200">
                <button
                  onClick={() => setShowPreview(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Close Preview
                </button>
                <button
                  onClick={() => {
                    setShowPreview(false);
                    deployAgent();
                  }}
                  disabled={isLoading}
                  className="px-6 py-2 text-sm font-medium text-white bg-gradient-to-r from-green-500 to-green-600 rounded-lg hover:from-green-600 hover:to-green-700 disabled:opacity-50"
                >
                  Deploy Agent
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function HatchAgentConfigSimple() {
  return (
    <HatchWizardProvider>
      <HatchConfigSimpleContent />
    </HatchWizardProvider>
  );
}