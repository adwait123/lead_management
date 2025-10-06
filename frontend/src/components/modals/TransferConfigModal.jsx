import React, { useState } from 'react';
import { ToolConfigModal, ToolConfigContent, ConfigSection, TestConnection } from './ToolConfigModal';
import { Button } from '../ui/Button';

export function TransferConfigModal({ isOpen, onClose, onSave, config = {}, onConfigChange }) {
  const [transferConfig, setTransferConfig] = useState({
    teams: config?.teams || [
      {
        id: 'sales_team',
        name: 'Sales Team',
        description: 'For qualified leads and appointment scheduling',
        availability: {
          monday: { start: '09:00', end: '17:00', enabled: true },
          tuesday: { start: '09:00', end: '17:00', enabled: true },
          wednesday: { start: '09:00', end: '17:00', enabled: true },
          thursday: { start: '09:00', end: '17:00', enabled: true },
          friday: { start: '09:00', end: '17:00', enabled: true },
          saturday: { start: '09:00', end: '15:00', enabled: false },
          sunday: { start: '10:00', end: '16:00', enabled: false }
        },
        members: ['John Smith', 'Sarah Johnson'],
        priority: 1
      }
    ],
    transferMessages: config?.transferMessages || {
      'sales_team': 'I\'m connecting you with our sales specialist who can help you with scheduling and pricing.',
      'technical_support': 'Let me transfer you to our technical team who can assist with your specific needs.',
      'billing': 'I\'m transferring you to our billing department to help resolve your payment questions.',
      'manager': 'I\'m escalating your call to a manager who can provide additional assistance.'
    },
    escalationRules: config?.escalationRules || {
      maxAttempts: 2,
      fallbackTeam: 'manager',
      escalationDelay: '30_seconds',
      failureAction: 'bailout'
    },
    availabilityFallback: config?.availabilityFallback || {
      action: 'leave_message', // 'bailout', 'leave_message', 'schedule_callback'
      message: 'Our team is currently unavailable. Would you like to leave a message or schedule a callback?'
    },
    testStatus: config?.testStatus || 'not_tested'
  });

  const [newTeam, setNewTeam] = useState({
    name: '',
    description: '',
    members: [],
    priority: 1
  });

  const [newMember, setNewMember] = useState('');

  // Team priorities for ordering
  const priorityOptions = [
    { value: 1, label: 'High Priority' },
    { value: 2, label: 'Medium Priority' },
    { value: 3, label: 'Low Priority' }
  ];

  // Escalation delay options
  const delayOptions = [
    { value: '15_seconds', label: '15 seconds' },
    { value: '30_seconds', label: '30 seconds' },
    { value: '1_minute', label: '1 minute' },
    { value: '2_minutes', label: '2 minutes' }
  ];

  // Failure action options
  const failureActions = [
    { value: 'bailout', label: 'End conversation' },
    { value: 'leave_message', label: 'Take a message' },
    { value: 'schedule_callback', label: 'Schedule callback' }
  ];

  const updateConfig = (updates) => {
    const newConfig = { ...transferConfig, ...updates };
    setTransferConfig(newConfig);
    onConfigChange && onConfigChange(newConfig);
  };

  const addTeam = () => {
    if (!newTeam.name.trim()) return;

    const team = {
      ...newTeam,
      id: newTeam.name.toLowerCase().replace(/[^a-z0-9]/g, '_'),
      availability: {
        monday: { start: '09:00', end: '17:00', enabled: true },
        tuesday: { start: '09:00', end: '17:00', enabled: true },
        wednesday: { start: '09:00', end: '17:00', enabled: true },
        thursday: { start: '09:00', end: '17:00', enabled: true },
        friday: { start: '09:00', end: '17:00', enabled: true },
        saturday: { start: '09:00', end: '15:00', enabled: false },
        sunday: { start: '10:00', end: '16:00', enabled: false }
      },
      members: []
    };

    const updatedTeams = [...transferConfig.teams, team];
    updateConfig({
      teams: updatedTeams,
      transferMessages: {
        ...transferConfig.transferMessages,
        [team.id]: `I'm connecting you with our ${team.name.toLowerCase()} who can assist you.`
      }
    });

    setNewTeam({ name: '', description: '', members: [], priority: 1 });
  };

  const removeTeam = (teamId) => {
    const updatedTeams = transferConfig.teams.filter(team => team.id !== teamId);
    const updatedMessages = { ...transferConfig.transferMessages };
    delete updatedMessages[teamId];

    updateConfig({
      teams: updatedTeams,
      transferMessages: updatedMessages
    });
  };

  const updateTeamAvailability = (teamId, day, field, value) => {
    const updatedTeams = transferConfig.teams.map(team => {
      if (team.id === teamId) {
        return {
          ...team,
          availability: {
            ...team.availability,
            [day]: {
              ...team.availability[day],
              [field]: value
            }
          }
        };
      }
      return team;
    });
    updateConfig({ teams: updatedTeams });
  };

  const addTeamMember = (teamId) => {
    if (!newMember.trim()) return;

    const updatedTeams = transferConfig.teams.map(team => {
      if (team.id === teamId) {
        return {
          ...team,
          members: [...team.members, newMember.trim()]
        };
      }
      return team;
    });

    updateConfig({ teams: updatedTeams });
    setNewMember('');
  };

  const removeTeamMember = (teamId, memberIndex) => {
    const updatedTeams = transferConfig.teams.map(team => {
      if (team.id === teamId) {
        return {
          ...team,
          members: team.members.filter((_, index) => index !== memberIndex)
        };
      }
      return team;
    });
    updateConfig({ teams: updatedTeams });
  };

  const updateTransferMessage = (teamId, message) => {
    const updatedMessages = {
      ...transferConfig.transferMessages,
      [teamId]: message
    };
    updateConfig({ transferMessages: updatedMessages });
  };

  const testTransferFlow = async () => {
    updateConfig({ testStatus: 'testing' });

    // Simulate testing transfer scenarios
    setTimeout(() => {
      const success = Math.random() > 0.25; // 75% success rate for demo
      updateConfig({
        testStatus: success ? 'passed' : 'failed',
        testMessage: success
          ? 'Transfer flow tested successfully. All teams and escalation rules are working correctly.'
          : 'Test failed. Please check team availability and escalation settings.'
      });
    }, 2500);
  };

  const handleSave = () => {
    const isConfigured = transferConfig.teams.length > 0;
    onSave({
      ...transferConfig,
      enabled: true,
      configured: isConfigured
    });
  };

  return (
    <ToolConfigModal
      isOpen={isOpen}
      onClose={onClose}
      onSave={handleSave}
      title="Transfer Configuration"
      icon={
        <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      }
      isConfigured={transferConfig.teams.length > 0}
      testStatus={transferConfig.testStatus}
    >
      <ToolConfigContent
        description="Configure team transfers for when the AI agent needs to connect customers with human specialists. Set up teams, availability, and escalation rules."
      >
        {/* Team Management */}
        <ConfigSection
          title="Teams"
          description="Define the teams available for transfers"
          required
        >
          {/* Current Teams */}
          {transferConfig.teams.length > 0 && (
            <div className="space-y-4 mb-6">
              <h4 className="font-medium text-gray-900">Configured Teams ({transferConfig.teams.length})</h4>
              {transferConfig.teams.map((team) => (
                <div key={team.id} className="border rounded-lg p-4 bg-gray-50">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center">
                      <div className={`w-3 h-3 rounded-full mr-3 ${
                        team.priority === 1 ? 'bg-red-500' :
                        team.priority === 2 ? 'bg-yellow-500' : 'bg-green-500'
                      }`}></div>
                      <div>
                        <h5 className="font-medium text-gray-900">{team.name}</h5>
                        <p className="text-sm text-gray-600">{team.description}</p>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => removeTeam(team.id)}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                    >
                      Remove
                    </Button>
                  </div>

                  {/* Team Members */}
                  <div className="mb-4">
                    <h6 className="text-sm font-medium text-gray-700 mb-2">Team Members</h6>
                    <div className="flex flex-wrap gap-2 mb-2">
                      {team.members.map((member, index) => (
                        <span key={index} className="inline-flex items-center bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                          {member}
                          <button
                            onClick={() => removeTeamMember(team.id, index)}
                            className="ml-1 text-blue-600 hover:text-blue-800"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                    <div className="flex space-x-2">
                      <input
                        type="text"
                        value={newMember}
                        onChange={(e) => setNewMember(e.target.value)}
                        placeholder="Add team member name"
                        className="flex-1 px-3 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                        onKeyPress={(e) => e.key === 'Enter' && addTeamMember(team.id)}
                      />
                      <Button
                        size="sm"
                        onClick={() => addTeamMember(team.id)}
                        disabled={!newMember.trim()}
                        className="bg-blue-600 hover:bg-blue-700 text-xs"
                      >
                        Add
                      </Button>
                    </div>
                  </div>

                  {/* Availability */}
                  <div>
                    <h6 className="text-sm font-medium text-gray-700 mb-2">Availability</h6>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                      {Object.entries(team.availability || {}).map(([day, hours]) => (
                        <div key={day} className="flex items-center space-x-2">
                          <div className="w-16">
                            <label className="flex items-center">
                              <input
                                type="checkbox"
                                checked={hours.enabled}
                                onChange={(e) => updateTeamAvailability(team.id, day, 'enabled', e.target.checked)}
                                className="mr-1"
                              />
                              <span className="capitalize text-xs">{day.substring(0, 3)}</span>
                            </label>
                          </div>
                          {hours.enabled && (
                            <div className="flex items-center space-x-1">
                              <input
                                type="time"
                                value={hours.start}
                                onChange={(e) => updateTeamAvailability(team.id, day, 'start', e.target.value)}
                                className="px-2 py-1 text-xs border border-gray-300 rounded"
                              />
                              <span className="text-xs text-gray-500">-</span>
                              <input
                                type="time"
                                value={hours.end}
                                onChange={(e) => updateTeamAvailability(team.id, day, 'end', e.target.value)}
                                className="px-2 py-1 text-xs border border-gray-300 rounded"
                              />
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Add New Team */}
          <div className="bg-green-50 rounded-lg p-6">
            <h4 className="font-medium text-gray-900 mb-4">Add New Team</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Team Name</label>
                <input
                  type="text"
                  value={newTeam.name}
                  onChange={(e) => setNewTeam({...newTeam, name: e.target.value})}
                  placeholder="e.g., Technical Support"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Priority</label>
                <select
                  value={newTeam.priority}
                  onChange={(e) => setNewTeam({...newTeam, priority: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                >
                  {priorityOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <input
                  type="text"
                  value={newTeam.description}
                  onChange={(e) => setNewTeam({...newTeam, description: e.target.value})}
                  placeholder="Brief description of this team's role"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
                />
              </div>
            </div>
            <Button
              onClick={addTeam}
              disabled={!newTeam.name.trim()}
              className="mt-4 bg-green-600 hover:bg-green-700"
            >
              Add Team
            </Button>
          </div>
        </ConfigSection>

        {/* Transfer Messages */}
        <ConfigSection
          title="Transfer Messages"
          description="Customize the messages sent to customers when transferring to each team"
        >
          <div className="space-y-4">
            {transferConfig.teams.map((team) => {
              const currentMessage = transferConfig.transferMessages[team.id] ||
                `I'm connecting you with our ${team.name.toLowerCase()} who can assist you.`;

              return (
                <div key={team.id} className="border rounded-lg p-4">
                  <div className="flex items-center mb-3">
                    <div className={`w-3 h-3 rounded-full mr-3 ${
                      team.priority === 1 ? 'bg-red-500' :
                      team.priority === 2 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}></div>
                    <h5 className="font-medium text-gray-900">{team.name}</h5>
                  </div>
                  <textarea
                    value={currentMessage}
                    onChange={(e) => updateTransferMessage(team.id, e.target.value)}
                    placeholder={`Enter the transfer message for ${team.name}...`}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm"
                  />
                </div>
              );
            })}
          </div>
        </ConfigSection>

        {/* Escalation Rules */}
        <ConfigSection
          title="Escalation Rules"
          description="Configure how failed transfers are handled"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Max Transfer Attempts</label>
              <input
                type="number"
                value={transferConfig.escalationRules.maxAttempts}
                onChange={(e) => updateConfig({
                  escalationRules: {
                    ...transferConfig.escalationRules,
                    maxAttempts: parseInt(e.target.value)
                  }
                })}
                min="1"
                max="5"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Escalation Delay</label>
              <select
                value={transferConfig.escalationRules.escalationDelay}
                onChange={(e) => updateConfig({
                  escalationRules: {
                    ...transferConfig.escalationRules,
                    escalationDelay: e.target.value
                  }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              >
                {delayOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Fallback Team</label>
              <select
                value={transferConfig.escalationRules.fallbackTeam}
                onChange={(e) => updateConfig({
                  escalationRules: {
                    ...transferConfig.escalationRules,
                    fallbackTeam: e.target.value
                  }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              >
                {transferConfig.teams.map((team) => (
                  <option key={team.id} value={team.id}>
                    {team.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Final Failure Action</label>
              <select
                value={transferConfig.escalationRules.failureAction}
                onChange={(e) => updateConfig({
                  escalationRules: {
                    ...transferConfig.escalationRules,
                    failureAction: e.target.value
                  }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
              >
                {failureActions.map((action) => (
                  <option key={action.value} value={action.value}>
                    {action.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </ConfigSection>

        {/* Test Configuration */}
        <TestConnection
          onTest={testTransferFlow}
          testStatus={transferConfig.testStatus}
          testMessage={transferConfig.testMessage}
        />
      </ToolConfigContent>
    </ToolConfigModal>
  );
}