// Tool execution simulation system for realistic agent testing

export class ToolSimulation {
  constructor(wizardData) {
    this.wizardData = wizardData;
    this.simulationResults = new Map();
  }

  // Simulate appointment booking tool execution
  async simulateAppointmentTool(userMessage, context = {}) {
    if (!this.wizardData?.tools?.appointment?.enabled) {
      return {
        success: false,
        message: "Appointment booking tool is not enabled",
        toolUsed: false
      };
    }

    const config = this.wizardData.tools.appointment;

    // Simulate processing delay
    await this.delay(1500);

    if (!config.configured) {
      return {
        success: false,
        message: "I'd like to help you schedule an appointment, but the booking system isn't fully configured yet.",
        toolUsed: true,
        toolStatus: 'not_configured',
        details: "Calendar integration required"
      };
    }

    // Extract appointment details from message
    const appointmentType = this.extractAppointmentType(userMessage, config.appointmentTypes);
    const preferredDate = this.extractDate(userMessage);
    const timePreference = this.extractTime(userMessage);

    // Simulate calendar check
    const availableSlots = this.generateAvailableSlots(config.availabilityRules, preferredDate);

    if (availableSlots.length === 0) {
      return {
        success: false,
        message: "I don't see any available slots for your preferred time. Let me suggest some alternative times:",
        toolUsed: true,
        toolStatus: 'executed',
        details: {
          type: appointmentType,
          requestedDate: preferredDate,
          alternatives: this.generateAlternativeSlots(config.availabilityRules)
        },
        followUp: "Would any of these times work better for you?"
      };
    }

    // Successful booking simulation
    const selectedSlot = availableSlots[0];
    const confirmationId = this.generateConfirmationId();

    return {
      success: true,
      message: `Perfect! I've scheduled your ${appointmentType.name} appointment for ${selectedSlot.date} at ${selectedSlot.time}.`,
      toolUsed: true,
      toolStatus: 'executed',
      details: {
        appointmentType: appointmentType,
        scheduledDate: selectedSlot.date,
        scheduledTime: selectedSlot.time,
        confirmationId: confirmationId,
        duration: appointmentType.duration,
        calendarIntegration: config.calendarIntegration?.name
      },
      followUp: "You'll receive a confirmation email shortly. Is there anything else I can help you with?"
    };
  }

  // Simulate knowledge base search
  async simulateKnowledgeTool(userMessage, context = {}) {
    if (!this.wizardData?.tools?.knowledge?.enabled) {
      return {
        success: false,
        message: "Knowledge search is not available",
        toolUsed: false
      };
    }

    const config = this.wizardData.tools.knowledge;

    // Simulate search delay
    await this.delay(800);

    if (!config.configured) {
      return {
        success: false,
        message: "I'd like to help find that information, but our knowledge base isn't configured yet.",
        toolUsed: true,
        toolStatus: 'not_configured',
        details: "Knowledge sources required"
      };
    }

    // Simulate searching through configured sources
    const searchResults = this.simulateKnowledgeSearch(userMessage, config.sources);

    if (searchResults.length === 0) {
      return {
        success: false,
        message: "I searched our knowledge base but couldn't find specific information about that. Let me connect you with someone who can help.",
        toolUsed: true,
        toolStatus: 'executed',
        details: {
          searchQuery: this.extractSearchTerms(userMessage),
          sourcesSearched: config.sources.map(s => s.name),
          searchMethod: config.searchLogic.method
        },
        followUp: "Would you like me to transfer you to a specialist?"
      };
    }

    // Successful knowledge retrieval
    const bestResult = searchResults[0];

    return {
      success: true,
      message: this.formatKnowledgeResponse(bestResult, config.presentationFormat),
      toolUsed: true,
      toolStatus: 'executed',
      details: {
        searchQuery: this.extractSearchTerms(userMessage),
        resultsFound: searchResults.length,
        sourceUsed: bestResult.source,
        confidence: bestResult.confidence,
        searchMethod: config.searchLogic.method
      }
    };
  }

