import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Plus, Search, Filter, Eye, Phone, Mail, Building2, Calendar, Clock, User, MessageCircle } from 'lucide-react'
import { leadsAPI } from '../lib/api.js'

export function Leads() {
  const navigate = useNavigate()
  const [leads, setLeads] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [page, setPage] = useState(1)
  const [pagination, setPagination] = useState({})
  const [selectedLead, setSelectedLead] = useState(null)
  const [showLeadDetail, setShowLeadDetail] = useState(false)

  const fetchLeads = async () => {
    try {
      setLoading(true)
      const params = {
        page,
        per_page: 10,
        ...(search && { search }),
        ...(statusFilter && { status: statusFilter }),
        ...(sourceFilter && { source: sourceFilter })
      }

      const response = await leadsAPI.getAll(params)
      setLeads(response.data.leads)
      setPagination({
        total: response.data.total,
        page: response.data.page,
        per_page: response.data.per_page,
        total_pages: response.data.total_pages
      })
    } catch (err) {
      setError('Failed to fetch leads')
      console.error('Error fetching leads:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLeads()
  }, [page, search, statusFilter, sourceFilter])

  const handleSearch = (e) => {
    setSearch(e.target.value)
    setPage(1) // Reset to first page when searching
  }

  const handleStatusFilter = (e) => {
    setStatusFilter(e.target.value)
    setPage(1)
  }

  const handleSourceFilter = (e) => {
    setSourceFilter(e.target.value)
    setPage(1)
  }

  const viewLeadDetail = async (leadId) => {
    try {
      const response = await leadsAPI.getById(leadId)
      setSelectedLead(response.data)
      setShowLeadDetail(true)
    } catch (err) {
      console.error('Error fetching lead details:', err)
    }
  }

  const getStatusBadge = (status) => {
    const statusColors = {
      new: 'bg-blue-100 text-blue-800',
      contacted: 'bg-yellow-100 text-yellow-800',
      qualified: 'bg-purple-100 text-purple-800',
      won: 'bg-green-100 text-green-800',
      lost: 'bg-red-100 text-red-800'
    }

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Leads</h1>
          <p className="text-gray-500 mt-2">Manage and track your leads</p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Add Lead
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <input
                  type="text"
                  placeholder="Search leads by name, email, or company..."
                  value={search}
                  onChange={handleSearch}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <select
                value={statusFilter}
                onChange={handleStatusFilter}
                className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Status</option>
                <option value="new">New</option>
                <option value="contacted">Contacted</option>
                <option value="qualified">Qualified</option>
                <option value="won">Won</option>
                <option value="lost">Lost</option>
              </select>
              <select
                value={sourceFilter}
                onChange={handleSourceFilter}
                className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Sources</option>
                <option value="torkin">Torkin</option>
                <option value="Facebook Ads">Facebook Ads</option>
                <option value="Google Ads">Google Ads</option>
                <option value="Website">Website</option>
                <option value="Referral">Referral</option>
                <option value="LinkedIn">LinkedIn</option>
                <option value="Email Campaign">Email Campaign</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Leads Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Leads ({pagination.total || 0})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-gray-500 mt-2">Loading leads...</p>
            </div>
          ) : error ? (
            <div className="text-center py-12 text-red-500">
              {error}
            </div>
          ) : leads.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              No leads found matching your criteria
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 font-medium text-gray-900">Lead</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-900">Company</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-900">Status</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-900">Source</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-900">Created</th>
                      <th className="text-left py-3 px-4 font-medium text-gray-900">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {leads.map((lead) => (
                      <tr key={lead.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3 px-4">
                          <div>
                            <div className="font-medium text-gray-900">{lead.name || `${lead.first_name} ${lead.last_name}`}</div>
                            <div className="text-sm text-gray-500">{lead.email}</div>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="text-gray-900">{lead.company}</div>
                          <div className="text-sm text-gray-500">{lead.service_requested}</div>
                        </td>
                        <td className="py-3 px-4">
                          {getStatusBadge(lead.status)}
                        </td>
                        <td className="py-3 px-4 text-gray-900">
                          {lead.source}
                        </td>
                        <td className="py-3 px-4 text-gray-900">
                          {formatDate(lead.created_at)}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => viewLeadDetail(lead.id)}
                            >
                              <Eye className="h-4 w-4 mr-1" />
                              View
                            </Button>
                            {lead.external_id && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => navigate(`/leads/${lead.id}/chat`)}
                                className="bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100"
                              >
                                <MessageCircle className="h-4 w-4 mr-1" />
                                Chat
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {pagination.total_pages > 1 && (
                <div className="flex items-center justify-between mt-6">
                  <div className="text-sm text-gray-500">
                    Showing {((pagination.page - 1) * pagination.per_page) + 1} to{' '}
                    {Math.min(pagination.page * pagination.per_page, pagination.total)} of{' '}
                    {pagination.total} results
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={pagination.page <= 1}
                    >
                      Previous
                    </Button>
                    <span className="px-3 py-1 text-sm text-gray-900">
                      Page {pagination.page} of {pagination.total_pages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(p => Math.min(pagination.total_pages, p + 1))}
                      disabled={pagination.page >= pagination.total_pages}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Lead Detail Modal */}
      {showLeadDetail && selectedLead && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">{selectedLead.name || `${selectedLead.first_name} ${selectedLead.last_name}`}</h2>
                  <p className="text-gray-500">{selectedLead.company}</p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowLeadDetail(false)}
                >
                  Close
                </Button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Contact Info */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Contact Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-gray-400" />
                    <span className="text-gray-900">{selectedLead.email}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-gray-400" />
                    <span className="text-gray-900">{selectedLead.phone}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-gray-400" />
                    <span className="text-gray-900">{selectedLead.company}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-gray-400" />
                    <span className="text-gray-900">Created {formatDate(selectedLead.created_at)}</span>
                  </div>
                </div>
              </div>

              {/* Status and Source */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Lead Details</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <span className="text-sm text-gray-500">Status</span>
                    <div className="mt-1">{getStatusBadge(selectedLead.status)}</div>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">Source</span>
                    <div className="mt-1 text-gray-900">{selectedLead.source}</div>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">Service Requested</span>
                    <div className="mt-1 text-gray-900">{selectedLead.service_requested}</div>
                  </div>
                </div>
              </div>

              {/* Notes */}
              {selectedLead.notes && selectedLead.notes.length > 0 && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Notes</h3>
                  <div className="space-y-3">
                    {selectedLead.notes.map((note) => (
                      <div key={note.id} className="bg-gray-50 p-3 rounded-md">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-900">{note.author}</span>
                          <span className="text-sm text-gray-500">
                            {formatDate(note.timestamp)}
                          </span>
                        </div>
                        <p className="text-gray-700">{note.content}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Interaction History */}
              {selectedLead.interaction_history && selectedLead.interaction_history.length > 0 && (
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Interaction History</h3>
                  <div className="space-y-3">
                    {selectedLead.interaction_history.map((interaction) => (
                      <div key={interaction.id} className="bg-blue-50 p-3 rounded-md">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-blue-900">
                              {interaction.type.replace('_', ' ').toUpperCase()}
                            </span>
                            <span className="text-sm text-blue-700">by {interaction.agent_name}</span>
                          </div>
                          <span className="text-sm text-blue-600">
                            {formatDate(interaction.timestamp)}
                          </span>
                        </div>
                        <p className="text-blue-800">{interaction.content}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="border-t border-gray-200 pt-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {selectedLead.external_id && (
                    <Button
                      className="w-full bg-blue-600 hover:bg-blue-700"
                      onClick={() => {
                        setShowLeadDetail(false)
                        navigate(`/leads/${selectedLead.id}/chat`)
                      }}
                    >
                      <MessageCircle className="h-4 w-4 mr-2" />
                      Start Chat
                    </Button>
                  )}

                  {selectedLead.phone && (
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() => window.open(`tel:${selectedLead.phone}`)}
                    >
                      <Phone className="h-4 w-4 mr-2" />
                      Call Lead
                    </Button>
                  )}

                  {selectedLead.email && (
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() => window.open(`mailto:${selectedLead.email}`)}
                    >
                      <Mail className="h-4 w-4 mr-2" />
                      Email Lead
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}