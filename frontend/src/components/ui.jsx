// Shared presentational components.
import React from 'react'

export function Badge({ value, kind }) {
  const cls = (kind || value || 'neutral').toLowerCase()
  return <span className={`badge ${cls}`}>{String(value)}</span>
}

export function StatCard({ label, value, tone, icon }) {
  return (
    <div className={`stat-card ${tone || ''}`}>
      <div className="stat-card-top">
        {icon && <span className="stat-icon">{icon}</span>}
        <h3>{label}</h3>
      </div>
      <div className={`stat-value ${tone || ''}`}>{value}</div>
    </div>
  )
}

export function PageHeader({ title, subtitle, children }) {
  return (
    <header className="page-header">
      <div className="page-header-text">
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-sub">{subtitle}</p>}
      </div>
      {children && <div className="page-header-actions">{children}</div>}
    </header>
  )
}

export function Panel({ title, children, right, className = '' }) {
  return (
    <div className={`panel ${className}`}>
      {(title || right) && (
        <div className="panel-head">
          {title && <h2>{title}</h2>}
          {right}
        </div>
      )}
      <div className="panel-body">{children}</div>
    </div>
  )
}

export function TableWrap({ children }) {
  return <div className="table-wrap">{children}</div>
}

export function EmptyState({ title, hint }) {
  return (
    <div className="empty-state">
      <div className="empty-icon">◎</div>
      <strong>{title}</strong>
      {hint && <p>{hint}</p>}
    </div>
  )
}

export function Loading({ what = 'data' }) {
  return (
    <div className="loading-block">
      <div className="spinner" />
      <span>Loading {what}…</span>
    </div>
  )
}

export function ErrorMsg({ error }) {
  if (!error) return null
  return (
    <div className="alert alert-error">
      <span className="alert-icon">!</span>
      {error.message || String(error)}
    </div>
  )
}

export function KV({ data }) {
  return (
    <div className="kv">
      {Object.entries(data).map(([k, v]) => (
        <React.Fragment key={k}>
          <div className="k">{k}</div>
          <div>{typeof v === 'boolean' ? (v ? 'yes' : 'no') : String(v ?? '—')}</div>
        </React.Fragment>
      ))}
    </div>
  )
}
