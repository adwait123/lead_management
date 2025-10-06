/**
 * Mock API services for external calendar integrations
 * Simulates real-world calendar system connections like Google Calendar, ServiceTitan, etc.
 */

// Mock API delay to simulate real network calls
const apiDelay = (ms = 1000) => new Promise(resolve => setTimeout(resolve, ms));

// Mock appointment data from external calendars
const mockExternalAppointments = {
  google_calendar: [
    {
      id: 'gc_001',
      title: 'Team Meeting',
      start: '2024-01-15T09:00:00Z',
      end: '2024-01-15T10:00:00Z',
      type: 'meeting',
      source: 'google_calendar',
      editable: false
    },
    {
      id: 'gc_002',
      title: 'HVAC Consultation - Smith Residence',
      start: '2024-01-15T14:00:00Z',
      end: '2024-01-15T15:00:00Z',
      type: 'consultation',
      source: 'google_calendar',
      customer: 'John Smith',
      phone: '(555) 123-4567',
      address: '123 Oak Street, Dallas, TX 75201',
      editable: true
    }
  ],
  servicetitan: [
    {
      id: 'st_001',
      title: 'Plumbing Repair - Johnson Home',
      start: '2024-01-15T10:30:00Z',
      end: '2024-01-15T12:30:00Z',
      type: 'repair',
      source: 'servicetitan',
      customer: 'Sarah Johnson',
      phone: '(555) 987-6543',
      address: '456 Pine Avenue, Plano, TX 75023',
      technician: 'Tom Wilson',
      jobNumber: 'ST-2024-001',
      editable: true
    },
    {
      id: 'st_002',
      title: 'Electrical Installation - Davis Property',
      start: '2024-01-16T09:00:00Z',
      end: '2024-01-16T13:00:00Z',
      type: 'installation',
      source: 'servicetitan',
      customer: 'Mike Davis',
      phone: '(555) 456-7890',
      address: '789 Elm Drive, McKinney, TX 75070',
      technician: 'Carlos Rodriguez',
      jobNumber: 'ST-2024-002',
      editable: true
    }
  ],
  housecall_pro: [
    {
      id: 'hcp_001',
      title: 'Emergency Water Heater Repair',
      start: '2024-01-15T16:00:00Z',
      end: '2024-01-15T18:30:00Z',
      type: 'emergency',
      source: 'housecall_pro',
      customer: 'Lisa Wilson',
      phone: '(555) 321-0987',
      address: '321 Maple Court, Frisco, TX 75034',
      priority: 'urgent',
      jobId: 'HCP-2024-001',
      editable: true
    }
  ],
  jobber: [
    {
      id: 'jb_001',
      title: 'Routine HVAC Maintenance',
      start: '2024-01-16T08:00:00Z',
      end: '2024-01-16T09:30:00Z',
      type: 'maintenance',
      source: 'jobber',
      customer: 'Robert Martinez',
      phone: '(555) 333-4444',
      address: '654 Cedar Lane, Allen, TX 75013',
      recurring: true,
      workOrderId: 'JB-WO-001',
      editable: true
    }
  ],
  outlook_365: [
    {
      id: 'o365_001',
      title: 'Client Consultation Call',
      start: '2024-01-15T11:00:00Z',
      end: '2024-01-15T11:30:00Z',
      type: 'meeting',
      source: 'outlook_365',
      isTeamsMeeting: true,
      meetingLink: 'https://teams.microsoft.com/l/meetup-join/...',
      editable: false
    }
  ]
};

// Mock integration status for different platforms
const mockIntegrationStatus = {
  google_calendar: {
    connected: true,
    lastSync: new Date('2024-01-15T08:30:00Z'),
    syncDirection: 'bidirectional',
    syncFrequency: 'real_time',
    conflictResolution: 'calendar_priority',
    accountEmail: 'business@acmehomeservices.com',
    calendarName: 'Business Calendar'
  },
  servicetitan: {
    connected: true,
    lastSync: new Date('2024-01-15T08:25:00Z'),
    syncDirection: 'bidirectional',
    syncFrequency: 'every_5_minutes',
    conflictResolution: 'agent_priority',
    companyId: 'ACME-123',
    locationId: 'LOC-001'
  },
  housecall_pro: {
    connected: false,
    lastSync: null,
    error: 'Authentication expired'
  },
  jobber: {
    connected: true,
    lastSync: new Date('2024-01-15T08:20:00Z'),
    syncDirection: 'to_calendar',
    syncFrequency: 'every_15_minutes',
    conflictResolution: 'manual_review',
    companyId: 'acme-home-services'
  },
  outlook_365: {
    connected: true,
    lastSync: new Date('2024-01-15T08:35:00Z'),
    syncDirection: 'from_calendar',
    syncFrequency: 'real_time',
    conflictResolution: 'calendar_priority',
    tenantId: 'tenant-123',
    mailboxes: ['business@acmehomeservices.com']
  },
  custom_crm: {
    connected: false,
    lastSync: null,
    requiresConfiguration: true
  }
};

/**
 * Calendar Integration API Service
 */
