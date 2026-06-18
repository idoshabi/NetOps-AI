import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { Panel, ErrorMsg, PageHeader } from '../components/ui'

const DEFAULTS = {
  requester_name: 'Dana Whitfield', requester_email: 'dana.whitfield@acme.example',
  team: 'HR Platform Team', application: 'HR Portal', business_unit: 'HR',
  environment: 'dev', requested_cidr: '10.42.18.0/24', vpc: 'vpc-hr-dev-use1',
  cloud_provider: 'aws', region: 'us-east-1',
  business_justification: 'New private subnet for HR Portal dev microservices.',
  data_classification: 'internal', internet_exposure_required: false,
  expected_traffic_pattern: 'east-west', cost_center: 'HR-2042',
  owner: 'HR Platform Team', technical_owner: 'Dana Whitfield',
}

function PolicyResult({ result }) {
  if (!result) return null
  return (
    <Panel title={`Policy preview — ${result.status?.toUpperCase()} (risk ${result.risk_level})`}>
      <div className="row"><span className={`badge ${result.status}`}>{result.status}</span>
        <span className={`badge ${result.risk_level}`}>{result.risk_level}</span></div>
      {result.reasons?.length > 0 && (<><h4>Denials</h4><ul className="clean">{result.reasons.map((r, i) => <li key={i} style={{ color: 'var(--red)' }}>{r}</li>)}</ul></>)}
      {result.warnings?.length > 0 && (<><h4>Warnings</h4><ul className="clean">{result.warnings.map((r, i) => <li key={i} style={{ color: 'var(--yellow)' }}>{r}</li>)}</ul></>)}
      <h4>Required approvals</h4><div className="row">{(result.required_approvals || []).map((r) => <span key={r} className="badge neutral">{r}</span>)}</div>
      {result.evidence?.length > 0 && (<><h4>Evidence</h4><div className="mono">{result.evidence.join(', ')}</div></>)}
      <p style={{ marginTop: 10, color: 'var(--muted)' }}>{result.recommended_action}</p>
    </Panel>
  )
}

export default function RequestForm({ embedded = false }) {
  const [form, setForm] = useState(DEFAULTS)
  const [policy, setPolicy] = useState(null)
  const [error, setError] = useState(null)
  const nav = useNavigate()

  const set = (k) => (e) => {
    const v = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm({ ...form, [k]: v })
  }

  const preview = async () => {
    try { setError(null); setPolicy(await api.evaluatePolicy(form)) }
    catch (e) { setError(e) }
  }
  const submit = async () => {
    try {
      setError(null)
      const req = await api.createRequest(form)
      await api.validateRequest(req.id)
      nav(embedded ? `/change/requests/${req.id}` : `/requests/${req.id}`)
    } catch (e) { setError(e) }
  }

  const fields = [
    ['requester_name', 'Requester name'], ['requester_email', 'Requester email'],
    ['team', 'Team'], ['application', 'Application'], ['business_unit', 'Business unit'],
    ['requested_cidr', 'Requested CIDR'], ['vpc', 'VPC / VNet'], ['region', 'Region'],
    ['cost_center', 'Cost center'], ['owner', 'Owner'], ['technical_owner', 'Technical owner'],
    ['expected_traffic_pattern', 'Expected traffic'],
  ]

  return (
    <div>
      {!embedded ? (
        <PageHeader
          title="New Subnet Request"
          subtitle="Validate against policy before submitting. Try CIDR 10.42.10.128/25 to see an overlap denial."
        />
      ) : null}
      <ErrorMsg error={error} />
      <Panel>
        <div className="form-grid">
          {fields.map(([k, label]) => (
            <div className="field" key={k}><label>{label}</label>
              <input value={form[k]} onChange={set(k)} /></div>
          ))}
          <div className="field"><label>Environment</label>
            <select value={form.environment} onChange={set('environment')}>
              <option>dev</option><option>staging</option><option>prod</option>
            </select></div>
          <div className="field"><label>Cloud provider</label>
            <select value={form.cloud_provider} onChange={set('cloud_provider')}>
              <option>aws</option><option>azure</option><option>gcp</option>
            </select></div>
          <div className="field"><label>Data classification</label>
            <select value={form.data_classification} onChange={set('data_classification')}>
              <option>internal</option><option>confidential</option><option>regulated</option><option>public</option>
            </select></div>
          <div className="field"><label>Internet exposure required</label>
            <div className="row"><input type="checkbox" style={{ width: 'auto' }} checked={form.internet_exposure_required} onChange={set('internet_exposure_required')} /> <span>{form.internet_exposure_required ? 'yes' : 'no'}</span></div></div>
          <div className="field full"><label>Business justification</label>
            <textarea rows={2} value={form.business_justification} onChange={set('business_justification')} /></div>
        </div>
        <div className="row" style={{ marginTop: 14 }}>
          <button className="btn secondary" onClick={preview}>Preview policy</button>
          <button className="btn" onClick={submit}>Submit request</button>
        </div>
      </Panel>
      <PolicyResult result={policy} />
    </div>
  )
}
