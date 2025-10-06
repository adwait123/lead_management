import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Leads } from './pages/Leads'
import { Agents } from './pages/Agents'
import { Workflows } from './pages/Workflows'
import { Integrations } from './pages/Integrations'
import { Settings } from './pages/Settings'
import { Calendar } from './pages/Calendar'
import { HatchAgentWizard } from './components/wizard/HatchAgentWizard'
import { HatchAgentConfigSimple } from './components/wizard/HatchAgentConfigSimple'
import { HatchAgentEdit } from './components/wizard/HatchAgentEdit'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/leads" element={<Leads />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/agents/new" element={<HatchAgentWizard />} />
          <Route path="/agents/config" element={<HatchAgentConfigSimple />} />
          <Route path="/agents/edit/:id" element={<HatchAgentEdit />} />
          <Route path="/workflows" element={<Workflows />} />
          <Route path="/integrations" element={<Integrations />} />
          <Route path="/calendar" element={<Calendar />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
