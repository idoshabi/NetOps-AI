import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import { api, getIdentity } from '../api/client'
import { useApi } from '../components/useApi'
import { Loading, ErrorMsg, Badge, Panel } from '../components/ui'

function Diff({ text }) {
  return (
    <pre>{text.split('\n').map((l, i) => (
      <div key={i} className={l.startsWith('+') && !l.startsWith('+++') ? 'diff-add' : ''}>{l}</div>
    ))}</pre>
  )
}

export default function PRPreview() {
  const { id } = useParams()
  const { data, error, loading, reload } = useApi(() => api.getPR(id), [id])
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)
  const { role, actor } = getIdentity()

  const act = async (fn) => { setBusy(true); setErr(null); try { await fn(); reload() } catch (e) { setErr(e) } finally { setBusy(false) } }
  const approve = () => act(() => api.approvePR(id, { approver: actor, role }))
  const reject = () => act(() => api.rejectPR(id, { approver: actor, role, reason: 'Rejected at PR review' }))

  if (loading) return <Loading what="pull request" />
  if (error) return <ErrorMsg error={error} />
  const pr = data
  const p = pr.policy_result || {}

  return (
    <div>
      <div className="row between">
        <h1 className="page-title">{pr.title}</h1>
        <Badge value={pr.status} />
      </div>
      <p className="page-sub mono">{pr.branch}</p>
      <ErrorMsg error={err} />

      <Panel title="Reviewers & approvals">
        <div className="row">{(pr.reviewers || []).map((r) => <span key={r} className="badge neutral">{r}</span>)}</div>
        <p style={{ color: 'var(--muted)', marginTop: 8 }}>Required approval roles: {(pr.approval_requirements || []).join(', ') || 'none'}</p>
      </Panel>

      <Panel title="Description"><pre style={{ whiteSpace: 'pre-wrap' }}>{pr.description}</pre></Panel>

      <Panel title="Terraform diff"><Diff text={pr.terraform_diff || ''} /></Panel>

      <Panel title={`Policy summary — ${p.status?.toUpperCase()} · risk ${p.risk_level}`}>
        {p.warnings?.length > 0 && <ul className="clean">{p.warnings.map((w, i) => <li key={i} style={{ color: 'var(--yellow)' }}>{w}</li>)}</ul>}
        <p>{pr.risk_summary}</p>
      </Panel>

      <Panel title="Rollback plan"><p>{pr.rollback_notes}</p></Panel>
      <Panel title="Test plan"><pre style={{ whiteSpace: 'pre-wrap' }}>{pr.test_plan}</pre></Panel>

      <Panel title="Approve / reject (human-in-the-loop)">
        <p className="page-sub" style={{ marginBottom: 10 }}>Acting as <strong>{role}</strong>. NetGraph Copilot never approves or merges its own PRs.</p>
        <div className="row">
          <button className="btn green" disabled={busy || pr.status !== 'open'} onClick={approve}>Approve PR</button>
          <button className="btn red" disabled={busy || pr.status !== 'open'} onClick={reject}>Reject PR</button>
        </div>
        <p className="mono" style={{ color: 'var(--muted)', marginTop: 10 }}>Audit event: {pr.audit_event_id}</p>
      </Panel>
    </div>
  )
}
