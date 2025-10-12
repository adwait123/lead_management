import React from 'react';
import { useHatchWizard } from '../HatchWizardContext';
import { Card } from '../../ui/Card';

export function WorkflowConfigTab() {
  const { wizardData, updateNestedData } = useHatchWizard();

  // Available trigger events
  const availableTriggers = [
    {
      id: 'new_lead',
      label: 'New Lead Created',
      description: 'Trigger when a new lead is added to the system',
      icon: '🆕'
    },
    {
      id: 'form_submission',
      label: 'Form Submission',
      description: 'Trigger when a lead submits a contact form',
      icon: '📝'
    },
    {
      id: 'email_opened',
      label: 'Email Opened',
      description: 'Trigger when a lead opens an email',
      icon: '📧'
    },
    {
      id: 'website_visit',
      label: 'Website Visit',
      description: 'Trigger when a lead visits the website',
      icon: '🌐'
    },
    {
      id: 'meeting_scheduled',
      label: 'Meeting Scheduled',
      description: 'Trigger when a meeting is booked',
      icon: '📅'
    },
    {
      id: 'support_ticket',
      label: 'Support Ticket',
      description: 'Trigger when a support ticket is created',
      icon: '🎫'
    }
  ];

  // Available lead sources for filtering
  const leadSources = [
    { id: 'yelp', label: 'Yelp', icon: '🟡' },
    { id: 'google', label: 'Google', icon: '🔍' },
    { id: 'website', label: 'Website', icon: '🌐' },
    { id: 'referral', label: 'Referrals', icon: '👥' },
    { id: 'facebook', label: 'Facebook', icon: '📘' },
    { id: 'other', label: 'Other Sources', icon: '📌' }
  ];

  // Initialize workflows state if it doesn't exist
  const workflows = wizardData.workflows || {
    triggers: {},
    followUps: {
      noResponse: { enabled: false, delayHours: 48 },
      appointmentReminder: { enabled: false, hoursBefore: 24 },
      reEngagement: { enabled: false, delayDays: 7 }
    },
    leadFiltering: {
      mode: 'all',
      sources: []
    }
  };

  const handleTriggerToggle = (triggerId, enabled) => {
    const newTriggers = {
      ...workflows.triggers,
      [triggerId]: {
        enabled,
        sources: enabled ? ['all'] : []
      }
    };
    updateNestedData('workflows.triggers', newTriggers);
  };

  const handleFollowUpToggle = (followUpType, enabled) => {
    const newFollowUps = {
      ...workflows.followUps,
      [followUpType]: {
        ...workflows.followUps[followUpType],
        enabled
      }
    };
    updateNestedData('workflows.followUps', newFollowUps);
  };

  const handleFollowUpDelayChange = (followUpType, value, unit) => {
    const newFollowUps = {
      ...workflows.followUps,
      [followUpType]: {
        ...workflows.followUps[followUpType],
        [unit]: parseInt(value) || 0
      }
    };
    updateNestedData('workflows.followUps', newFollowUps);
  };

  // No response sequence management
  const handleNoResponseSequenceAdd = () => {
    const currentSequence = workflows.followUps.noResponse.sequence || [];
    const newStep = {
      id: `step_${Date.now()}`,
      delay: 1,
      unit: 'hours',
      message: `Follow-up message ${currentSequence.length + 1}`
    };

    const newFollowUps = {
      ...workflows.followUps,
      noResponse: {
        ...workflows.followUps.noResponse,
        sequence: [...currentSequence, newStep]
      }
    };
    updateNestedData('workflows.followUps', newFollowUps);
  };

  const handleNoResponseSequenceRemove = (stepId) => {
    const currentSequence = workflows.followUps.noResponse.sequence || [];
    const newSequence = currentSequence.filter(step => step.id !== stepId);

    const newFollowUps = {
      ...workflows.followUps,
      noResponse: {
        ...workflows.followUps.noResponse,
        sequence: newSequence
      }
    };
    updateNestedData('workflows.followUps', newFollowUps);
  };

  const handleNoResponseSequenceUpdate = (stepId, field, value) => {
    const currentSequence = workflows.followUps.noResponse.sequence || [];
    const newSequence = currentSequence.map(step =>
      step.id === stepId ? { ...step, [field]: value } : step
    );

    const newFollowUps = {
      ...workflows.followUps,
      noResponse: {
        ...workflows.followUps.noResponse,
        sequence: newSequence
      }
    };
    updateNestedData('workflows.followUps', newFollowUps);
  };

  // Convert sequence to timeline display
  const getSequenceTimeline = (sequence) => {
    if (!sequence || sequence.length === 0) return '';

    const formatDelay = (delay, unit) => {
      const unitMap = {
        'minutes': 'm',
        'hours': 'h',
        'days': 'd'
      };
      return `${delay}${unitMap[unit] || unit}`;
    };

    return sequence.map(step => formatDelay(step.delay, step.unit)).join(' → ');
  };

  const handleLeadFilteringModeChange = (mode) => {
    updateNestedData('workflows.leadFiltering.mode', mode);
    if (mode === 'all') {
      updateNestedData('workflows.leadFiltering.sources', []);
    }
  };

  const handleSourceToggle = (sourceId, enabled) => {
    const currentSources = workflows.leadFiltering.sources || [];
    let newSources;

    if (enabled) {
      newSources = [...currentSources, sourceId];
    } else {
      newSources = currentSources.filter(s => s !== sourceId);
    }

    updateNestedData('workflows.leadFiltering.sources', newSources);
  };

  const selectedTriggersCount = Object.values(workflows.triggers).filter(t => t.enabled).length;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Workflows & Automation</h2>
        <p className="text-gray-600">Configure when and how your agent should be triggered</p>
      </div>

      {/* Immediate Triggers Section */}
      <Card className="border border-gray-200">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Immediate Triggers</h3>
              <p className="text-sm text-gray-600">Select events that should activate your agent</p>
            </div>
            <div className="bg-blue-50 px-3 py-1 rounded-full">
              <span className="text-sm font-medium text-blue-700">
                {selectedTriggersCount} selected
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {availableTriggers.map(trigger => (
              <div
                key={trigger.id}
                className={`border rounded-lg p-4 cursor-pointer transition-all duration-200 ${
                  workflows.triggers[trigger.id]?.enabled
                    ? 'border-blue-300 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => handleTriggerToggle(trigger.id, !workflows.triggers[trigger.id]?.enabled)}
              >
                <div className="flex items-start space-x-3">
                  <div className="text-2xl">{trigger.icon}</div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium text-gray-900">{trigger.label}</h4>
                      <input
                        type="checkbox"
                        checked={workflows.triggers[trigger.id]?.enabled || false}
                        onChange={(e) => handleTriggerToggle(trigger.id, e.target.checked)}
                        onClick={(e) => e.stopPropagation()}
                        className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                      />
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{trigger.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Follow-up Automation Section */}
      <Card className="border border-gray-200">
        <div className="p-6">
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Follow-up Automation</h3>
            <p className="text-sm text-gray-600">Configure time-based follow-up workflows</p>
          </div>

          <div className="space-y-4">
            {/* No Response Follow-up */}
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <span className="text-xl">⏰</span>
                  <div>
                    <h4 className="font-medium text-gray-900">No Response Follow-up Sequence</h4>
                    <p className="text-sm text-gray-600">Send automated follow-up messages when leads don't respond</p>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={workflows.followUps.noResponse.enabled}
                  onChange={(e) => handleFollowUpToggle('noResponse', e.target.checked)}
                  className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                />
              </div>

              {workflows.followUps.noResponse.enabled && (
                <div className="ml-8 space-y-4">
                  {/* Sequence Timeline Preview */}
                  {workflows.followUps.noResponse.sequence && workflows.followUps.noResponse.sequence.length > 0 && (
                    <div className="bg-blue-50 rounded-lg p-3">
                      <div className="text-sm font-medium text-blue-900 mb-1">Follow-up Timeline:</div>
                      <div className="text-sm text-blue-800 font-mono">
                        {getSequenceTimeline(workflows.followUps.noResponse.sequence)}
                      </div>
                    </div>
                  )}

                  {/* Sequence Steps */}
                  <div className="space-y-3">
                    {(workflows.followUps.noResponse.sequence || []).map((step, index) => (
                      <div key={step.id} className="border border-gray-200 rounded-lg p-3 bg-gray-50">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-700">
                            Step {index + 1}
                          </span>
                          <button
                            onClick={() => handleNoResponseSequenceRemove(step.id)}
                            className="text-red-500 hover:text-red-700 text-sm"
                          >
                            ✕ Remove
                          </button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                          {/* Delay Input */}
                          <div className="flex items-center space-x-2">
                            <span className="text-sm text-gray-600">After:</span>
                            <input
                              type="number"
                              value={step.delay}
                              onChange={(e) => handleNoResponseSequenceUpdate(step.id, 'delay', parseInt(e.target.value) || 1)}
                              className="w-16 px-2 py-1 border border-gray-300 rounded text-sm"
                              min="1"
                              max="999"
                            />
                            <select
                              value={step.unit}
                              onChange={(e) => handleNoResponseSequenceUpdate(step.id, 'unit', e.target.value)}
                              className="px-2 py-1 border border-gray-300 rounded text-sm"
                            >
                              <option value="minutes">Minutes</option>
                              <option value="hours">Hours</option>
                              <option value="days">Days</option>
                            </select>
                          </div>

                          {/* Message Template */}
                          <div className="md:col-span-2">
                            <input
                              type="text"
                              value={step.message}
                              onChange={(e) => handleNoResponseSequenceUpdate(step.id, 'message', e.target.value)}
                              placeholder="Follow-up message template"
                              className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Add Step Button */}
                  <button
                    onClick={handleNoResponseSequenceAdd}
                    className="w-full py-2 px-4 border-2 border-dashed border-gray-300 rounded-lg text-sm text-gray-600 hover:border-blue-300 hover:text-blue-600 transition-colors"
                  >
                    + Add Follow-up Step
                  </button>

                  {/* Legacy single follow-up support */}
                  {(!workflows.followUps.noResponse.sequence || workflows.followUps.noResponse.sequence.length === 0) && (
                    <div className="flex items-center space-x-2 p-3 bg-yellow-50 rounded-lg">
                      <span className="text-sm text-yellow-800">💡 Add your first follow-up step above, or use simple mode:</span>
                      <input
                        type="number"
                        value={workflows.followUps.noResponse.delayHours || 48}
                        onChange={(e) => handleFollowUpDelayChange('noResponse', e.target.value, 'delayHours')}
                        className="w-16 px-2 py-1 border border-gray-300 rounded text-sm"
                        min="1"
                        max="168"
                      />
                      <span className="text-sm text-yellow-800">hours</span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Appointment Reminder */}
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <span className="text-xl">📅</span>
                  <div>
                    <h4 className="font-medium text-gray-900">Appointment Reminders</h4>
                    <p className="text-sm text-gray-600">Send reminders before scheduled appointments</p>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={workflows.followUps.appointmentReminder.enabled}
                  onChange={(e) => handleFollowUpToggle('appointmentReminder', e.target.checked)}
                  className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                />
              </div>
              {workflows.followUps.appointmentReminder.enabled && (
                <div className="ml-8 flex items-center space-x-2">
                  <span className="text-sm text-gray-600">Send:</span>
                  <input
                    type="number"
                    value={workflows.followUps.appointmentReminder.hoursBefore}
                    onChange={(e) => handleFollowUpDelayChange('appointmentReminder', e.target.value, 'hoursBefore')}
                    className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
                    min="1"
                    max="72"
                  />
                  <span className="text-sm text-gray-600">hours before</span>
                </div>
              )}
            </div>

            {/* Re-engagement */}
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <span className="text-xl">🔄</span>
                  <div>
                    <h4 className="font-medium text-gray-900">Re-engagement Sequence</h4>
                    <p className="text-sm text-gray-600">Reach out to inactive leads</p>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={workflows.followUps.reEngagement.enabled}
                  onChange={(e) => handleFollowUpToggle('reEngagement', e.target.checked)}
                  className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                />
              </div>
              {workflows.followUps.reEngagement.enabled && (
                <div className="ml-8 flex items-center space-x-2">
                  <span className="text-sm text-gray-600">After:</span>
                  <input
                    type="number"
                    value={workflows.followUps.reEngagement.delayDays}
                    onChange={(e) => handleFollowUpDelayChange('reEngagement', e.target.value, 'delayDays')}
                    className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
                    min="1"
                    max="30"
                  />
                  <span className="text-sm text-gray-600">days of inactivity</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Lead Filtering Section */}
      <Card className="border border-gray-200">
        <div className="p-6">
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Lead Filtering</h3>
            <p className="text-sm text-gray-600">Control which leads trigger this agent</p>
          </div>

          <div className="space-y-4">
            {/* Filtering Mode */}
            <div className="space-y-3">
              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="radio"
                  name="filteringMode"
                  value="all"
                  checked={workflows.leadFiltering.mode === 'all'}
                  onChange={() => handleLeadFilteringModeChange('all')}
                  className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                />
                <div>
                  <span className="text-sm font-medium text-gray-900">Handle all leads</span>
                  <p className="text-xs text-gray-600">Agent will be triggered for leads from any source</p>
                </div>
              </label>

              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="radio"
                  name="filteringMode"
                  value="filtered"
                  checked={workflows.leadFiltering.mode === 'filtered'}
                  onChange={() => handleLeadFilteringModeChange('filtered')}
                  className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                />
                <div>
                  <span className="text-sm font-medium text-gray-900">Only specific sources</span>
                  <p className="text-xs text-gray-600">Agent will only be triggered for selected lead sources</p>
                </div>
              </label>
            </div>

            {/* Source Selection */}
            {workflows.leadFiltering.mode === 'filtered' && (
              <div className="ml-7 mt-4">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {leadSources.map(source => (
                    <label key={source.id} className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={workflows.leadFiltering.sources.includes(source.id)}
                        onChange={(e) => handleSourceToggle(source.id, e.target.checked)}
                        className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                      />
                      <span className="text-lg">{source.icon}</span>
                      <span className="text-sm text-gray-700">{source.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Summary Section */}
      {(selectedTriggersCount > 0 || Object.values(workflows.followUps).some(f => f.enabled)) && (
        <Card className="border border-blue-200 bg-blue-50">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-3">Workflow Summary</h3>
            <div className="space-y-2">
              {selectedTriggersCount > 0 && (
                <p className="text-sm text-blue-800">
                  ✅ Agent will be triggered by <strong>{selectedTriggersCount}</strong> event{selectedTriggersCount !== 1 ? 's' : ''}
                </p>
              )}
              {workflows.followUps.noResponse.enabled && (
                <p className="text-sm text-blue-800">
                  {workflows.followUps.noResponse.sequence && workflows.followUps.noResponse.sequence.length > 0 ? (
                    <>
                      ⏰ Follow-up sequence: <strong>{getSequenceTimeline(workflows.followUps.noResponse.sequence)}</strong>
                    </>
                  ) : (
                    <>
                      ⏰ Follow-up messages after <strong>{workflows.followUps.noResponse.delayHours || 48} hours</strong> of no response
                    </>
                  )}
                </p>
              )}
              {workflows.followUps.appointmentReminder.enabled && (
                <p className="text-sm text-blue-800">
                  📅 Appointment reminders <strong>{workflows.followUps.appointmentReminder.hoursBefore} hours</strong> in advance
                </p>
              )}
              {workflows.followUps.reEngagement.enabled && (
                <p className="text-sm text-blue-800">
                  🔄 Re-engagement after <strong>{workflows.followUps.reEngagement.delayDays} days</strong> of inactivity
                </p>
              )}
              {workflows.leadFiltering.mode === 'filtered' && workflows.leadFiltering.sources.length > 0 && (
                <p className="text-sm text-blue-800">
                  🎯 Only handling leads from: <strong>{workflows.leadFiltering.sources.join(', ')}</strong>
                </p>
              )}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}