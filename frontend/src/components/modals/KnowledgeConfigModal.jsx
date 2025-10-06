import React, { useState } from 'react';
import { ToolConfigModal, ToolConfigContent, ConfigSection, TestConnection } from './ToolConfigModal';
import { Button } from '../ui/Button';

export function KnowledgeConfigModal({ isOpen, onClose, onSave, config = {}, onConfigChange }) {
  const [knowledgeConfig, setKnowledgeConfig] = useState({
    sources: config?.sources || [
      {
        id: 'company_website',
        name: 'Company Website',
        type: 'website',
        url: 'https://yourcompany.com',
        sections: ['About', 'Services', 'Pricing', 'FAQ'],
        lastUpdated: new Date().toISOString(),
        status: 'active'
      }
    ],
    searchLogic: config?.searchLogic || {
      method: 'semantic', // 'semantic', 'keyword', 'hybrid'
      matchThreshold: 0.7,
      maxResults: 3,
      includeContext: true,
      fallbackToGeneral: true
    },
    presentationFormat: config?.presentationFormat || 'contextual', // 'contextual', 'direct_quote', 'summarized'
    updateRules: config?.updateRules || {
      autoSync: true,
      syncFrequency: 'daily', // 'hourly', 'daily', 'weekly', 'manual'
      notifyOnChanges: true,
      retainHistory: true
    },
    accessControl: config?.accessControl || {
      requireAuth: false,
      allowedDomains: [],
      restrictedContent: []
    },
    testStatus: config?.testStatus || 'not_tested'
  });

  const [newSource, setNewSource] = useState({
    name: '',
    type: 'website',
    url: '',
    description: ''
  });

  // Source types
  const sourceTypes = [
    { value: 'website', label: 'Website/URL', icon: '🌐', description: 'Crawl and index web pages' },
    { value: 'document', label: 'Document', icon: '📄', description: 'Upload PDF, Word, or text files' },
    { value: 'database', label: 'Database', icon: '🗄️', description: 'Connect to existing database' },
    { value: 'api', label: 'API Endpoint', icon: '🔗', description: 'Real-time data from API' },
    { value: 'faq', label: 'FAQ System', icon: '❓', description: 'Structured Q&A knowledge base' },
    { value: 'manual', label: 'Manual Entry', icon: '✏️', description: 'Manually entered information' }
  ];

  // Search methods
  const searchMethods = [
    { value: 'semantic', label: 'Semantic Search', description: 'AI-powered meaning-based search' },
    { value: 'keyword', label: 'Keyword Search', description: 'Traditional keyword matching' },
    { value: 'hybrid', label: 'Hybrid Search', description: 'Combines semantic and keyword search' }
  ];

  // Presentation formats
  const presentationFormats = [
    { value: 'contextual', label: 'Contextual', description: 'Naturally woven into conversation' },
    { value: 'direct_quote', label: 'Direct Quote', description: 'Exact text with attribution' },
    { value: 'summarized', label: 'Summarized', description: 'AI-generated summary' }
  ];

  // Sync frequencies
  const syncFrequencies = [
    { value: 'hourly', label: 'Every Hour' },
    { value: 'daily', label: 'Daily' },
    { value: 'weekly', label: 'Weekly' },
    { value: 'manual', label: 'Manual Only' }
  ];

  const updateConfig = (updates) => {
    const newConfig = { ...knowledgeConfig, ...updates };
    setKnowledgeConfig(newConfig);
    onConfigChange && onConfigChange(newConfig);
  };

  const addKnowledgeSource = () => {
    if (!newSource.name.trim()) return;

    const source = {
      ...newSource,
      id: newSource.name.toLowerCase().replace(/[^a-z0-9]/g, '_'),
      lastUpdated: new Date().toISOString(),
      status: 'pending',
      sections: [],
      indexedItems: 0
    };

    const updatedSources = [...knowledgeConfig.sources, source];
    updateConfig({ sources: updatedSources });

    setNewSource({ name: '', type: 'website', url: '', description: '' });
  };

  const removeKnowledgeSource = (sourceId) => {
    const updatedSources = knowledgeConfig.sources.filter(source => source.id !== sourceId);
    updateConfig({ sources: updatedSources });
  };

  const updateSourceStatus = (sourceId, status) => {
    const updatedSources = knowledgeConfig.sources.map(source => {
      if (source.id === sourceId) {
        return {
          ...source,
          status,
          lastUpdated: new Date().toISOString()
        };
      }
      return source;
    });
    updateConfig({ sources: updatedSources });
  };

  const testKnowledgeSearch = async () => {
    updateConfig({ testStatus: 'testing' });

    // Simulate testing knowledge search
    setTimeout(() => {
      const success = Math.random() > 0.2; // 80% success rate for demo
      updateConfig({
        testStatus: success ? 'passed' : 'failed',
        testMessage: success
          ? 'Knowledge search tested successfully. All sources are accessible and search is working correctly.'
          : 'Test failed. Please check your knowledge sources and search configuration.'
      });
    }, 3000);
  };

  const getSourceIcon = (type) => {
    const sourceType = sourceTypes.find(st => st.value === type);
    return sourceType ? sourceType.icon : '📄';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100';
      case 'pending': return 'text-yellow-600 bg-yellow-100';
      case 'error': return 'text-red-600 bg-red-100';
      case 'syncing': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const handleSave = () => {
    const isConfigured = knowledgeConfig.sources.length > 0;
    onSave({
      ...knowledgeConfig,
      enabled: true,
      configured: isConfigured
    });
  };

  return (
    <ToolConfigModal
      isOpen={isOpen}
      onClose={onClose}
      onSave={handleSave}
      title="Knowledge Base Configuration"
      icon={
        <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      }
      isConfigured={knowledgeConfig.sources.length > 0}
      testStatus={knowledgeConfig.testStatus}
    >
      <ToolConfigContent
        description="Configure knowledge sources that your AI agent can search through to provide accurate, up-to-date information to customers. Connect websites, documents, databases, and more."
      >
        {/* Knowledge Sources */}
        <ConfigSection
          title="Knowledge Sources"
          description="Add and manage the sources your agent can search through"
          required
        >
          {/* Current Sources */}
          {knowledgeConfig.sources.length > 0 && (
            <div className="space-y-3 mb-6">
              <h4 className="font-medium text-gray-900">Configured Sources ({knowledgeConfig.sources.length})</h4>
              {knowledgeConfig.sources.map((source) => (
                <div key={source.id} className="border rounded-lg p-4 bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="text-2xl mr-3">{getSourceIcon(source.type)}</div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <h5 className="font-medium text-gray-900">{source.name}</h5>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(source.status)}`}>
                            {source.status}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">{source.url || source.description}</p>
                        <div className="flex items-center space-x-4 mt-1">
                          <span className="text-xs text-gray-500">
                            Type: {sourceTypes.find(st => st.value === source.type)?.label}
                          </span>
                          {source.indexedItems && (
                            <span className="text-xs text-gray-500">
                              {source.indexedItems} items indexed
                            </span>
                          )}
                          <span className="text-xs text-gray-500">
                            Updated: {new Date(source.lastUpdated).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {source.status === 'pending' && (
                        <Button
                          size="sm"
                          onClick={() => updateSourceStatus(source.id, 'active')}
                          className="bg-blue-600 hover:bg-blue-700 text-xs"
                        >
                          Activate
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => removeKnowledgeSource(source.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
                      >
                        Remove
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Add New Source */}
          <div className="bg-purple-50 rounded-lg p-6">
            <h4 className="font-medium text-gray-900 mb-4">Add Knowledge Source</h4>

            {/* Source Type Selection */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Source Type</label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {sourceTypes.map((type) => (
                  <div
                    key={type.value}
                    onClick={() => setNewSource({...newSource, type: type.value})}
                    className={`border-2 rounded-lg p-3 cursor-pointer transition-all ${
                      newSource.type === type.value
                        ? 'border-purple-500 bg-purple-50'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center">
                      <div className="text-xl mr-3">{type.icon}</div>
                      <div>
                        <h5 className="font-medium text-gray-900 text-sm">{type.label}</h5>
                        <p className="text-xs text-gray-600">{type.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Source Name</label>
                <input
                  type="text"
                  value={newSource.name}
                  onChange={(e) => setNewSource({...newSource, name: e.target.value})}
                  placeholder="e.g., Company FAQ"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {newSource.type === 'website' ? 'URL' :
                   newSource.type === 'api' ? 'API Endpoint' :
                   newSource.type === 'database' ? 'Connection String' : 'Source Location'}
                </label>
                <input
                  type="text"
                  value={newSource.url}
                  onChange={(e) => setNewSource({...newSource, url: e.target.value})}
                  placeholder={
                    newSource.type === 'website' ? 'https://example.com' :
                    newSource.type === 'api' ? 'https://api.example.com/knowledge' :
                    newSource.type === 'database' ? 'Database connection details' :
                    'Source location or identifier'
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <input
                  type="text"
                  value={newSource.description}
                  onChange={(e) => setNewSource({...newSource, description: e.target.value})}
                  placeholder="Brief description of this knowledge source"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
            </div>
            <Button
              onClick={addKnowledgeSource}
              disabled={!newSource.name.trim()}
              className="mt-4 bg-purple-600 hover:bg-purple-700"
            >
              Add Knowledge Source
            </Button>
          </div>
        </ConfigSection>

        {/* Search Configuration */}
        <ConfigSection
          title="Search Configuration"
          description="Configure how the agent searches through your knowledge sources"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Search Method</label>
              <div className="space-y-2">
                {searchMethods.map((method) => (
                  <label key={method.value} className="flex items-start">
                    <input
                      type="radio"
                      name="searchMethod"
                      value={method.value}
                      checked={knowledgeConfig.searchLogic.method === method.value}
                      onChange={(e) => updateConfig({
                        searchLogic: {
                          ...knowledgeConfig.searchLogic,
                          method: e.target.value
                        }
                      })}
                      className="mt-1 mr-3"
                    />
                    <div>
                      <div className="font-medium text-gray-900">{method.label}</div>
                      <div className="text-sm text-gray-600">{method.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Match Threshold ({knowledgeConfig.searchLogic.matchThreshold})
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="1"
                  step="0.1"
                  value={knowledgeConfig.searchLogic.matchThreshold}
                  onChange={(e) => updateConfig({
                    searchLogic: {
                      ...knowledgeConfig.searchLogic,
                      matchThreshold: parseFloat(e.target.value)
                    }
                  })}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Less strict</span>
                  <span>More strict</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Max Results</label>
                <input
                  type="number"
                  value={knowledgeConfig.searchLogic.maxResults}
                  onChange={(e) => updateConfig({
                    searchLogic: {
                      ...knowledgeConfig.searchLogic,
                      maxResults: parseInt(e.target.value)
                    }
                  })}
                  min="1"
                  max="10"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                />
              </div>

              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={knowledgeConfig.searchLogic.includeContext}
                    onChange={(e) => updateConfig({
                      searchLogic: {
                        ...knowledgeConfig.searchLogic,
                        includeContext: e.target.checked
                      }
                    })}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium text-gray-700">Include context around matches</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={knowledgeConfig.searchLogic.fallbackToGeneral}
                    onChange={(e) => updateConfig({
                      searchLogic: {
                        ...knowledgeConfig.searchLogic,
                        fallbackToGeneral: e.target.checked
                      }
                    })}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium text-gray-700">Fallback to general knowledge if no matches</span>
                </label>
              </div>
            </div>
          </div>
        </ConfigSection>

        {/* Presentation Format */}
        <ConfigSection
          title="Presentation Format"
          description="Choose how knowledge is presented to customers"
        >
          <div className="space-y-2">
            {presentationFormats.map((format) => (
              <label key={format.value} className="flex items-start">
                <input
                  type="radio"
                  name="presentationFormat"
                  value={format.value}
                  checked={knowledgeConfig.presentationFormat === format.value}
                  onChange={(e) => updateConfig({ presentationFormat: e.target.value })}
                  className="mt-1 mr-3"
                />
                <div>
                  <div className="font-medium text-gray-900">{format.label}</div>
                  <div className="text-sm text-gray-600">{format.description}</div>
                </div>
              </label>
            ))}
          </div>
        </ConfigSection>

        {/* Update Rules */}
        <ConfigSection
          title="Update & Sync Rules"
          description="Configure how knowledge sources are kept up-to-date"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Sync Frequency</label>
              <select
                value={knowledgeConfig.updateRules.syncFrequency}
                onChange={(e) => updateConfig({
                  updateRules: {
                    ...knowledgeConfig.updateRules,
                    syncFrequency: e.target.value
                  }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              >
                {syncFrequencies.map((freq) => (
                  <option key={freq.value} value={freq.value}>
                    {freq.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={knowledgeConfig.updateRules.autoSync}
                  onChange={(e) => updateConfig({
                    updateRules: {
                      ...knowledgeConfig.updateRules,
                      autoSync: e.target.checked
                    }
                  })}
                  className="mr-2"
                />
                <span className="text-sm font-medium text-gray-700">Auto-sync sources</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={knowledgeConfig.updateRules.notifyOnChanges}
                  onChange={(e) => updateConfig({
                    updateRules: {
                      ...knowledgeConfig.updateRules,
                      notifyOnChanges: e.target.checked
                    }
                  })}
                  className="mr-2"
                />
                <span className="text-sm font-medium text-gray-700">Notify on content changes</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={knowledgeConfig.updateRules.retainHistory}
                  onChange={(e) => updateConfig({
                    updateRules: {
                      ...knowledgeConfig.updateRules,
                      retainHistory: e.target.checked
                    }
                  })}
                  className="mr-2"
                />
                <span className="text-sm font-medium text-gray-700">Retain version history</span>
              </label>
            </div>
          </div>
        </ConfigSection>

        {/* Test Configuration */}
        <TestConnection
          onTest={testKnowledgeSearch}
          testStatus={knowledgeConfig.testStatus}
          testMessage={knowledgeConfig.testMessage}
        />
      </ToolConfigContent>
    </ToolConfigModal>
  );
}