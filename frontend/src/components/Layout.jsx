import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Users,
  Bot,
  Workflow,
  Blocks,
  Calendar as CalendarIcon,
  Settings
} from 'lucide-react'

export function Layout({ children }) {
  const location = useLocation()

  const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Leads', href: '/leads', icon: Users },
    { name: 'AI Agents', href: '/agents', icon: Bot },
    { name: 'Calendar', href: '/calendar', icon: CalendarIcon },
    { name: 'Workflows', href: '/workflows', icon: Workflow },
    { name: 'Integrations', href: '/integrations', icon: Blocks },
  ]

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/'
    return location.pathname.startsWith(path)
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="flex items-center h-16 px-6 border-b border-gray-200">
          <Bot className="h-8 w-8 text-blue-600" />
          <span className="ml-2 text-xl font-bold text-gray-900">AI Lead Manager</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-2">
          {navigation.map((item) => {
            const Icon = item.icon
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`
                  flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors
                  ${isActive(item.href)
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                  }
                `}
              >
                <Icon className="h-5 w-5 mr-3" />
                {item.name}
              </Link>
            )
          })}
        </nav>

        {/* Settings */}
        <div className="px-4 pb-4">
          <Link
            to="/settings"
            className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-100 hover:text-gray-900 transition-colors"
          >
            <Settings className="h-5 w-5 mr-3" />
            Settings
          </Link>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar (optional for user profile, notifications, etc.) */}
        <header className="bg-white border-b border-gray-200 h-16 flex items-center justify-end px-6">
          <div className="text-sm text-gray-500">
            AI Lead Management System
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-8 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}