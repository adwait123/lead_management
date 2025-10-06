import React, { useState } from 'react';
import { ToolConfigModal, ToolConfigContent, ConfigSection, TestConnection } from './ToolConfigModal';
import { Button } from '../ui/Button';

export function AppointmentConfigModal({ isOpen, onClose, onSave, config = {}, onConfigChange }) {
  const defaultBusinessHours = {
    monday: { start: '09:00', end: '17:00', enabled: true },
    tuesday: { start: '09:00', end: '17:00', enabled: true },
    wednesday: { start: '09:00', end: '17:00', enabled: true },
    thursday: { start: '09:00', end: '17:00', enabled: true },
    friday: { start: '09:00', end: '17:00', enabled: true },
    saturday: { start: '09:00', end: '15:00', enabled: true },
    sunday: { start: '10:00', end: '16:00', enabled: false }
  };

  const [appointmentConfig, setAppointmentConfig] = useState({
    calendarIntegration: config?.calendarIntegration || null,
    appointmentTypes: config?.appointmentTypes || [],
    availabilityRules: {
      businessHours: config?.availabilityRules?.businessHours || defaultBusinessHours,
      minimumNotice: config?.availabilityRules?.minimumNotice || '2_hours',
      maxAdvanceBooking: config?.availabilityRules?.maxAdvanceBooking || '30_days'
    },
    confirmationMessages: config?.confirmationMessages || {
      booking: 'Your appointment has been scheduled for {date} at {time}. We\'ll send you a confirmation shortly.',
      reminder: 'Reminder: You have an appointment scheduled for {date} at {time}.',
      cancellation: 'Your appointment has been cancelled. Please contact us to reschedule.'
    },
    testStatus: config?.testStatus || 'not_tested'
  });

  const [newAppointmentType, setNewAppointmentType] = useState({
    name: '',
    duration: 60,
    description: '',
    color: '#3B82F6'
  });

  // Available calendar integrations
  const calendarIntegrations = [
    {
      id: 'google_calendar',
      name: 'Google Calendar',
      description: 'Sync with Google Calendar',
      icon: '📅',
      status: 'available'
    },
    {
      id: 'servicetitan',
      name: 'ServiceTitan',
      description: 'Professional field service management',
      icon: '🔧',
      status: 'available'
    },
    {
      id: 'outlook_365',
      name: 'Outlook 365',
      description: 'Microsoft Office 365 calendar',
      icon: '📧',
      status: 'available'
    },
    {
      id: 'housecall_pro',
      name: 'Housecall Pro',
      description: 'Home service scheduling',
      icon: '🏠',
      status: 'coming_soon'
    },
    {
      id: 'jobber',
      name: 'Jobber',
      description: 'Home service business management',
      icon: '⚡',
      status: 'coming_soon'
    }
  ];

  const defaultAppointmentTypes = [
    { name: 'Consultation', duration: 30, description: 'Initial consultation and assessment', color: '#3B82F6' },
    { name: 'Repair', duration: 120, description: 'Standard repair service', color: '#EF4444' },
    { name: 'Installation', duration: 240, description: 'New installation service', color: '#10B981' },
    { name: 'Maintenance', duration: 90, description: 'Routine maintenance check', color: '#F59E0B' },
    { name: 'Emergency', duration: 60, description: 'Emergency service call', color: '#DC2626' }
  ];

  const updateConfig = (updates) => {
    const newConfig = { ...appointmentConfig, ...updates };
    setAppointmentConfig(newConfig);
    onConfigChange && onConfigChange(newConfig);
  };

  const handleCalendarSelection = (integration) => {
    updateConfig({ calendarIntegration: integration });
  };

  const addAppointmentType = (type = null) => {
    const typeToAdd = type || newAppointmentType;
    if (!typeToAdd.name.trim()) return;

    const updatedTypes = [...appointmentConfig.appointmentTypes, { ...typeToAdd, id: Date.now() }];
    updateConfig({ appointmentTypes: updatedTypes });

    if (!type) {
      setNewAppointmentType({ name: '', duration: 60, description: '', color: '#3B82F6' });
    }
  };

  const removeAppointmentType = (id) => {
    const updatedTypes = appointmentConfig.appointmentTypes.filter(type => type.id !== id);
    updateConfig({ appointmentTypes: updatedTypes });
  };

  const updateBusinessHours = (day, field, value) => {
    const updatedRules = {
      ...appointmentConfig.availabilityRules,
      businessHours: {
        ...appointmentConfig.availabilityRules.businessHours,
        [day]: {
          ...appointmentConfig.availabilityRules.businessHours[day],
          [field]: value
        }
      }
    };
    updateConfig({ availabilityRules: updatedRules });
  };

  const testCalendarConnection = async () => {
    updateConfig({ testStatus: 'testing' });

    // Simulate API test
    setTimeout(() => {
      const success = Math.random() > 0.3; // 70% success rate for demo
      updateConfig({
        testStatus: success ? 'passed' : 'failed',
        testMessage: success
          ? 'Calendar connection successful! Ready to book appointments.'
          : 'Connection failed. Please check your calendar integration settings.'
      });
    }, 2000);
  };

  const handleSave = () => {
    const isConfigured = appointmentConfig.calendarIntegration && appointmentConfig.appointmentTypes.length > 0;
    onSave({
      ...appointmentConfig,
      enabled: true,
      configured: isConfigured
    });
  };

  return (
    <ToolConfigModal
      isOpen={isOpen}
      onClose={onClose}
      onSave={handleSave}
      title="Appointment Booking Configuration"
      icon={
        <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      }
      isConfigured={appointmentConfig.calendarIntegration && appointmentConfig.appointmentTypes.length > 0}
      testStatus={appointmentConfig.testStatus}
    >
      <ToolConfigContent
        description="Configure how your AI agent books appointments with customers. Connect your calendar system and define appointment types."
      >
        {/* Calendar Integration Selection */}
        <ConfigSection
          title="Calendar Integration"
          description="Choose which calendar system to connect with"
          required
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {calendarIntegrations.map((integration) => (
              <div
                key={integration.id}
                onClick={() => integration.status === 'available' && handleCalendarSelection(integration)}
                className={`relative border-2 rounded-lg p-4 cursor-pointer transition-all duration-200 ${
                  appointmentConfig.calendarIntegration?.id === integration.id
                    ? 'border-blue-500 bg-blue-50'
                    : integration.status === 'available'
                    ? 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    : 'border-gray-100 bg-gray-50 cursor-not-allowed opacity-60'
                }`}
              >
                <div className="flex items-center">
                  <div className="text-2xl mr-3">{integration.icon}</div>
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{integration.name}</h4>
                    <p className="text-sm text-gray-600">{integration.description}</p>
                  </div>
                  {integration.status === 'coming_soon' && (
                    <span className="absolute top-2 right-2 bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded">
                      Coming Soon
                    </span>
                  )}
                  {appointmentConfig.calendarIntegration?.id === integration.id && (
                    <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
              </div>
            ))}
          </div>
        </ConfigSection>

        {/* Appointment Types */}
        <ConfigSection
          title="Appointment Types"
          description="Define the types of appointments customers can book"
          required
        >
          {/* Current Appointment Types */}
          {appointmentConfig.appointmentTypes.length > 0 && (
            <div className="space-y-3 mb-6">
              <h4 className="font-medium text-gray-900">Configured Types ({appointmentConfig.appointmentTypes.length})</h4>
              {appointmentConfig.appointmentTypes.map((type) => (
                <div key={type.id} className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
                  <div className="flex items-center">
                    <div
                      className="w-4 h-4 rounded-full mr-3"
                      style={{ backgroundColor: type.color }}
                    ></div>
                    <div>
                      <h5 className="font-medium text-gray-900">{type.name}</h5>
                      <p className="text-sm text-gray-600">{type.duration} minutes • {type.description}</p>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => removeAppointmentType(type.id)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                  >
                    Remove
                  </Button>
                </div>
              ))}
            </div>
          )}

          {/* Quick Add Default Types */}
          <div className="mb-6">
            <h4 className="font-medium text-gray-900 mb-3">Quick Add - Common Service Types</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {defaultAppointmentTypes.filter(defaultType =>
                !appointmentConfig.appointmentTypes.some(existing => existing.name === defaultType.name)
              ).map((type, index) => (
                <div key={index} className="flex items-center justify-between bg-white border rounded-lg p-3">
                  <div className="flex items-center">
                    <div
                      className="w-4 h-4 rounded-full mr-3"
                      style={{ backgroundColor: type.color }}
                    ></div>
                    <div>
                      <h5 className="font-medium text-gray-900 text-sm">{type.name}</h5>
                      <p className="text-xs text-gray-600">{type.duration} min • {type.description}</p>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => addAppointmentType(type)}
                    className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 border-blue-200"
                  >
                    Add
                  </Button>
                </div>
              ))}
            </div>
          </div>

          {/* Add Custom Type */}
          <div className="bg-blue-50 rounded-lg p-6">
            <h4 className="font-medium text-gray-900 mb-4">Add Custom Appointment Type</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Type Name</label>
                <input
                  type="text"
                  value={newAppointmentType.name}
                  onChange={(e) => setNewAppointmentType({...newAppointmentType, name: e.target.value})}
                  placeholder="e.g., Emergency Repair"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Duration (minutes)</label>
                <input
                  type="number"
                  value={newAppointmentType.duration}
                  onChange={(e) => setNewAppointmentType({...newAppointmentType, duration: parseInt(e.target.value)})}
                  min="15"
                  max="480"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <input
                  type="text"
                  value={newAppointmentType.description}
                  onChange={(e) => setNewAppointmentType({...newAppointmentType, description: e.target.value})}
                  placeholder="Brief description of this appointment type"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
            <Button
              onClick={() => addAppointmentType()}
              disabled={!newAppointmentType.name.trim()}
              className="mt-4 bg-blue-600 hover:bg-blue-700"
            >
              Add Appointment Type
            </Button>
          </div>
        </ConfigSection>

        {/* Business Hours */}
        <ConfigSection
          title="Availability Rules"
          description="Set when appointments can be booked"
        >
          <div className="space-y-4">
            <h4 className="font-medium text-gray-900">Business Hours</h4>
            {Object.entries(appointmentConfig.availabilityRules?.businessHours || defaultBusinessHours).map(([day, hours]) => (
              <div key={day} className="flex items-center space-x-4">
                <div className="w-20">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={hours.enabled}
                      onChange={(e) => updateBusinessHours(day, 'enabled', e.target.checked)}
                      className="mr-2"
                    />
                    <span className="capitalize text-sm font-medium">{day}</span>
                  </label>
                </div>
                {hours.enabled && (
                  <>
                    <input
                      type="time"
                      value={hours.start}
                      onChange={(e) => updateBusinessHours(day, 'start', e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded"
                    />
                    <span className="text-gray-500">to</span>
                    <input
                      type="time"
                      value={hours.end}
                      onChange={(e) => updateBusinessHours(day, 'end', e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded"
                    />
                  </>
                )}
              </div>
            ))}
          </div>
        </ConfigSection>

        {/* Test Connection */}
        {appointmentConfig.calendarIntegration && (
          <TestConnection
            onTest={testCalendarConnection}
            testStatus={appointmentConfig.testStatus}
            testMessage={appointmentConfig.testMessage}
          />
        )}
      </ToolConfigContent>
    </ToolConfigModal>
  );
}