export class CalendarIntegrationService {

  /**
   * Test connection to a calendar platform
   */
  static async testConnection(integrationId, credentials = {}) {
    await apiDelay(2000); // Simulate API call

    // Simulate different connection scenarios
    const scenarios = {
      google_calendar: { success: true, message: 'Successfully connected to Google Calendar' },
      servicetitan: { success: true, message: 'Connected to ServiceTitan API' },
      housecall_pro: { success: false, error: 'Invalid API key provided' },
      jobber: { success: true, message: 'Jobber integration active' },
      outlook_365: { success: true, message: 'Office 365 authentication successful' },
      custom_crm: { success: false, error: 'API endpoint configuration required' }
    };

    const result = scenarios[integrationId] || { success: false, error: 'Unknown integration' };

    if (!result.success) {
      throw new Error(result.error);
    }

    return result;
  }

  /**
   * Get integration status and configuration
   */
  static async getIntegrationStatus(integrationId) {
    await apiDelay(500);
    return mockIntegrationStatus[integrationId] || { connected: false };
  }

  /**
   * Fetch appointments from external calendar
   */
  static async fetchExternalAppointments(integrationId, dateRange = {}) {
    await apiDelay(1000);

    if (!mockIntegrationStatus[integrationId]?.connected) {
      throw new Error(`${integrationId} is not connected`);
    }

    return mockExternalAppointments[integrationId] || [];
  }

  /**
   * Create appointment in external calendar
   */
  static async createExternalAppointment(integrationId, appointmentData) {
    await apiDelay(1500);

    if (!mockIntegrationStatus[integrationId]?.connected) {
      throw new Error(`${integrationId} is not connected`);
    }

    // Simulate appointment creation
    const newAppointment = {
      id: `${integrationId}_${Date.now()}`,
      ...appointmentData,
      source: integrationId,
      createdAt: new Date().toISOString(),
      syncStatus: 'synced'
    };

    // Add to mock data
    if (!mockExternalAppointments[integrationId]) {
      mockExternalAppointments[integrationId] = [];
    }
    mockExternalAppointments[integrationId].push(newAppointment);

    return newAppointment;
  }

  /**
   * Update appointment in external calendar
   */
  static async updateExternalAppointment(integrationId, appointmentId, updates) {
    await apiDelay(1200);

    if (!mockIntegrationStatus[integrationId]?.connected) {
      throw new Error(`${integrationId} is not connected`);
    }

    const appointments = mockExternalAppointments[integrationId] || [];
    const index = appointments.findIndex(apt => apt.id === appointmentId);

    if (index === -1) {
      throw new Error('Appointment not found');
    }

    // Update appointment
    appointments[index] = {
      ...appointments[index],
      ...updates,
      updatedAt: new Date().toISOString(),
      syncStatus: 'synced'
    };

    return appointments[index];
  }

  /**
   * Delete appointment from external calendar
   */
  static async deleteExternalAppointment(integrationId, appointmentId) {
    await apiDelay(800);

    if (!mockIntegrationStatus[integrationId]?.connected) {
      throw new Error(`${integrationId} is not connected`);
    }

    const appointments = mockExternalAppointments[integrationId] || [];
    const index = appointments.findIndex(apt => apt.id === appointmentId);

    if (index === -1) {
      throw new Error('Appointment not found');
    }

    // Remove appointment
    appointments.splice(index, 1);

    return { success: true, message: 'Appointment deleted successfully' };
  }

  /**
   * Get available time slots from external calendar
   */
  static async getAvailableTimeSlots(integrationId, date, duration = 60) {
    await apiDelay(1000);

    if (!mockIntegrationStatus[integrationId]?.connected) {
      throw new Error(`${integrationId} is not connected`);
    }

    // Mock available time slots (9 AM to 5 PM, excluding existing appointments)
    const timeSlots = [];
    const startHour = 9;
    const endHour = 17;

    for (let hour = startHour; hour < endHour; hour++) {
      for (let minute = 0; minute < 60; minute += duration) {
        if (hour === endHour - 1 && minute + duration > 60) break;

        const slotTime = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
        timeSlots.push({
          time: slotTime,
          available: Math.random() > 0.3, // 70% chance of being available
          duration: duration
        });
      }
    }

    return timeSlots;
  }

  /**
   * Check for scheduling conflicts
   */
  static async checkConflicts(integrationId, proposedAppointment) {
    await apiDelay(800);

    if (!mockIntegrationStatus[integrationId]?.connected) {
      throw new Error(`${integrationId} is not connected`);
    }

    const existingAppointments = mockExternalAppointments[integrationId] || [];
    const conflicts = [];

    // Simple conflict detection
    for (const existing of existingAppointments) {
      const proposedStart = new Date(proposedAppointment.start);
      const proposedEnd = new Date(proposedAppointment.end);
      const existingStart = new Date(existing.start);
      const existingEnd = new Date(existing.end);

      // Check for overlap
      if (proposedStart < existingEnd && proposedEnd > existingStart) {
        conflicts.push({
          conflictingAppointment: existing,
          overlapType: 'time_conflict',
          resolution: mockIntegrationStatus[integrationId].conflictResolution
        });
      }
    }

    return {
      hasConflicts: conflicts.length > 0,
      conflicts: conflicts,
      recommendations: conflicts.length > 0 ? [
        'Consider moving appointment 30 minutes later',
        'Check if existing appointment can be rescheduled',
        'Assign to different technician if available'
      ] : []
    };
  }

