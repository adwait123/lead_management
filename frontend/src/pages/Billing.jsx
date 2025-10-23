import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { CreditCard, Download, CheckCircle, Clock, XCircle, Check, Star, Zap, Shield, Users } from 'lucide-react'

export function Billing() {
  const [currentPlan, setCurrentPlan] = useState('pro')
  const [showPaymentModal, setShowPaymentModal] = useState(false)
  const [showPlanModal, setShowPlanModal] = useState(false)
  const [cardForm, setCardForm] = useState({
    number: '**** **** **** 4242',
    expiry: '12/25',
    cvc: '***',
    name: 'John Doe'
  })

  // Pricing plans
  const plans = {
    pro: {
      name: 'Professional',
      price: 499,
      billing: 'monthly',
      features: [
        'Up to 50 AI Agents',
        '10,000 Leads per month',
        '5,000 Call minutes',
        'Advanced Analytics',
        'Priority Support',
        'Custom Integrations'
      ],
      usageLimits: {
        agents: 50,
        leads: 10000,
        callMinutes: 5000
      }
    },
    enterprise: {
      name: 'Enterprise',
      price: 999,
      billing: 'monthly',
      features: [
        'Unlimited AI Agents',
        '50,000 Leads per month',
        '20,000 Call minutes',
        'Advanced Analytics',
        'Dedicated Support',
        'Custom Integrations',
        'White-label Options',
        'Advanced Security'
      ],
      usageLimits: {
        agents: 999,
        leads: 50000,
        callMinutes: 20000
      }
    }
  }

  // Current usage (mock data)
  const usage = {
    agents: { used: 23, limit: plans[currentPlan].usageLimits.agents },
    leads: { used: 3420, limit: plans[currentPlan].usageLimits.leads },
    callMinutes: { used: 1240, limit: plans[currentPlan].usageLimits.callMinutes }
  }

  // Mock invoice data
  const invoices = [
    {
      id: 'INV-2024-001',
      date: 'Nov 20, 2024',
      amount: '$499.00',
      status: 'paid',
      downloadUrl: '#'
    },
    {
      id: 'INV-2024-002',
      date: 'Oct 20, 2024',
      amount: '$499.00',
      status: 'paid',
      downloadUrl: '#'
    },
    {
      id: 'INV-2024-003',
      date: 'Sep 20, 2024',
      amount: '$499.00',
      status: 'paid',
      downloadUrl: '#'
    },
    {
      id: 'INV-2024-004',
      date: 'Aug 20, 2024',
      amount: '$499.00',
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

  const handleUpgradePlan = (planKey) => {
    setCurrentPlan(planKey)
    setShowPlanModal(false)
    // Mock success - in real app would call Stripe
    alert(`Upgraded to ${plans[planKey].name} plan!`)
  }

  const handleUpdatePayment = () => {
    setShowPaymentModal(false)
    // Mock success - in real app would call Stripe
    alert('Payment method updated successfully!')
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Billing & Subscription</h1>
          <p className="text-gray-500 mt-2">Manage your subscription and payment methods</p>
        </div>
        <Button onClick={() => setShowPlanModal(true)} className="bg-blue-600 hover:bg-blue-700">
          <Zap className="h-4 w-4 mr-2" />
          Change Plan
        </Button>
      </div>

      {/* Current Plan Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Star className="h-5 w-5 mr-2 text-blue-600" />
              Current Plan: {plans[currentPlan].name}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between mb-6">
              <div>
                <p className="text-3xl font-bold text-gray-900">${plans[currentPlan].price}</p>
                <p className="text-gray-500">per month</p>
              </div>
              <div className="text-right">
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                  <CheckCircle className="h-4 w-4 mr-1" />
                  Active
                </span>
                <p className="text-sm text-gray-500 mt-1">Next billing: Dec 20, 2024</p>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {plans[currentPlan].features.slice(0, 6).map((feature, index) => (
                <div key={index} className="flex items-center text-sm">
                  <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                  <span className="text-gray-700">{feature}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Payment Method */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <CreditCard className="h-5 w-5 mr-2" />
              Payment Method
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-4 text-white mb-4">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <p className="text-sm opacity-90">VISA</p>
                  <p className="text-lg font-mono">{cardForm.number}</p>
                </div>
                <div className="text-right text-sm">
                  <p className="opacity-90">EXPIRES</p>
                  <p className="font-mono">{cardForm.expiry}</p>
                </div>
              </div>
              <p className="text-sm font-medium">{cardForm.name}</p>
            </div>
            <Button
              variant="outline"
              onClick={() => setShowPaymentModal(true)}
              className="w-full"
            >
              Update Payment Method
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Usage Metrics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Users className="h-5 w-5 mr-2" />
            Usage This Month
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg">
              <div className="flex justify-between items-center mb-3">
                <span className="text-sm font-medium text-blue-900">AI Agents</span>
                <span className="text-sm text-blue-700 font-mono">{usage.agents.used.toLocaleString()}/{usage.agents.limit.toLocaleString()}</span>
              </div>
              <div className="w-full bg-blue-200 rounded-full h-2 mb-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${getUsagePercentage(usage.agents.used, usage.agents.limit)}%` }}
                ></div>
              </div>
              <p className="text-xs text-blue-600">{getUsagePercentage(usage.agents.used, usage.agents.limit)}% used</p>
            </div>

            <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg">
              <div className="flex justify-between items-center mb-3">
                <span className="text-sm font-medium text-green-900">Leads Processed</span>
                <span className="text-sm text-green-700 font-mono">{usage.leads.used.toLocaleString()}/{usage.leads.limit.toLocaleString()}</span>
              </div>
              <div className="w-full bg-green-200 rounded-full h-2 mb-2">
                <div
                  className="bg-green-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${getUsagePercentage(usage.leads.used, usage.leads.limit)}%` }}
                ></div>
              </div>
              <p className="text-xs text-green-600">{getUsagePercentage(usage.leads.used, usage.leads.limit)}% used</p>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg">
              <div className="flex justify-between items-center mb-3">
                <span className="text-sm font-medium text-purple-900">Call Minutes</span>
                <span className="text-sm text-purple-700 font-mono">{usage.callMinutes.used.toLocaleString()}/{usage.callMinutes.limit.toLocaleString()}</span>
              </div>
              <div className="w-full bg-purple-200 rounded-full h-2 mb-2">
                <div
                  className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${getUsagePercentage(usage.callMinutes.used, usage.callMinutes.limit)}%` }}
                ></div>
              </div>
              <p className="text-xs text-purple-600">{getUsagePercentage(usage.callMinutes.used, usage.callMinutes.limit)}% used</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Invoice History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Download className="h-5 w-5 mr-2" />
            Invoice History
          </CardTitle>
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
                  <tr key={invoice.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {invoice.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {invoice.date}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-mono">
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
                        <button className="flex items-center text-blue-600 hover:text-blue-800 transition-colors">
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

      {/* Plan Selection Modal */}
      {showPlanModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Choose Your Plan</h2>
                <button
                  onClick={() => setShowPlanModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {Object.entries(plans).map(([key, plan]) => (
                  <div
                    key={key}
                    className={`border-2 rounded-lg p-6 transition-all ${
                      currentPlan === key
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-blue-300'
                    }`}
                  >
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="text-xl font-bold text-gray-900">{plan.name}</h3>
                      {currentPlan === key && (
                        <span className="bg-blue-100 text-blue-800 text-sm px-2 py-1 rounded">
                          Current
                        </span>
                      )}
                    </div>

                    <div className="mb-6">
                      <span className="text-4xl font-bold text-gray-900">${plan.price}</span>
                      <span className="text-gray-500 ml-2">/{plan.billing}</span>
                    </div>

                    <ul className="space-y-3 mb-6">
                      {plan.features.map((feature, index) => (
                        <li key={index} className="flex items-center text-sm">
                          <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                          {feature}
                        </li>
                      ))}
                    </ul>

                    <Button
                      onClick={() => handleUpgradePlan(key)}
                      className={`w-full ${
                        currentPlan === key
                          ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
                          : 'bg-blue-600 hover:bg-blue-700 text-white'
                      }`}
                      disabled={currentPlan === key}
                    >
                      {currentPlan === key ? 'Current Plan' : `Switch to ${plan.name}`}
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Payment Method Modal */}
      {showPaymentModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-900">Update Payment Method</h2>
                <button
                  onClick={() => setShowPaymentModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Card Number
                  </label>
                  <input
                    type="text"
                    placeholder="4242 4242 4242 4242"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Expiry Date
                    </label>
                    <input
                      type="text"
                      placeholder="MM/YY"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      CVC
                    </label>
                    <input
                      type="text"
                      placeholder="123"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Cardholder Name
                  </label>
                  <input
                    type="text"
                    placeholder="John Doe"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div className="flex items-center pt-4">
                  <Shield className="h-5 w-5 text-green-500 mr-2" />
                  <span className="text-sm text-gray-600">
                    Your payment information is encrypted and secure
                  </span>
                </div>

                <div className="flex gap-3 pt-4">
                  <Button
                    variant="outline"
                    onClick={() => setShowPaymentModal(false)}
                    className="flex-1"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleUpdatePayment}
                    className="flex-1 bg-blue-600 hover:bg-blue-700"
                  >
                    Update Payment Method
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}