import React, { useState } from 'react';
import { Button } from '../ui/Button';

export function ToolConfigModal({ isOpen, onClose, onSave, title, icon, children, isConfigured = false, testStatus = 'not_tested' }) {
  const [hasChanges, setHasChanges] = useState(false);

  if (!isOpen) return null;

  const handleSave = () => {
    onSave();
    setHasChanges(false);
  };

  const handleCancel = () => {
    if (hasChanges) {
      if (window.confirm('You have unsaved changes. Are you sure you want to cancel?')) {
        onClose();
        setHasChanges(false);
      }
    } else {
      onClose();
    }
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
      case 'passed': return 'Test Passed';
      case 'failed': return 'Test Failed';
      case 'testing': return 'Testing...';
      default: return 'Not Tested';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b bg-gradient-to-r from-gray-50 to-blue-50">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
              {icon}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
              <div className="flex items-center space-x-3 mt-1">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  isConfigured ? 'text-green-600 bg-green-100' : 'text-yellow-600 bg-yellow-100'
                }`}>
                  {isConfigured ? 'Configured' : 'Not Configured'}
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
          {React.cloneElement(children, {
            onConfigChange: () => setHasChanges(true),
            hasChanges,
            setHasChanges
          })}
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

// Base component for tool configuration content
export function ToolConfigContent({ title, description, children, onConfigChange }) {
  return (
    <div className="space-y-8">
      {/* Description */}
      {description && (
        <div className="bg-blue-50 rounded-lg p-4">
          <p className="text-blue-800 text-sm leading-relaxed">{description}</p>
        </div>
      )}

      {/* Configuration Content */}
      <div className="space-y-6">
        {React.Children.map(children, child =>
          React.cloneElement(child, { onConfigChange })
        )}
      </div>
    </div>
  );
}

// Reusable section component for configuration forms
export function ConfigSection({ title, description, children, required = false, onConfigChange }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          {title}
          {required && <span className="text-red-500 ml-1">*</span>}
        </h3>
        {description && (
          <p className="text-gray-600 text-sm mt-1">{description}</p>
        )}
      </div>

      <div className="space-y-4">
        {React.Children.map(children, child =>
          child && React.cloneElement(child, {
            onConfigChange: onConfigChange || child.props.onConfigChange
          })
        )}
      </div>
    </div>
  );
}

// Test connection component
export function TestConnection({ onTest, testStatus, testMessage }) {
  return (
    <div className="bg-gray-50 rounded-lg p-4 border">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-medium text-gray-900">Test Configuration</h4>
          <p className="text-sm text-gray-600 mt-1">
            Verify that your configuration is working correctly
          </p>
          {testMessage && (
            <p className={`text-sm mt-2 ${
              testStatus === 'passed' ? 'text-green-600' :
              testStatus === 'failed' ? 'text-red-600' : 'text-gray-600'
            }`}>
              {testMessage}
            </p>
          )}
        </div>

        <Button
          onClick={onTest}
          disabled={testStatus === 'testing'}
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
            'Test Configuration'
          )}
        </Button>
      </div>
    </div>
  );
}