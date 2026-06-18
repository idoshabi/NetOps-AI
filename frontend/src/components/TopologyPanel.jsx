import React, { useState } from 'react'
import { api } from '../api/client'

export default function TopologyPanel({ selected, tenant, onSync }) {
  const [timeIdx, setTimeIdx] = useState(100)
  const [live, setLive] = useState(true)
  const timestamp = '2026-06-18 16:00:00Z'

  const runSync = async () => {
    await api.runDiscovery()
    onSync?.()
  }

  return (
    <div className="topology-panel">
      <div className="panel-block">
        <h3 className="panel-kicker">Inspector</h3>
        {!selected ? (
          <div className="glass-elevated inspector-empty">
            <span className="inspector-icon">↖</span>
            <p>Select a node on the topology to inspect its rules, provenance, and sync metadata.</p>
          </div>
        ) : (
          <div className="glass-elevated inspector-detail">
            <div className="inspector-head">
              <strong>{selected.label}</strong>
              <span className="badge neutral">{selected.type}</span>
            </div>
            <div className="mono inspector-id">id: {selected.id}</div>
            {Object.entries(selected.props || {}).slice(0, 8).map(([k, v]) => (
              <div key={k} className="inspector-row">
                <span className="inspector-key">{k}</span>
                <span>{String(v)}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="panel-block">
        <h3 className="panel-kicker">Incremental sync</h3>
        <p className="panel-copy">Unchanged resources produce a hash hit (no graph write); reconcile prunes anything not seen this run.</p>
        <div className="panel-actions">
          <button type="button" className="btn-ghost" onClick={runSync}>↻ Incremental sync</button>
          <button type="button" className="btn-ghost" onClick={runSync}>⌁ Reconcile</button>
        </div>
      </div>

      <div className="panel-block">
        <h3 className="panel-kicker">Time travel</h3>
        <p className="panel-copy">Relationships keep valid_from / valid_to for historical queries.</p>
        <div className="glass-elevated time-travel">
          <div className="time-slider-row">
            <span className="time-icon">◷</span>
            <input
              type="range"
              min={0}
              max={100}
              value={timeIdx}
              onChange={(e) => { setTimeIdx(Number(e.target.value)); setLive(false) }}
            />
          </div>
          <div className="time-footer">
            <span className="mono time-stamp">{timestamp}</span>
            <div className="time-toggle">
              <button type="button" className={`btn-ghost sm${!live ? ' active' : ''}`} onClick={() => setLive(false)}>Baseline</button>
              <button type="button" className={`btn-ghost sm${live ? ' active' : ''}`} onClick={() => { setLive(true); setTimeIdx(100) }}>Live</button>
            </div>
          </div>
        </div>
      </div>

      <div className="topology-tenant-label">
        <strong>{tenant}</strong>
        <span>· {live ? 'live topology' : 'baseline snapshot'}</span>
      </div>
    </div>
  )
}