  /**
   * Sync data between AI agent and external calendar
   */
  static async performSync(integrationId, syncDirection = 'bidirectional') {
    await apiDelay(2000);

    if (!mockIntegrationStatus[integrationId]?.connected) {
      throw new Error(`${integrationId} is not connected`);
    }

    const syncResults = {
      lastSync: new Date().toISOString(),
      direction: syncDirection,
      appointmentsUpdated: Math.floor(Math.random() * 5),
      appointmentsCreated: Math.floor(Math.random() * 3),
      conflicts: Math.floor(Math.random() * 2),
      errors: []
    };

    // Update last sync time
    mockIntegrationStatus[integrationId].lastSync = new Date();

    return syncResults;
  }

  /**
   * Get integration configuration options
   */
  static async getConfigurationOptions(integrationId) {
    await apiDelay(500);

    const configurations = {
      google_calendar: {
        calendars: [
          { id: 'primary', name: 'Business Calendar', selected: true },
          { id: 'appointments', name: 'Appointments', selected: false },
          { id: 'team', name: 'Team Schedule', selected: false }
        ],
        syncOptions: ['events', 'tasks', 'reminders'],
        permissions: ['read', 'write', 'delete']
      },
      servicetitan: {
        locations: [
          { id: 'loc_001', name: 'Main Office - Dallas', selected: true },
          { id: 'loc_002', name: 'Branch Office - Plano', selected: false }
        ],
        jobTypes: ['estimate', 'repair', 'installation', 'maintenance', 'emergency'],
        technicians: [
          { id: 'tech_001', name: 'Tom Wilson', specialties: ['plumbing'] },
          { id: 'tech_002', name: 'Carlos Rodriguez', specialties: ['hvac', 'electrical'] }
        ]
      },
      housecall_pro: {
        services: ['plumbing', 'hvac', 'electrical', 'appliance_repair'],
        teams: [
          { id: 'team_001', name: 'Plumbing Team' },
          { id: 'team_002', name: 'HVAC Team' }
        ],
        automations: ['confirmation_emails', 'reminder_texts', 'follow_up_surveys']
      },
      jobber: {
        clients: [
          { id: 'client_001', name: 'Residential Customers', type: 'residential' },
          { id: 'client_002', name: 'Commercial Accounts', type: 'commercial' }
        ],
        scheduleOptions: ['optimize_routes', 'buffer_time', 'travel_allowance'],
        notifications: ['staff', 'clients', 'managers']
      },
      outlook_365: {
        mailboxes: [
          { id: 'mb_001', email: 'business@acmehomeservices.com', selected: true },
          { id: 'mb_002', email: 'dispatch@acmehomeservices.com', selected: false }
        ],
        meetingOptions: ['teams_integration', 'room_booking', 'external_attendees'],
        sharing: ['calendar_delegation', 'shared_calendars', 'public_folders']
      },
      custom_crm: {
        endpoints: [
          { name: 'Get Appointments', url: '/api/appointments', method: 'GET' },
          { name: 'Create Appointment', url: '/api/appointments', method: 'POST' },
          { name: 'Update Appointment', url: '/api/appointments/{id}', method: 'PUT' }
        ],
        authentication: ['api_key', 'oauth2', 'basic_auth'],
        webhooks: ['appointment_created', 'appointment_updated', 'appointment_cancelled']
      }
    };

    return configurations[integrationId] || {};
  }
}

/**
 * Mock webhook events from external calendars
 */
export class CalendarWebhookService {

  static mockWebhookEvents = [
    {
      id: 'webhook_001',
      source: 'google_calendar',
      event: 'appointment_created',
      timestamp: new Date('2024-01-15T10:30:00Z'),
      data: {
        appointmentId: 'gc_003',
        customer: 'Jennifer Clark',
        service: 'HVAC Consultation',
        scheduledTime: '2024-01-16T14:00:00Z'
      }
    },
    {
      id: 'webhook_002',
      source: 'servicetitan',
      event: 'appointment_updated',
      timestamp: new Date('2024-01-15T11:15:00Z'),
      data: {
        appointmentId: 'st_001',
        changes: { technician: 'Mike Rodriguez', estimatedDuration: 180 }
      }
    }
  ];

  /**
   * Simulate receiving webhook events
   */
  static async getRecentWebhookEvents(integrationId, since = null) {
    await apiDelay(300);

    const sinceDate = since ? new Date(since) : new Date(Date.now() - 24 * 60 * 60 * 1000);

    return this.mockWebhookEvents.filter(event =>
      event.source === integrationId &&
      new Date(event.timestamp) > sinceDate
    );
  }
}

export default CalendarIntegrationService;