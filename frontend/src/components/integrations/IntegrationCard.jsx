import React, { useState } from 'react';
import { Button } from '../ui/Button';

export function IntegrationCard({ integration, onClick }) {
  const { name, description, logoUrl, logoFallback, isConnected } = integration;
  const [logoError, setLogoError] = useState(false);

  const handleLogoError = () => {
    setLogoError(true);
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:border-gray-300 transition-colors cursor-pointer group">
      <div className="flex items-start justify-between mb-4">
        {/* Logo */}
        <div className="w-12 h-12 rounded-lg flex items-center justify-center shrink-0 overflow-hidden">
          {!logoError && logoUrl ? (
            <img
              src={logoUrl}
              alt={`${name} logo`}
              className="w-full h-full object-contain"
              onError={handleLogoError}
            />
          ) : (
            <div className={`w-full h-full ${logoFallback.color} rounded-lg flex items-center justify-center text-white font-bold text-lg`}>
              {logoFallback.text}
            </div>
          )}
        </div>

        {/* Connection Status */}
        <div className="flex items-center">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-300'}`}></div>
          <span className={`ml-2 text-xs font-medium ${isConnected ? 'text-green-600' : 'text-gray-500'}`}>
            {isConnected ? 'Connected' : 'Not Connected'}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
          {name}
        </h3>
        <p className="text-gray-600 text-sm leading-relaxed">
          {description}
        </p>
      </div>

      {/* Action Button */}
      <Button
        onClick={(e) => {
          e.stopPropagation();
          onClick(integration);
        }}
        variant={isConnected ? "outline" : "default"}
        size="sm"
        className="w-full"
      >
        {isConnected ? 'Configure' : 'Connect'}
      </Button>
    </div>
  );
}