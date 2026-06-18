import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import AppHeader from './layout/AppHeader'
import IconNav from './layout/IconNav'

import TopologyPage from './pages/TopologyPage.jsx'
import Assistant from './pages/Assistant.jsx'
import ReachabilityPage from './pages/ReachabilityPage.jsx'
import DriftPage from './pages/DriftPage.jsx'
import ChangePage from './pages/ChangePage.jsx'
import RequestReview from './pages/RequestReview.jsx'
import PRPreview from './pages/PRPreview.jsx'
import Audit from './pages/Audit.jsx'

export default function App() {
  return (
    <div className="app-shell mesh-bg">
      <AppHeader />
      <div className="app-body">
        <IconNav />
        <div className="app-main">
          <Routes>
            <Route path="/" element={<TopologyPage />} />
            <Route path="/copilot" element={<div className="content-scroll"><Assistant /></div>} />
            <Route path="/reachability" element={<ReachabilityPage />} />
            <Route path="/drift" element={<DriftPage />} />
            <Route path="/change" element={<ChangePage />} />
            <Route path="/change/requests/:id" element={<div className="content-scroll"><RequestReview /></div>} />
            <Route path="/change/prs/:id" element={<div className="content-scroll"><PRPreview /></div>} />
            <Route path="/audit" element={<div className="content-scroll"><Audit /></div>} />
            {/* legacy redirects */}
            <Route path="/graph" element={<Navigate to="/" replace />} />
            <Route path="/assistant" element={<Navigate to="/copilot" replace />} />
            <Route path="/requests/:id" element={<Navigate to="/change/requests/:id" replace />} />
            <Route path="/pull-requests/:id" element={<Navigate to="/change/prs/:id" replace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </div>
  )
}
