import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api, getIdentity } from '../api/client'
import { useApi } from '../components/useApi'
import { Loading, ErrorMsg, Badge, Panel, KV, PageHeader } from '../components/ui'

export default function RequestReview() {
  const { id } = useParams()
  const nav = useNavigate()
  const { data, error, loading, reload } = useApi(() => api.getRequest(id), [id])
  const [busy, setBusy] = useState(false)
  const [actionErr, setActionErr] = useState(null)

  const act = async (fn) => {
    setBusy(true); setActionErr(null)
    try { await fn(); reload() } catch (e) { setActionErr(e) } finally { setBusy(false) }
  }
  const { role } = getIdentity()
  const approve = () => act(() => api.approveRequest(id, { approver: getIdentity().actor, role }))
  const reject = () => act(() => api.rejectRequest(id, { approver: getIdentity().actor, role, reason: 'Rejected via review screen' }))
  const genPR = () => act(async () => { const pr = await api.generatePR(id); nav(`/pull-requests/${pr.id}`) })

  if (loading) return <Loading what="request" />
  if (error) return <ErrorMsg error={error} />
  const r = data
  const p = r.policy_result || {}

  return (
    <div>
      <PageHeader title={`Request ${r.id}`} subtitle={`${r.application} · ${r.environment} · ${r.requested_cidr}`}>
        <Badge value={r.status} />
      </PageHeader>
      <ErrorMsg error={actionErr} />

      <Panel title="Request details">
        <KV data={{
          Requester: `${r.requester_name} <${r.requester_email}>`, Team: r.team,
          'Business unit': r.business_unit, VPC: r.vpc, 'Requested CIDR': r.requested_cidr,
          Region: `${r.cloud_provider} / ${r.region}`, Owner: r.owner, 'Cost center': r.cost_center,
          'Data classification': r.data_classification, 'Internet exposure': r.internet_exposure_required,
          Justification: r.business_justification,
        }} />
      </Panel>

      <Panel title={`Policy result — ${p.status?.toUpperCase()} · risk ${p.risk_level}`}>
        <div className="row" style={{ marginBottom: 8 }}>
          <Badge value={p.status} /> <Badge value={p.risk_level} kind={p.risk_level} />
        </div>
        {p.reasons?.length > 0 && <><h4>Denials</h4><ul className="clean">{p.reasons.map((x, i) => <li key={i} style={{ color: 'var(--red)' }}>{x}</li>)}</ul></>}
        {p.warnings?.length > 0 && <><h4>Warnings</h4><ul className="clean">{p.warnings.map((x, i) => <li key={i} style={{ color: 'var(--yellow)' }}>{x}</li>)}</ul></>}
        <h4>Evidence</h4><div className="mono">{(p.evidence || []).join(', ') || '—'}</div>
        <p style={{ color: 'var(--muted)' }}>{p.recommended_action}</p>
      </Panel>

      <Panel title="Required approvals">
        {r.required_approvals?.length > 0
          ? <div className="row">{r.required_approvals.map((x) => <span key={x} className="badge warning">{x} (pending)</span>)}</div>
          : <p>No outstanding approvals.</p>}
        <h4 style={{ marginTop: 14 }}>Approvals recorded</h4>
        {r.approvals?.length > 0 ? (
          <table><thead><tr><th>Approver</th><th>Role</th><th>Decision</th><th>When</th><th>Comment</th></tr></thead>
            <tbody>{r.approvals.map((a) => (
              <tr key={a.id}><td>{a.approver}</td><td>{a.role}</td><td><Badge value={a.decision} /></td>
                <td className="mono">{new Date(a.timestamp).toLocaleString()}</td><td>{a.comment}</td></tr>
            ))}</tbody></table>
        ) : <p style={{ color: 'var(--muted)' }}>None yet.</p>}
      </Panel>

      <Panel title="Actions">
        <p className="page-sub" style={{ marginBottom: 10 }}>Acting as role <strong>{role}</strong>. Switch roles in the sidebar to satisfy different approvals.</p>
        <div className="row">
          <button className="btn green" disabled={busy || r.status !== 'pending_approval'} onClick={approve}>Approve (as {role})</button>
          <button className="btn red" disabled={busy || r.status === 'rejected'} onClick={reject}>Reject</button>
          <button className="btn" disabled={busy || r.status !== 'approved'} onClick={genPR}>Generate Terraform PR</button>
        </div>
        {p.status === 'denied' && <p className="error">Policy denied — a PR cannot be generated until denials are resolved.</p>}
      </Panel>
    </div>
  )
}
