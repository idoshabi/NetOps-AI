import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import Requests from './Requests'
import PullRequests from './PullRequests'
import RequestForm from './RequestForm'

const TABS = [
  { id: 'requests', label: 'Requests' },
  { id: 'prs', label: 'Pull requests' },
  { id: 'new', label: 'New request' },
]

export default function ChangePage() {
  const [tab, setTab] = useState('requests')

  return (
    <div className="content-scroll">
      <div className="content-head row between">
        <div>
          <h2 className="content-title">Change</h2>
          <p className="content-sub">Subnet requests, policy validation, and guarded Terraform PRs.</p>
        </div>
        <Link to="/change/new" className="btn" onClick={(e) => { e.preventDefault(); setTab('new') }}>New request</Link>
      </div>

      <div className="sub-tabs">
        {TABS.map((t) => (
          <button key={t.id} type="button" className={`sub-tab${tab === t.id ? ' active' : ''}`} onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'requests' && <Requests embedded />}
      {tab === 'prs' && <PullRequests embedded />}
      {tab === 'new' && <RequestForm embedded />}
    </div>
  )
}