  // Simulate transfer tool execution
  async simulateTransferTool(userMessage, context = {}) {
    if (!this.wizardData?.tools?.transfer?.enabled) {
      return {
        success: false,
        message: "Transfer capability is not available",
        toolUsed: false
      };
    }

    const config = this.wizardData.tools.transfer;

    // Simulate processing delay
    await this.delay(1200);

    if (!config.configured) {
      return {
        success: false,
        message: "I'd like to transfer you to someone who can help, but our transfer system isn't configured yet.",
        toolUsed: true,
        toolStatus: 'not_configured',
        details: "Transfer teams required"
      };
    }

    // Determine appropriate team for transfer
    const targetTeam = this.determineTransferTeam(userMessage, context, config.teams);

    if (!targetTeam) {
      return {
        success: false,
        message: "I'm not sure which team would be best for your request. Let me connect you with our general support.",
        toolUsed: true,
        toolStatus: 'executed',
        details: {
          reason: "No specific team match found",
          fallbackTeam: "General Support"
        }
      };
    }

    // Check team availability
    const isAvailable = this.checkTeamAvailability(targetTeam);

    if (!isAvailable) {
      return {
        success: false,
        message: `${targetTeam.name} is currently unavailable. ${config.availabilityFallback.message}`,
        toolUsed: true,
        toolStatus: 'executed',
        details: {
          targetTeam: targetTeam.name,
          availability: "Unavailable",
          fallbackAction: config.availabilityFallback.action
        },
        followUp: "How would you prefer to proceed?"
      };
    }

    // Successful transfer simulation
    const transferMessage = config.transferMessages[targetTeam.id] ||
      `I'm connecting you with our ${targetTeam.name.toLowerCase()} who can assist you.`;

    return {
      success: true,
      message: transferMessage,
      toolUsed: true,
      toolStatus: 'executed',
      details: {
        targetTeam: targetTeam.name,
        teamMembers: targetTeam.members,
        estimatedWaitTime: "2-3 minutes",
        transferReason: this.getTransferReason(userMessage, context)
      },
      followUp: "Please hold while I connect you."
    };
  }

  // Simulate bailout tool execution
  async simulateBailoutTool(disposition, context = {}) {
    if (!this.wizardData?.tools?.bailout?.enabled) {
      return {
        success: false,
        message: "Conversation end handling is not available",
        toolUsed: false
      };
    }

    const config = this.wizardData.tools.bailout;

    // Simulate processing delay
    await this.delay(1000);

    if (!config.configured) {
      return {
        success: false,
        message: "I'm unable to properly end this conversation as the system isn't configured yet.",
        toolUsed: true,
        toolStatus: 'not_configured',
        details: "Disposition management required"
      };
    }

    // Find the disposition
    const selectedDisposition = this.findDisposition(disposition, config);

    if (!selectedDisposition) {
      return {
        success: false,
        message: "I'm having trouble processing how to end this conversation.",
        toolUsed: true,
        toolStatus: 'executed',
        details: {
          requestedDisposition: disposition,
          availableDispositions: [...config.dispositions, ...config.customDispositions.map(d => d.name)]
        }
      };
    }

    // Get the appropriate end message
    const dispositionKey = selectedDisposition.toLowerCase().replace(/[^a-z0-9]/g, '_');
    const endMessage = config.endMessages[dispositionKey] ||
      `Thank you for contacting us regarding ${selectedDisposition.toLowerCase()}.`;

    // Simulate CRM update
    const crmStatus = config.crmMapping[dispositionKey] || 'unqualified';

    return {
      success: true,
      message: endMessage,
      toolUsed: true,
      toolStatus: 'executed',
      details: {
        disposition: selectedDisposition,
        crmStatus: crmStatus,
        leadUpdated: true,
        conversationId: this.generateConversationId()
      },
      isConversationEnd: true
    };
  }

