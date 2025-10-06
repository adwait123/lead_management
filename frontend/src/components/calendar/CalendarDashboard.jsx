import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { CalendarIntegrationService } from '../../services/calendarIntegrations';

export function CalendarDashboard() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedView, setSelectedView] = useState('week');
  const [appointments, setAppointments] = useState([]);
  const [integrationStatus, setIntegrationStatus] = useState({});
  const [loading, setLoading] = useState(true);
  const [lastSync, setLastSync] = useState(null);

  // Connected integrations (simulating user's connected systems)
  const connectedIntegrations = ['google_calendar', 'servicetitan', 'jobber', 'outlook_365'];

  useEffect(() => {
    loadCalendarData();
  }, []);

  const loadCalendarData = async () => {
    setLoading(true);
    try {
      // Fetch appointments from all connected integrations
      const allAppointments = [];
      const statusData = {};

      for (const integrationId of connectedIntegrations) {
        try {
          const status = await CalendarIntegrationService.getIntegrationStatus(integrationId);
          statusData[integrationId] = status;

          if (status.connected) {
            const externalAppointments = await CalendarIntegrationService.fetchExternalAppointments(integrationId);
            allAppointments.push(...externalAppointments);
          }
        } catch (error) {
          console.error(`Failed to load data from ${integrationId}:`, error);
          statusData[integrationId] = { connected: false, error: error.message };
        }
      }

      setAppointments(allAppointments);
      setIntegrationStatus(statusData);
      setLastSync(new Date());
    } catch (error) {
      console.error('Failed to load calendar data:', error);
    } finally {
      setLoading(false);
    }
  };

  const syncAllCalendars = async () => {
    setLoading(true);
    try {
      for (const integrationId of connectedIntegrations) {
        if (integrationStatus[integrationId]?.connected) {
          await CalendarIntegrationService.performSync(integrationId);
        }
      }
      await loadCalendarData(); // Reload data after sync
    } catch (error) {
      console.error('Sync failed:', error);
    } finally {
      setLoading(false);
    }
  };

  // Get appointments for current week
  const getWeekAppointments = () => {
    const startOfWeek = new Date(currentDate);
    startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());

    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);

    return appointments.filter(apt => {
      const aptDate = new Date(apt.start);
      return aptDate >= startOfWeek && aptDate <= endOfWeek;
    });
  };

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };

  const getSourceIcon = (source) => {
    const icons = {
      google_calendar: '📅',
      servicetitan: '🚛',
      housecall_pro: '🏠',
      jobber: '⚡',
      outlook_365: '📧',
      custom_crm: '🔗'
    };
    return icons[source] || '📄';
  };

  const getSourceColor = (source) => {
    const colors = {
      google_calendar: 'bg-blue-100 text-blue-800',
      servicetitan: 'bg-orange-100 text-orange-800',
      housecall_pro: 'bg-green-100 text-green-800',
      jobber: 'bg-purple-100 text-purple-800',
      outlook_365: 'bg-indigo-100 text-indigo-800',
      custom_crm: 'bg-gray-100 text-gray-800'
    };
    return colors[source] || 'bg-gray-100 text-gray-800';
  };

  const weekAppointments = getWeekAppointments();
  const connectedCount = Object.values(integrationStatus).filter(s => s.connected).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Calendar Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Synced appointments from {connectedCount} connected platform{connectedCount !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="flex space-x-3">
          <Button
            onClick={syncAllCalendars}
            disabled={loading}
            className="flex items-center space-x-2"
          >
            <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>{loading ? 'Syncing...' : 'Sync All'}</span>
          </Button>
        </div>
      </div>

      {/* Sync Status */}
      {lastSync && (
        <Card className="border-0 shadow-sm bg-green-50">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2 text-green-800">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium">
                Last synced: {lastSync.toLocaleTimeString()} • All platforms up to date
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Integration Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {connectedIntegrations.map(integrationId => {
          const status = integrationStatus[integrationId];
          const isConnected = status?.connected;

          return (
            <Card key={integrationId} className="border-0 shadow-sm">
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="text-2xl">{getSourceIcon(integrationId)}</div>
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900 capitalize">
                      {integrationId.replace('_', ' ')}
                    </h4>
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                      <span className={`text-xs font-medium ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
                        {isConnected ? 'Connected' : 'Disconnected'}
                      </span>
                    </div>
                  </div>
                </div>
                {isConnected && status.lastSync && (
                  <p className="text-xs text-gray-500 mt-2">
                    Synced: {new Date(status.lastSync).toLocaleTimeString()}
                  </p>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="border-0 shadow-sm">
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{weekAppointments.length}</p>
                <p className="text-sm text-gray-600">This Week</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm">
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center mr-3">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {weekAppointments.filter(apt => apt.type === 'estimate').length}
                </p>
                <p className="text-sm text-gray-600">Estimates</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm">
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-yellow-100 rounded-lg flex items-center justify-center mr-3">
                <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {weekAppointments.filter(apt => apt.type === 'emergency').length}
                </p>
                <p className="text-sm text-gray-600">Emergency</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm">
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center mr-3">
                <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{connectedCount}</p>
                <p className="text-sm text-gray-600">Integrations</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Calendar View */}
      <Card className="border-0 shadow-lg">
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="text-xl font-semibold">
              Week of {currentDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
            </CardTitle>
            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  const prevWeek = new Date(currentDate);
                  prevWeek.setDate(currentDate.getDate() - 7);
                  setCurrentDate(prevWeek);
                }}
              >
                ← Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentDate(new Date())}
              >
                Today
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  const nextWeek = new Date(currentDate);
                  nextWeek.setDate(currentDate.getDate() + 7);
                  setCurrentDate(nextWeek);
                }}
              >
                Next →
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-3 text-gray-600">Loading appointments...</span>
            </div>
          ) : weekAppointments.length > 0 ? (
            <div className="space-y-4">
              {weekAppointments.map((appointment) => (
                <div
                  key={appointment.id}
                  className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  {/* Time */}
                  <div className="flex-shrink-0 w-20 text-center">
                    <div className="text-sm font-medium text-gray-900">
                      {formatDate(appointment.start)}
                    </div>
                    <div className="text-sm text-gray-600">
                      {formatTime(appointment.start)}
                    </div>
                  </div>

                  {/* Appointment Details */}
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <h4 className="font-medium text-gray-900">{appointment.title}</h4>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSourceColor(appointment.source)}`}>
                        {getSourceIcon(appointment.source)} {appointment.source.replace('_', ' ')}
                      </span>
                    </div>
                    {appointment.customer && (
                      <p className="text-sm text-gray-600">
                        {appointment.customer} • {appointment.phone}
                      </p>
                    )}
                    {appointment.address && (
                      <p className="text-sm text-gray-500">{appointment.address}</p>
                    )}
                    {appointment.technician && (
                      <p className="text-sm text-blue-600">Assigned: {appointment.technician}</p>
                    )}
                  </div>

                  {/* Type Badge */}
                  <div className="flex-shrink-0">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      appointment.type === 'emergency' ? 'bg-red-100 text-red-800' :
                      appointment.type === 'estimate' ? 'bg-blue-100 text-blue-800' :
                      appointment.type === 'installation' ? 'bg-purple-100 text-purple-800' :
                      appointment.type === 'maintenance' ? 'bg-green-100 text-green-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {appointment.type}
                    </span>
                  </div>

                  {/* Actions */}
                  <div className="flex-shrink-0">
                    <Button variant="outline" size="sm">
                      View Details
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No appointments this week</h3>
              <p className="text-gray-600">
                Appointments from your connected calendar platforms will appear here.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Sync Details */}
      <Card className="border-0 shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Integration Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(integrationStatus).map(([integrationId, status]) => (
              <div key={integrationId} className="space-y-2">
                <div className="flex items-center space-x-2">
                  <span className="text-lg">{getSourceIcon(integrationId)}</span>
                  <h4 className="font-medium capitalize">{integrationId.replace('_', ' ')}</h4>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    status.connected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {status.connected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
                {status.connected && (
                  <div className="pl-6 space-y-1 text-sm text-gray-600">
                    <p>Sync: {status.syncDirection || 'bidirectional'}</p>
                    <p>Frequency: {status.syncFrequency || 'real_time'}</p>
                    <p>Conflicts: {status.conflictResolution || 'manual_review'}</p>
                    {status.lastSync && (
                      <p>Last sync: {new Date(status.lastSync).toLocaleString()}</p>
                    )}
                  </div>
                )}
                {status.error && (
                  <p className="pl-6 text-sm text-red-600">{status.error}</p>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}