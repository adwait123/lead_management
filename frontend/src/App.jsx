import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Leads } from './pages/Leads'
import { Agents } from './pages/Agents'
import { Workflows } from './pages/Workflows'
import { Integrations } from './pages/Integrations'
import { Settings } from './pages/Settings'
import { Calendar } from './pages/Calendar'
import { Conversations } from './pages/Conversations'
import { LeadChat } from './pages/LeadChat'
import { HatchAgentWizard } from './components/wizard/HatchAgentWizard'
import { HatchAgentConfigSimple } from './components/wizard/HatchAgentConfigSimple'
import { HatchAgentEdit } from './components/wizard/HatchAgentEdit'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout><Dashboard /></Layout>} />
        <Route path="/leads" element={<Layout><Leads /></Layout>} />
        <Route path="/leads/:leadId/chat" element={<LeadChat />} />
        <Route path="/conversations" element={<Layout><Conversations /></Layout>} />
        <Route path="/agents" element={<Layout><Agents /></Layout>} />
        <Route path="/agents/new" element={<Layout><HatchAgentWizard /></Layout>} />
        <Route path="/agents/config" element={<Layout><HatchAgentConfigSimple /></Layout>} />
        <Route path="/agents/edit/:id" element={<Layout><HatchAgentEdit /></Layout>} />
        <Route path="/workflows" element={<Layout><Workflows /></Layout>} />
        <Route path="/integrations" element={<Layout><Integrations /></Layout>} />
        <Route path="/calendar" element={<Layout><Calendar /></Layout>} />
        <Route path="/settings" element={<Layout><Settings /></Layout>} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
