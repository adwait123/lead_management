import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { IntegrationGrid } from '../components/integrations/IntegrationGrid';
import { IntegrationModal } from '../components/integrations/IntegrationModal';
import { integrations } from '../data/integrations';

export function Integrations() {
  const [selectedIntegration, setSelectedIntegration] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleIntegrationClick = (integration) => {
    setSelectedIntegration(integration);
    setIsModalOpen(true);
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setSelectedIntegration(null);
  };

  const handleSaveConfiguration = (integrationId, configData) => {
    // In a real app, this would save to your backend
    console.log('Saving configuration for:', integrationId, configData);

    // For demo purposes, we'll just show an alert
    alert(`Configuration saved for ${selectedIntegration?.name}!`);

    // You could update the integration's isConnected status here
    // integrations.crms.find(i => i.id === integrationId).isConnected = true;
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Integrations</h1>
        <p className="text-gray-500 mt-2">Connect your favorite tools and platforms to streamline your workflow</p>
      </div>

      {/* CRM Integrations */}
      <Card>
        <CardHeader>
          <CardTitle>CRM Systems</CardTitle>
        </CardHeader>
        <CardContent>
          <IntegrationGrid
            title="Customer Relationship Management"
            description="Connect your CRM to sync leads, customers, and manage your sales pipeline"
            integrations={integrations.crms}
            onIntegrationClick={handleIntegrationClick}
          />
        </CardContent>
      </Card>

      {/* Lead Source Integrations */}
      <Card>
        <CardHeader>
          <CardTitle>Lead Sources</CardTitle>
        </CardHeader>
        <CardContent>
          <IntegrationGrid
            title="Lead Generation Platforms"
            description="Automatically capture leads from your marketing channels and advertising platforms"
            integrations={integrations.leadSources}
            onIntegrationClick={handleIntegrationClick}
          />
        </CardContent>
      </Card>

      {/* Integration Configuration Modal */}
      <IntegrationModal
        integration={selectedIntegration}
        isOpen={isModalOpen}
        onClose={handleModalClose}
        onSave={handleSaveConfiguration}
      />
    </div>
  );
}