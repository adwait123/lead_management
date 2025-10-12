import React, { useState } from 'react';
import { useHatchWizard } from '../HatchWizardContext';
import { Button } from '../../ui/Button';

export function AgentBasicsTab() {
  const { wizardData, updateWizardData } = useHatchWizard();
  const [persona, setPersona] = useState(wizardData.persona || {});

  // Simplified personality traits for quick selection
  const personalityTraits = [
    { id: 'professional', label: 'Professional', description: 'Business-focused and formal' },
    { id: 'friendly', label: 'Friendly', description: 'Warm and approachable' },
    { id: 'helpful', label: 'Helpful', description: 'Solution-oriented' },
    { id: 'efficient', label: 'Efficient', description: 'Quick and direct' }
  ];

  // Quick name suggestions
  const sampleNames = ['Sarah', 'Mike', 'Jessica', 'David', 'Amanda', 'Chris'];

  const handlePersonaChange = (key, value) => {
    const updatedPersona = { ...persona, [key]: value };
    setPersona(updatedPersona);
    updateWizardData({ persona: updatedPersona });
  };

  const handleActiveStatusChange = (isActive) => {
    updateWizardData({ isActive });
  };

  const toggleTrait = (traitId) => {
    const currentTraits = persona.traits || [];
    const updatedTraits = currentTraits.includes(traitId)
      ? currentTraits.filter(t => t !== traitId)
      : [...currentTraits, traitId];
    handlePersonaChange('traits', updatedTraits);
  };

  const isTraitSelected = (traitId) => {
    return (persona.traits || []).includes(traitId);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Agent Basics
        </h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Set up your AI agent's core personality and communication preferences.
        </p>
      </div>

      {/* Agent Name */}
      <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-6">
        <label className="block text-lg font-semibold text-gray-900 mb-4">
          AI Agent Name
          <span className="text-red-500 ml-1">*</span>
        </label>
        <input
          type="text"
          value={persona.agentName || ''}
          onChange={(e) => handlePersonaChange('agentName', e.target.value)}
          placeholder="Enter a friendly name for your agent"
          className="w-full px-4 py-3 text-lg border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors"
        />
        <div className="mt-4">
          <span className="text-sm text-gray-600 mr-2">Popular choices:</span>
          {sampleNames.map((name) => (
            <Button
              key={name}
              variant="outline"
              size="sm"
              onClick={() => handlePersonaChange('agentName', name)}
              className="mr-2 mb-2 text-xs py-1 px-3 text-purple-600 hover:text-purple-700 hover:bg-purple-50 border-purple-200"
            >
              {name}
            </Button>
          ))}
        </div>
      </div>

      {/* Agent Active Status */}
      <div className="bg-gradient-to-r from-orange-50 to-red-50 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <label className="block text-lg font-semibold text-gray-900 mb-2">
              Agent Status
            </label>
            <p className="text-sm text-gray-600">
              {wizardData.isActive !== false ?
                'Agent is currently active and will respond to triggers' :
                'Agent is deactivated and will not respond to triggers'
              }
            </p>
          </div>
          <div className="flex items-center">
            <label className="flex items-center cursor-pointer">
              <span className="mr-3 text-sm font-medium text-gray-700">
                {wizardData.isActive !== false ? 'Active' : 'Inactive'}
              </span>
              <div className="relative">
                <input
                  type="checkbox"
                  checked={wizardData.isActive !== false}
                  onChange={(e) => handleActiveStatusChange(e.target.checked)}
                  className="sr-only"
                />
                <div className={`w-14 h-8 rounded-full transition-all duration-200 ${
                  wizardData.isActive !== false ? 'bg-green-500' : 'bg-gray-300'
                }`}>
                  <div className={`w-6 h-6 bg-white rounded-full shadow-md transform transition-transform duration-200 mt-1 ml-1 ${
                    wizardData.isActive !== false ? 'translate-x-6' : 'translate-x-0'
                  }`}></div>
                </div>
              </div>
            </label>
          </div>
        </div>
      </div>

      {/* Communication Mode */}
      <div className="bg-gradient-to-r from-blue-50 to-cyan-50 rounded-lg p-6">
        <label className="block text-lg font-semibold text-gray-900 mb-4">
          Communication Mode
          <span className="text-red-500 ml-1">*</span>
        </label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { value: 'voice', label: 'Voice Only', description: 'Phone conversations', icon: '📞' },
            { value: 'text', label: 'Text Only', description: 'SMS and chat', icon: '💬' },
            { value: 'both', label: 'Voice & Text', description: 'All channels', icon: '🎯' }
          ].map((mode) => (
            <label
              key={mode.value}
              className={`flex flex-col items-center p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 ${
                persona.communicationMode === mode.value
                  ? 'border-blue-500 bg-blue-50 shadow-md'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              <input
                type="radio"
                name="communicationMode"
                value={mode.value}
                checked={persona.communicationMode === mode.value}
                onChange={(e) => handlePersonaChange('communicationMode', e.target.value)}
                className="sr-only"
              />
              <div className="text-2xl mb-2">{mode.icon}</div>
              <div className="text-sm font-medium text-gray-900 text-center">{mode.label}</div>
              <div className="text-xs text-gray-600 text-center mt-1">{mode.description}</div>
            </label>
          ))}
        </div>
      </div>

      {/* Personality Traits */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-6">
        <label className="block text-lg font-semibold text-gray-900 mb-4">
          Personality Traits
          <span className="text-red-500 ml-1">*</span>
          <span className="text-sm font-normal text-gray-600 ml-2">(Select 2-4 traits)</span>
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {personalityTraits.map((trait) => (
            <div
              key={trait.id}
              onClick={() => toggleTrait(trait.id)}
              className={`cursor-pointer rounded-lg border-2 p-4 transition-all duration-200 ${
                isTraitSelected(trait.id)
                  ? 'border-green-500 bg-green-50 shadow-md'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-gray-900">{trait.label}</h4>
                {isTraitSelected(trait.id) && (
                  <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </div>
              <p className="text-sm text-gray-600">{trait.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Preview */}
      {persona.agentName && persona.communicationMode && (persona.traits || []).length >= 2 && (
        <div className="bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Preview</h3>
          <div className="bg-white rounded-lg p-4 border">
            <div className="flex items-center mb-3">
              <div className="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center text-white font-semibold mr-3">
                {persona.agentName.charAt(0)}
              </div>
              <div>
                <h4 className="font-semibold text-gray-900">{persona.agentName}</h4>
                <p className="text-sm text-gray-600">
                  {(persona.traits || []).map(t => personalityTraits.find(pt => pt.id === t)?.label).join(', ')}
                </p>
              </div>
            </div>
            <div className="text-sm text-gray-700">
              <p><strong>Communication:</strong> {persona.communicationMode?.replace('_', ' ')}</p>
            </div>
          </div>
        </div>
      )}

      {/* Validation Message */}
      {(!persona.agentName || !persona.communicationMode || (persona.traits || []).length < 2) && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-yellow-700">
                Please complete all required fields: agent name, communication mode, and at least 2 personality traits.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}