// Integration data structure for CRMs and Lead Sources

export const integrations = {
  crms: [
    {
      id: 'service-titan',
      name: 'ServiceTitan',
      description: 'Field service management and CRM platform',
      category: 'crm',
      logoUrl: 'https://logo.clearbit.com/servicetitan.com',
      logoFallback: { color: 'bg-blue-600', text: 'ST' },
      isConnected: false,
      fields: [
        {
          name: 'apiKey',
          label: 'API Key',
          type: 'password',
          required: true,
          placeholder: 'Enter your Service Titan API key'
        },
        {
          name: 'tenantId',
          label: 'Tenant ID',
          type: 'text',
          required: true,
          placeholder: 'Enter your Tenant ID'
        },
        {
          name: 'environment',
          label: 'Environment',
          type: 'select',
          required: true,
          options: [
            { value: 'sandbox', label: 'Sandbox' },
            { value: 'production', label: 'Production' }
          ]
        }
      ]
    },
    {
      id: 'housecall-pro',
      name: 'Housecall Pro',
      description: 'Home service business management platform',
      category: 'crm',
      logoUrl: 'https://logo.clearbit.com/housecallpro.com',
      logoFallback: { color: 'bg-orange-500', text: 'HP' },
      isConnected: false,
      fields: [
        {
          name: 'apiKey',
          label: 'API Key',
          type: 'password',
          required: true,
          placeholder: 'Enter your Housecall Pro API key'
        },
        {
          name: 'companyId',
          label: 'Company ID',
          type: 'text',
          required: true,
          placeholder: 'Enter your Company ID'
        }
      ]
    },
    {
      id: 'hubspot',
      name: 'HubSpot',
      description: 'Inbound marketing and sales platform',
      category: 'crm',
      logoUrl: 'https://logo.clearbit.com/hubspot.com',
      logoFallback: { color: 'bg-orange-600', text: 'HS' },
      isConnected: false,
      fields: [
        {
          name: 'accessToken',
          label: 'Access Token',
          type: 'password',
          required: true,
          placeholder: 'Enter your HubSpot access token'
        },
        {
          name: 'portalId',
          label: 'Portal ID',
          type: 'text',
          required: true,
          placeholder: 'Enter your Portal ID'
        }
      ]
    },
    {
      id: 'salesforce',
      name: 'Salesforce',
      description: 'Cloud-based CRM and sales automation',
      category: 'crm',
      logoUrl: 'https://logo.clearbit.com/salesforce.com',
      logoFallback: { color: 'bg-blue-700', text: 'SF' },
      isConnected: false,
      fields: [
        {
          name: 'username',
          label: 'Username',
          type: 'text',
          required: true,
          placeholder: 'Enter your Salesforce username'
        },
        {
          name: 'password',
          label: 'Password',
          type: 'password',
          required: true,
          placeholder: 'Enter your password'
        },
        {
          name: 'securityToken',
          label: 'Security Token',
          type: 'password',
          required: true,
          placeholder: 'Enter your security token'
        },
        {
          name: 'instanceUrl',
          label: 'Instance URL',
          type: 'text',
          required: true,
          placeholder: 'https://your-instance.salesforce.com'
        }
      ]
    }
  ],
  leadSources: [
    {
      id: 'angie',
      name: "Angie's List",
      description: 'Home service leads and customer reviews',
      category: 'lead_source',
      logoUrl: 'https://logo.clearbit.com/angi.com',
      logoFallback: { color: 'bg-green-600', text: 'AL' },
      isConnected: false,
      fields: [
        {
          name: 'apiKey',
          label: 'API Key',
          type: 'password',
          required: true,
          placeholder: 'Enter your Angie\'s List API key'
        },
        {
          name: 'providerId',
          label: 'Provider ID',
          type: 'text',
          required: true,
          placeholder: 'Enter your Provider ID'
        }
      ]
    },
    {
      id: 'google-ads',
      name: 'Google Ads',
      description: 'Online advertising and lead generation',
      category: 'lead_source',
      logoUrl: 'https://developers.google.com/static/ads/images/ads-logo-color_240x240dp.png',
      logoFallback: { color: 'bg-red-500', text: 'GA' },
      isConnected: false,
      fields: [
        {
          name: 'clientId',
          label: 'Client ID',
          type: 'text',
          required: true,
          placeholder: 'Enter your Google Ads Client ID'
        },
        {
          name: 'clientSecret',
          label: 'Client Secret',
          type: 'password',
          required: true,
          placeholder: 'Enter your Client Secret'
        },
        {
          name: 'refreshToken',
          label: 'Refresh Token',
          type: 'password',
          required: true,
          placeholder: 'Enter your Refresh Token'
        },
        {
          name: 'developerId',
          label: 'Developer ID',
          type: 'text',
          required: true,
          placeholder: 'Enter your Developer ID'
        }
      ]
    },
    {
      id: 'yelp-ads',
      name: 'Yelp Ads',
      description: 'Local business advertising and leads',
      category: 'lead_source',
      logoUrl: 'https://logo.clearbit.com/yelp.com',
      logoFallback: { color: 'bg-red-600', text: 'YA' },
      isConnected: false,
      fields: [
        {
          name: 'apiKey',
          label: 'API Key',
          type: 'password',
          required: true,
          placeholder: 'Enter your Yelp Ads API key'
        },
        {
          name: 'businessId',
          label: 'Business ID',
          type: 'text',
          required: true,
          placeholder: 'Enter your Business ID'
        }
      ]
    },
    {
      id: 'thumbtack',
      name: 'Thumbtack Ads',
      description: 'Professional service marketplace leads',
      category: 'lead_source',
      logoUrl: 'https://logo.clearbit.com/thumbtack.com',
      logoFallback: { color: 'bg-blue-500', text: 'TA' },
      isConnected: false,
      fields: [
        {
          name: 'apiKey',
          label: 'API Key',
          type: 'password',
          required: true,
          placeholder: 'Enter your Thumbtack API key'
        },
        {
          name: 'userId',
          label: 'User ID',
          type: 'text',
          required: true,
          placeholder: 'Enter your User ID'
        }
      ]
    }
  ]
};

// Helper functions
export const getAllIntegrations = () => {
  return [...integrations.crms, ...integrations.leadSources];
};

export const getIntegrationById = (id) => {
  return getAllIntegrations().find(integration => integration.id === id);
};

export const getConnectedIntegrations = () => {
  return getAllIntegrations().filter(integration => integration.isConnected);
};

export const getIntegrationsByCategory = (category) => {
  if (category === 'crm') return integrations.crms;
  if (category === 'lead_source') return integrations.leadSources;
  return getAllIntegrations();
};