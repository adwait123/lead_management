import React, { useState } from 'react';
import { ToolConfigModal, ToolConfigContent, ConfigSection, TestConnection } from './ToolConfigModal';
import { Button } from '../ui/Button';

export function BailoutConfigModal({ isOpen, onClose, onSave, config = {}, onConfigChange }) {
  const [bailoutConfig, setBailoutConfig] = useState({
    dispositions: config?.dispositions || [
      'Appointment set',
      'Bailout',
      'Discard',
      'Schedule follow-up',
      'Success/Completed',
      'Transfer'
    ],
    customDispositions: config?.customDispositions || [],
    endMessages: config?.endMessages || {
      'appointment_set': 'Thank you! Your appointment has been scheduled. We\'ll send you a confirmation shortly.',
      'bailout': 'Thank you for contacting us. If you need any assistance in the future, please don\'t hesitate to reach out.',
      'discard': 'Thank you for your time. Have a great day!',
      'schedule_follow_up': 'Thank you for your interest. We\'ll follow up with you shortly.',
      'success_completed': 'Great! We\'ve completed your request. Is there anything else I can help you with?',
      'transfer': 'I\'m connecting you with one of our specialists who can better assist you. Please hold on.'
    },
    crmMapping: config?.crmMapping || {
      'appointment_set': 'scheduled',
      'bailout': 'unqualified',
      'discard': 'disqualified',
      'schedule_follow_up': 'follow_up',
      'success_completed': 'converted',
      'transfer': 'transferred'
    },
    followUpActions: config?.followUpActions || {},
    testStatus: config?.testStatus || 'not_tested'
  });

  const [newDisposition, setNewDisposition] = useState('');
  const [selectedDisposition, setSelectedDisposition] = useState(null);

  // CRM lead statuses
  const crmStatuses = [
    { value: 'new', label: 'New Lead' },
    { value: 'contacted', label: 'Contacted' },
    { value: 'qualified', label: 'Qualified' },
    { value: 'unqualified', label: 'Unqualified' },
    { value: 'scheduled', label: 'Appointment Scheduled' },
    { value: 'converted', label: 'Converted' },
    { value: 'disqualified', label: 'Disqualified' },
    { value: 'follow_up', label: 'Follow-up Required' },
    { value: 'transferred', label: 'Transferred to Team' },
    { value: 'on_hold', label: 'On Hold' },
    { value: 'lost', label: 'Lost Opportunity' }
  ];

  const updateConfig = (updates) => {
    const newConfig = { ...bailoutConfig, ...updates };
    setBailoutConfig(newConfig);
    onConfigChange && onConfigChange(newConfig);
  };

  const addCustomDisposition = () => {
    if (!newDisposition.trim()) return;

    const updatedCustom = [...bailoutConfig.customDispositions, {
      id: Date.now(),
      name: newDisposition.trim(),
      message: `Thank you for contacting us regarding ${newDisposition.toLowerCase()}.`,
      crmStatus: 'unqualified'
    }];

    updateConfig({ customDispositions: updatedCustom });
    setNewDisposition('');
  };

  const removeCustomDisposition = (id) => {
    const updatedCustom = bailoutConfig.customDispositions.filter(d => d.id !== id);
    updateConfig({ customDispositions: updatedCustom });
  };

  const updateEndMessage = (disposition, message) => {
    const dispositionKey = disposition.toLowerCase().replace(/[^a-z0-9]/g, '_');
    const updatedMessages = {
      ...bailoutConfig.endMessages,
      [dispositionKey]: message
    };
    updateConfig({ endMessages: updatedMessages });
  };

  const updateCrmMapping = (disposition, crmStatus) => {
    const dispositionKey = disposition.toLowerCase().replace(/[^a-z0-9]/g, '_');
    const updatedMapping = {
      ...bailoutConfig.crmMapping,
      [dispositionKey]: crmStatus
    };
    updateConfig({ crmMapping: updatedMapping });
  };

  const testBailoutFlow = async () => {
    updateConfig({ testStatus: 'testing' });

    // Simulate testing different disposition flows
    setTimeout(() => {
      const success = Math.random() > 0.2; // 80% success rate for demo
      updateConfig({
        testStatus: success ? 'passed' : 'failed',
        testMessage: success
          ? 'All disposition flows tested successfully. Messages and CRM mapping are working correctly.'
          : 'Test failed. Please check your disposition configuration and try again.'
      });
    }, 3000);
  };

  const handleSave = () => {
    const isConfigured = bailoutConfig.dispositions.length > 0 || bailoutConfig.customDispositions.length > 0;
    onSave({
      ...bailoutConfig,
      enabled: true,
      configured: isConfigured
    });
  };

  const getAllDispositions = () => {
    return [
      ...bailoutConfig.dispositions.map(d => ({ name: d, isDefault: true })),
      ...bailoutConfig.customDispositions.map(d => ({ ...d, isDefault: false }))
    ];
  };

  return (
    <ToolConfigModal
      isOpen={isOpen}
      onClose={onClose}
      onSave={handleSave}
      title="Conversation End Configuration"
      icon={
        <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
        </svg>
      }
      isConfigured={bailoutConfig.dispositions.length > 0 || bailoutConfig.customDispositions.length > 0}
      testStatus={bailoutConfig.testStatus}
    >
      <ToolConfigContent
        description="Configure how conversations end and what happens when the AI agent uses the /bailout command. Set up dispositions, end messages, and CRM integration."
      >
        {/* Disposition Management */}
        <ConfigSection
          title="Disposition Types"
          description="Define the different ways a conversation can end"
          required
        >
          {/* Default Dispositions */}
          <div className="mb-6">
            <h4 className="font-medium text-gray-900 mb-3">Default Dispositions</h4>
            <div className="space-y-2">
              {bailoutConfig.dispositions.map((disposition, index) => (
                <div key={index} className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-blue-500 rounded-full mr-3"></div>
                    <span className="font-medium text-gray-900">{disposition}</span>
                  </div>
                  <span className="text-xs text-gray-500 bg-gray-200 px-2 py-1 rounded">Default</span>
                </div>
              ))}
            </div>
          </div>

          {/* Custom Dispositions */}
          {bailoutConfig.customDispositions.length > 0 && (
            <div className="mb-6">
              <h4 className="font-medium text-gray-900 mb-3">Custom Dispositions</h4>
              <div className="space-y-2">
                {bailoutConfig.customDispositions.map((disposition) => (
                  <div key={disposition.id} className="flex items-center justify-between bg-green-50 rounded-lg p-3">
                    <div className="flex items-center">
                      <div className="w-3 h-3 bg-green-500 rounded-full mr-3"></div>
                      <span className="font-medium text-gray-900">{disposition.name}</span>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => removeCustomDisposition(disposition.id)}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                    >
                      Remove
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Add Custom Disposition */}
          <div className="bg-blue-50 rounded-lg p-6">
            <h4 className="font-medium text-gray-900 mb-4">Add Custom Disposition</h4>
            <div className="flex space-x-3">
              <input
                type="text"
                value={newDisposition}
                onChange={(e) => setNewDisposition(e.target.value)}
                placeholder="e.g., Outside Service Area, Price Objection"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                onKeyPress={(e) => e.key === 'Enter' && addCustomDisposition()}
              />
              <Button
                onClick={addCustomDisposition}
                disabled={!newDisposition.trim()}
                className="bg-blue-600 hover:bg-blue-700"
              >
                Add Disposition
              </Button>
            </div>
          </div>
        </ConfigSection>

        {/* End Messages Configuration */}
        <ConfigSection
          title="End Messages"
          description="Customize the messages sent when each disposition is selected"
        >
          <div className="space-y-4">
            {getAllDispositions().map((disposition, index) => {
              const dispositionKey = disposition.name.toLowerCase().replace(/[^a-z0-9]/g, '_');
              const currentMessage = bailoutConfig.endMessages[dispositionKey] ||
                `Thank you for contacting us regarding ${disposition.name.toLowerCase()}.`;

              return (
                <div key={index} className="border rounded-lg p-4">
                  <div className="flex items-center mb-3">
                    <div className={`w-3 h-3 rounded-full mr-3 ${
                      disposition.isDefault ? 'bg-blue-500' : 'bg-green-500'
                    }`}></div>
                    <h5 className="font-medium text-gray-900">{disposition.name}</h5>
                  </div>
                  <textarea
                    value={currentMessage}
                    onChange={(e) => updateEndMessage(disposition.name, e.target.value)}
                    placeholder={`Enter the message for ${disposition.name} disposition...`}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                  />
                </div>
              );
            })}
          </div>
        </ConfigSection>

        {/* CRM Integration */}
        <ConfigSection
          title="CRM Integration"
          description="Map each disposition to a CRM lead status"
        >
          <div className="space-y-4">
            {getAllDispositions().map((disposition, index) => {
              const dispositionKey = disposition.name.toLowerCase().replace(/[^a-z0-9]/g, '_');
              const currentMapping = bailoutConfig.crmMapping[dispositionKey] || 'unqualified';

              return (
                <div key={index} className="flex items-center justify-between bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full mr-3 ${
                      disposition.isDefault ? 'bg-blue-500' : 'bg-green-500'
                    }`}></div>
                    <span className="font-medium text-gray-900">{disposition.name}</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className="text-sm text-gray-600">maps to</span>
                    <select
                      value={currentMapping}
                      onChange={(e) => updateCrmMapping(disposition.name, e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    >
                      {crmStatuses.map((status) => (
                        <option key={status.value} value={status.value}>
                          {status.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              );
            })}
          </div>
        </ConfigSection>

        {/* Message Templates */}
        <ConfigSection
          title="Message Templates"
          description="Common phrases and variables you can use in end messages"
        >
          <div className="bg-yellow-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-3">Available Variables</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
              <div className="bg-white rounded px-2 py-1"><code>{'{customer_name}'}</code></div>
              <div className="bg-white rounded px-2 py-1"><code>{'{service_type}'}</code></div>
              <div className="bg-white rounded px-2 py-1"><code>{'{phone_number}'}</code></div>
              <div className="bg-white rounded px-2 py-1"><code>{'{company_name}'}</code></div>
              <div className="bg-white rounded px-2 py-1"><code>{'{agent_name}'}</code></div>
              <div className="bg-white rounded px-2 py-1"><code>{'{current_date}'}</code></div>
            </div>
            <p className="text-xs text-gray-600 mt-3">
              These variables will be automatically replaced with actual values when the message is sent.
            </p>
          </div>
        </ConfigSection>

        {/* Test Configuration */}
        <TestConnection
          onTest={testBailoutFlow}
          testStatus={bailoutConfig.testStatus}
          testMessage={bailoutConfig.testMessage}
        />
      </ToolConfigContent>
    </ToolConfigModal>
  );
}