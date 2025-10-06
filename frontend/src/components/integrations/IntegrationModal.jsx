import React, { useState } from 'react';
import { Button } from '../ui/Button';

export function IntegrationModal({ integration, isOpen, onClose, onSave }) {
  const [formData, setFormData] = useState({});
  const [hasChanges, setHasChanges] = useState(false);
  const [testStatus, setTestStatus] = useState('not_tested'); // 'not_tested', 'testing', 'passed', 'failed'
  const [logoError, setLogoError] = useState(false);

  if (!isOpen || !integration) return null;

  const handleLogoError = () => {
    setLogoError(true);
  };

  const handleInputChange = (fieldName, value) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
    setHasChanges(true);
    setTestStatus('not_tested'); // Reset test status when form changes
  };

  const handleSave = () => {
    onSave(integration.id, formData);
    setHasChanges(false);
    onClose();
  };

  const handleCancel = () => {
    if (hasChanges) {
      if (window.confirm('You have unsaved changes. Are you sure you want to cancel?')) {
        setFormData({});
        setHasChanges(false);
        onClose();
      }
    } else {
      onClose();
    }
  };

  const handleTestConnection = async () => {
    setTestStatus('testing');
    // Simulate API test - replace with actual API call
    setTimeout(() => {
      // Random success/failure for demo
      const success = Math.random() > 0.3;
      setTestStatus(success ? 'passed' : 'failed');
    }, 2000);
  };

  const getTestStatusColor = () => {
    switch (testStatus) {
      case 'passed': return 'text-green-600 bg-green-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'testing': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getTestStatusText = () => {
    switch (testStatus) {
      case 'passed': return 'Connection Successful';
      case 'failed': return 'Connection Failed';
      case 'testing': return 'Testing Connection...';
      default: return 'Not Tested';
    }
  };

  const renderFormField = (field) => {
    const fieldId = `${integration.id}-${field.name}`;

    if (field.type === 'select') {
      return (
        <div key={field.name} className="space-y-2">
          <label htmlFor={fieldId} className="block text-sm font-medium text-gray-700">
            {field.label}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </label>
          <select
            id={fieldId}
            value={formData[field.name] || ''}
            onChange={(e) => handleInputChange(field.name, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required={field.required}
          >
            <option value="">Select {field.label}</option>
            {field.options.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      );
    }

    return (
      <div key={field.name} className="space-y-2">
        <label htmlFor={fieldId} className="block text-sm font-medium text-gray-700">
          {field.label}
          {field.required && <span className="text-red-500 ml-1">*</span>}
        </label>
        <input
          id={fieldId}
          type={field.type}
          value={formData[field.name] || ''}
          onChange={(e) => handleInputChange(field.name, e.target.value)}
          placeholder={field.placeholder}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          required={field.required}
        />
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b bg-gradient-to-r from-gray-50 to-blue-50">
          <div className="flex items-center">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center mr-4 overflow-hidden">
              {!logoError && integration.logoUrl ? (
                <img
                  src={integration.logoUrl}
                  alt={`${integration.name} logo`}
                  className="w-full h-full object-contain"
                  onError={handleLogoError}
                />
              ) : (
                <div className={`w-full h-full ${integration.logoFallback.color} rounded-lg flex items-center justify-center text-white font-bold`}>
                  {integration.logoFallback.text}
                </div>
              )}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{integration.name}</h2>
              <div className="flex items-center space-x-3 mt-1">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  integration.isConnected ? 'text-green-600 bg-green-100' : 'text-yellow-600 bg-yellow-100'
                }`}>
                  {integration.isConnected ? 'Connected' : 'Not Connected'}
                </span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getTestStatusColor()}`}>
                  {getTestStatusText()}
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={handleCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-6">
            {/* Description */}
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-blue-800 text-sm leading-relaxed">
                {integration.description}. Enter your API credentials below to connect this integration.
              </p>
            </div>

            {/* Form Fields */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                API Configuration
                <span className="text-red-500 ml-1">*</span>
              </h3>

              <div className="space-y-4">
                {integration.fields.map(renderFormField)}
              </div>
            </div>

            {/* Test Connection */}
            <div className="bg-gray-50 rounded-lg p-4 border">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900">Test Connection</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    Verify that your configuration is working correctly
                  </p>
                  {testStatus === 'failed' && (
                    <p className="text-sm text-red-600 mt-2">
                      Connection failed. Please check your credentials and try again.
                    </p>
                  )}
                  {testStatus === 'passed' && (
                    <p className="text-sm text-green-600 mt-2">
                      Connection successful! Your integration is ready to use.
                    </p>
                  )}
                </div>

                <Button
                  onClick={handleTestConnection}
                  disabled={testStatus === 'testing' || !hasChanges}
                  variant="outline"
                  className={`${
                    testStatus === 'passed' ? 'border-green-500 text-green-600 hover:bg-green-50' :
                    testStatus === 'failed' ? 'border-red-500 text-red-600 hover:bg-red-50' :
                    'border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {testStatus === 'testing' ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Testing...
                    </>
                  ) : (
                    'Test Connection'
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t bg-gray-50">
          <div className="flex items-center space-x-4">
            {hasChanges && (
              <span className="text-sm text-yellow-600 font-medium">
                You have unsaved changes
              </span>
            )}
          </div>

          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              onClick={handleCancel}
              className="px-6"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={!hasChanges}
              className="px-8 bg-blue-600 hover:bg-blue-700"
            >
              Save Configuration
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}