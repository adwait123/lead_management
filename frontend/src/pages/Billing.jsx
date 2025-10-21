import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { CreditCard, Download, CheckCircle, Clock, XCircle } from 'lucide-react'

export function Billing() {
  // Mock subscription data
  const subscription = {
    plan: 'Pro Plan',
    price: '$1500',
    billing: 'monthly',
    status: 'active',
    nextBilling: 'December 20, 2024'
  }

  // Mock usage data
  const usage = {
    agents: { used: 3, limit: 25 },
    leads: { used: 45, limit: 5000 },
    callMinutes: { used: 120, limit: 2000 }
  }

  // Mock invoice data
  const invoices = [
    {
      id: 'INV-2024-001',
      date: 'Nov 20, 2024',
      amount: '$1,500.00',
      status: 'paid',
      downloadUrl: '#'
    },
    {
      id: 'INV-2024-002',
      date: 'Oct 20, 2024',
      amount: '$1,500.00',
      status: 'paid',
      downloadUrl: '#'
    },
    {
      id: 'INV-2024-003',
      date: 'Sep 20, 2024',
      amount: '$1,500.00',
      status: 'paid',
      downloadUrl: '#'
    },
    {
      id: 'INV-2024-004',
      date: 'Aug 20, 2024',
      amount: '$1,500.00',
      status: 'failed',
      downloadUrl: '#'
    }
  ]

  const getStatusIcon = (status) => {
    switch (status) {
      case 'paid':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return null
    }
  }

  const getUsagePercentage = (used, limit) => {
    return Math.round((used / limit) * 100)
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Billing & Subscription</h1>
        <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors">
          Upgrade Plan
        </button>
      </div>

      {/* Current Subscription */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <CreditCard className="h-5 w-5 mr-2" />
            Current Subscription
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">Plan</p>
              <p className="text-lg font-semibold text-gray-900">{subscription.plan}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Price</p>
              <p className="text-lg font-semibold text-gray-900">{subscription.price}/{subscription.billing}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Status</p>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                {subscription.status}
              </span>
            </div>
            <div>
              <p className="text-sm text-gray-500">Next Billing</p>
              <p className="text-lg font-semibold text-gray-900">{subscription.nextBilling}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Usage Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Usage This Month</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">AI Agents</span>
                <span className="text-sm text-gray-500">{usage.agents.used}/{usage.agents.limit}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${getUsagePercentage(usage.agents.used, usage.agents.limit)}%` }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Leads Processed</span>
                <span className="text-sm text-gray-500">{usage.leads.used}/{usage.leads.limit}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-600 h-2 rounded-full"
                  style={{ width: `${getUsagePercentage(usage.leads.used, usage.leads.limit)}%` }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Call Minutes</span>
                <span className="text-sm text-gray-500">{usage.callMinutes.used}/{usage.callMinutes.limit}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-purple-600 h-2 rounded-full"
                  style={{ width: `${getUsagePercentage(usage.callMinutes.used, usage.callMinutes.limit)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Invoice History */}
      <Card>
        <CardHeader>
          <CardTitle>Invoice History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Invoice
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {invoices.map((invoice) => (
                  <tr key={invoice.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {invoice.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {invoice.date}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {invoice.amount}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getStatusIcon(invoice.status)}
                        <span className={`ml-2 text-sm capitalize ${
                          invoice.status === 'paid' ? 'text-green-600' :
                          invoice.status === 'pending' ? 'text-yellow-600' :
                          'text-red-600'
                        }`}>
                          {invoice.status}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {invoice.status === 'paid' ? (
                        <button className="flex items-center text-blue-600 hover:text-blue-800">
                          <Download className="h-4 w-4 mr-1" />
                          Download
                        </button>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Billing Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Billing Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
              <CreditCard className="h-5 w-5 mr-2" />
              Update Payment Method
            </button>
            <button className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
              <Download className="h-5 w-5 mr-2" />
              Download All Invoices
            </button>
            <button className="flex items-center justify-center px-4 py-3 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors">
              Cancel Subscription
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}