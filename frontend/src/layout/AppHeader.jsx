import React, { useState } from 'react'
import { api, getIdentity, setIdentity } from '../api/client'
import { useApi } from '../components/useApi'
import { IconNetwork } from '../components/icons'

const TENANTS = ['Acme Retail', 'Globex Financial', 'Initech SaaS']
const REGIONS = ['us-east-1', 'eu-west-1']
const ROLES = ['admin', 'requester', 'network_admin', 'security_reviewer', 'approver', 'auditor']

const ROLE_LABELS = {
  admin: 'Network Admin',
  requester: 'Requester',
  network_admin: 'Network Admin',
  security_reviewer: 'Security Reviewer',
  approver: 'Approver',
  auditor: 'Auditor',
}

export default function AppHeader() {
  const [tenant, setTenant] = useState(TENANTS[0])
  const [role, setRole] = useState(getIdentity().role)
  const { actor } = getIdentity()
  const graph = useApi(api.graph, [])
  const findings = useApi(api.findings, [])

  const onRole = (e) => {
    setRole(e.target.value)
    setIdentity({ role: e.target.value })
  }

  const nodes = graph.data?.stats?.node_count ?? graph.data?.nodes?.length ?? '—'
  const edges = graph.data?.stats?.edge_count ?? graph.data?.edges?.length ?? '—'
  const findingCount = findings.data?.length ?? '—'
  const initial = (actor || 'demo-user').charAt(0).toUpperCase()

  return (
    <header className="app-header glass">
      <div className="header-row">
        <div className="header-brand">
          <div className="header-logo">
            <IconNetwork size={20} stroke={2} color="#fff" />
          </div>
          <div>
            <div className="header-title-row">
              <h1 className="text-gradient">NetGraph Copilot</h1>
              <span className="demo-badge">Demo</span>
            </div>
            <p className="header-tagline">Discovery · grounded Q&amp;A · guarded change</p>
          </div>
        </div>

        <div className="tenant-tabs">
          {TENANTS.map((t) => (
            <button
              key={t}
              type="button"
              className={`tenant-tab${tenant === t ? ' active' : ''}`}
              onClick={() => setTenant(t)}
            >
              {tenant === t && <span className="tenant-dot" />}
              <span className={tenant === t ? 'tenant-active-label' : ''}>{t}</span>
            </button>
          ))}
        </div>

        <div className="header-stats">
          <div className="stat-pill"><div className="stat-pill-label">Nodes</div><div className="stat-pill-value">{nodes}</div></div>
          <div className="stat-pill"><div className="stat-pill-label">Edges</div><div className="stat-pill-value">{edges}</div></div>
          <div className="stat-pill"><div className="stat-pill-label">Findings</div><div className="stat-pill-value">{findingCount}</div></div>
        </div>

        <div className="header-right">
          <div className="region-pills">
            {REGIONS.map((r) => (
              <span key={r} className="region-pill"><span className="region-provider">aws</span><span className="region-name">:{r}</span></span>
            ))}
          </div>

          <div className="user-chip glass-subtle">
            <div className="user-avatar">{initial}</div>
            <div>
              <div className="user-name">{actor?.split('-')[0] || 'demo'}</div>
              <select className="user-role-select" value={role} onChange={onRole} title="Active role">
                {ROLES.map((r) => <option key={r} value={r}>{ROLE_LABELS[r] || r}</option>)}
              </select>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