  // Helper methods for simulation

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  extractAppointmentType(message, appointmentTypes) {
    const messageLower = message.toLowerCase();

    // Check if any appointment type is mentioned
    for (const type of appointmentTypes) {
      if (messageLower.includes(type.name.toLowerCase())) {
        return type;
      }
    }

    // Default fallback based on keywords
    if (messageLower.includes('emergency') || messageLower.includes('urgent')) {
      return appointmentTypes.find(t => t.name.toLowerCase().includes('emergency')) ||
        { name: 'Emergency Service', duration: 60, color: '#DC2626' };
    }

    if (messageLower.includes('install')) {
      return appointmentTypes.find(t => t.name.toLowerCase().includes('install')) ||
        { name: 'Installation', duration: 240, color: '#10B981' };
    }

    if (messageLower.includes('repair') || messageLower.includes('fix')) {
      return appointmentTypes.find(t => t.name.toLowerCase().includes('repair')) ||
        { name: 'Repair', duration: 120, color: '#EF4444' };
    }

    // Default to consultation
    return appointmentTypes.find(t => t.name.toLowerCase().includes('consultation')) ||
      { name: 'Consultation', duration: 30, color: '#3B82F6' };
  }

  extractDate(message) {
    const today = new Date();
    const messageLower = message.toLowerCase();

    if (messageLower.includes('today')) {
      return today.toLocaleDateString();
    }

    if (messageLower.includes('tomorrow')) {
      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);
      return tomorrow.toLocaleDateString();
    }

    if (messageLower.includes('next week')) {
      const nextWeek = new Date(today);
      nextWeek.setDate(nextWeek.getDate() + 7);
      return nextWeek.toLocaleDateString();
    }

