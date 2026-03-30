import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import NewCampaign from './pages/NewCampaign'
import CampaignLive from './pages/CampaignLive'
import CampaignResults from './pages/CampaignResults'
import CampaignHistory from './pages/CampaignHistory'

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg)' }}>
        <Sidebar />
        <main style={{ flex: 1, overflowY: 'auto' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/campaigns/new" element={<NewCampaign />} />
            <Route path="/campaigns/:id/live" element={<CampaignLive />} />
            <Route path="/campaigns/:id" element={<CampaignResults />} />
            <Route path="/history" element={<CampaignHistory />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
