import React from 'react'
import Dashboard from './Dashboard'
import Subnets from './Subnets'

export default function DriftPage() {
  return (
    <div className="content-scroll">
      <div className="content-head">
        <h2 className="content-title">Drift &amp; posture</h2>
        <p className="content-sub">Discovery posture, inventory drift signals, and subnet coverage.</p>
      </div>
      <Dashboard embedded />
      <div style={{ height: 24 }} />
      <Subnets embedded />
    </div>
  )
}
