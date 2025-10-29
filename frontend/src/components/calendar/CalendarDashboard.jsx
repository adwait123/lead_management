import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Link } from 'react-router-dom';

export function CalendarDashboard() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Calendar</h1>
          <p className="text-gray-600 mt-1">
            Manage your appointments and sync with external calendar platforms
          </p>
        </div>
      </div>

      {/* Main Calendar Connection Card */}
      <Card className="border-0 shadow-lg">
        <CardContent className="p-12">
          <div className="text-center">
            {/* Calendar Icon */}
            <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-10 h-10 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>

            {/* Main Message */}
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Connect Your Calendar</h2>
            <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
              To view and manage your appointments, please connect your calendar through the integrations section.
              Once connected, all your appointments will appear here automatically.
            </p>

            {/* Action Button */}
            <Link to="/integrations">
              <Button className="px-8 py-3 text-lg">
                Go to Integrations
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Available Integrations Preview */}
      <Card className="border-0 shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Available Calendar Integrations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { name: 'Google Calendar', icon: '📅', description: 'Sync with Google Calendar' },
              { name: 'Outlook 365', icon: '📧', description: 'Sync with Microsoft Outlook' },
              { name: 'ServiceTitan', icon: '🚛', description: 'Field service management' },
              { name: 'Jobber', icon: '⚡', description: 'Home service scheduling' }
            ].map((integration) => (
              <div key={integration.name} className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors">
                <div className="flex items-center space-x-3 mb-2">
                  <span className="text-2xl">{integration.icon}</span>
                  <h4 className="font-medium text-gray-900">{integration.name}</h4>
                </div>
                <p className="text-sm text-gray-600">{integration.description}</p>
              </div>
            ))}
          </div>
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-500 mb-4">
              Connect these and more calendar platforms in the integrations section
            </p>
            <Link to="/integrations">
              <Button variant="outline">
                Browse All Integrations
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}