    // Default to tomorrow
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toLocaleDateString();
  }

  extractTime(message) {
    const messageLower = message.toLowerCase();

    if (messageLower.includes('morning')) return 'morning';
    if (messageLower.includes('afternoon')) return 'afternoon';
    if (messageLower.includes('evening')) return 'evening';

    return null;
  }

  generateAvailableSlots(availabilityRules, preferredDate) {
    // Simulate finding available time slots
    const slots = [
      { date: preferredDate, time: '10:00 AM' },
      { date: preferredDate, time: '2:00 PM' },
      { date: preferredDate, time: '4:00 PM' }
    ];

    // Randomly remove some slots to simulate realistic availability
    return slots.filter(() => Math.random() > 0.3);
  }

  generateAlternativeSlots(availabilityRules) {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 2);

    return [
      { date: tomorrow.toLocaleDateString(), time: '9:00 AM' },
      { date: tomorrow.toLocaleDateString(), time: '1:00 PM' },
      { date: tomorrow.toLocaleDateString(), time: '3:00 PM' }
    ];
  }

  generateConfirmationId() {
    return 'APT-' + Math.random().toString(36).substr(2, 9).toUpperCase();
  }

  simulateKnowledgeSearch(message, sources) {
    const messageLower = message.toLowerCase();
    const results = [];

    // Simulate different types of knowledge matches
    if (messageLower.includes('price') || messageLower.includes('cost')) {
      results.push({
        content: "Our service rates start at $89 for basic diagnostics, with repair costs varying based on complexity.",
        source: sources[0]?.name || "Pricing Guide",
        confidence: 0.92,
        type: "pricing"
      });
    }

    if (messageLower.includes('hours') || messageLower.includes('open')) {
      results.push({
        content: "We're open Monday through Friday 8 AM to 6 PM, Saturday 9 AM to 4 PM, and offer 24/7 emergency service.",
        source: sources[0]?.name || "Business Information",
        confidence: 0.95,
        type: "hours"
      });
    }

    if (messageLower.includes('service') || messageLower.includes('area')) {
      results.push({
        content: "We provide service throughout the metropolitan area, typically within a 25-mile radius of downtown.",
        source: sources[0]?.name || "Service Areas",
        confidence: 0.88,
        type: "service_area"
      });
    }

    return results;
  }

  formatKnowledgeResponse(result, presentationFormat) {
    switch (presentationFormat) {
      case 'direct_quote':
        return `According to our ${result.source}: "${result.content}"`;
      case 'summarized':
        return `Based on our knowledge base, ${result.content.toLowerCase()}`;
      case 'contextual':
      default:
        return `${result.content} This information comes from our ${result.source}.`;
    }
  }

  extractSearchTerms(message) {
    // Simple keyword extraction
    const words = message.toLowerCase()
      .replace(/[^\w\s]/g, '')
      .split(/\s+/)
      .filter(word => word.length > 3);

    return words.slice(0, 3).join(', ');
  }

  determineTransferTeam(message, context, teams) {
    const messageLower = message.toLowerCase();

    // Emergency keywords
    if (messageLower.includes('emergency') || messageLower.includes('urgent') || messageLower.includes('leak')) {
      return teams.find(t => t.name.toLowerCase().includes('emergency')) || teams[0];
    }

    // Technical support keywords
    if (messageLower.includes('technical') || messageLower.includes('install') || messageLower.includes('repair')) {
      return teams.find(t => t.name.toLowerCase().includes('technical') || t.name.toLowerCase().includes('support')) || teams[0];
    }

    // Sales keywords
    if (messageLower.includes('quote') || messageLower.includes('price') || messageLower.includes('buy')) {
      return teams.find(t => t.name.toLowerCase().includes('sales')) || teams[0];
    }

    // Billing keywords
    if (messageLower.includes('bill') || messageLower.includes('payment') || messageLower.includes('charge')) {
      return teams.find(t => t.name.toLowerCase().includes('billing')) || teams[0];
    }

    // Default to first available team
    return teams[0];
  }

  checkTeamAvailability(team) {
    // Simulate checking team availability based on current time and team hours
    const now = new Date();
    const currentDay = now.toLocaleDateString('en-US', { weekday: 'lowercase' });
    const currentTime = now.getHours();

    if (!team.availability || !team.availability[currentDay]) {
      return Math.random() > 0.3; // 70% chance available if no specific hours
    }

    const daySchedule = team.availability[currentDay];
    if (!daySchedule.enabled) {
      return false;
    }

    // Simple time check (would be more sophisticated in real implementation)
    const startHour = parseInt(daySchedule.start.split(':')[0]);
    const endHour = parseInt(daySchedule.end.split(':')[0]);

    if (currentTime >= startHour && currentTime <= endHour) {
      return Math.random() > 0.2; // 80% chance available during business hours
    }

    return Math.random() > 0.7; // 30% chance available outside hours
  }

  getTransferReason(message, context) {
    const messageLower = message.toLowerCase();

    if (messageLower.includes('angry') || messageLower.includes('frustrated')) {
      return "Customer escalation";
    }

    if (messageLower.includes('technical') || messageLower.includes('complex')) {
      return "Technical expertise required";
    }

    if (messageLower.includes('manager') || messageLower.includes('supervisor')) {
      return "Management request";
    }

    return "Specialized assistance needed";
  }

  findDisposition(disposition, config) {
    // Check default dispositions
    if (config.dispositions.includes(disposition)) {
      return disposition;
    }

    // Check custom dispositions
    const customDisposition = config.customDispositions.find(d => d.name === disposition);
    if (customDisposition) {
      return customDisposition.name;
    }

    // Fallback matching
    const dispositionLower = disposition.toLowerCase();

    if (dispositionLower.includes('appointment') || dispositionLower.includes('scheduled')) {
      return 'Appointment set';
    }

    if (dispositionLower.includes('transfer') || dispositionLower.includes('escalate')) {
      return 'Transfer';
    }

    if (dispositionLower.includes('success') || dispositionLower.includes('complete')) {
      return 'Success/Completed';
    }

    return 'Bailout'; // Default fallback
  }

  generateConversationId() {
    return 'CONV-' + Math.random().toString(36).substr(2, 9).toUpperCase();
  }
}

// Factory function to create tool simulation
export function createToolSimulation(wizardData) {
  return new ToolSimulation(wizardData);
}

// Individual tool simulators for easier testing
export const toolSimulators = {
  appointment: (wizardData, message, context) => {
    const sim = new ToolSimulation(wizardData);
    return sim.simulateAppointmentTool(message, context);
  },

  knowledge: (wizardData, message, context) => {
    const sim = new ToolSimulation(wizardData);
    return sim.simulateKnowledgeTool(message, context);
  },

  transfer: (wizardData, message, context) => {
    const sim = new ToolSimulation(wizardData);
    return sim.simulateTransferTool(message, context);
  },

  bailout: (wizardData, disposition, context) => {
    const sim = new ToolSimulation(wizardData);
    return sim.simulateBailoutTool(disposition, context);
  }
};