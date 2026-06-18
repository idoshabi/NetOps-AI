import React from 'react'
import { api } from '../api/client'
import { useApi } from '../components/useApi'
import { StatCard, Panel, Loading, ErrorMsg, Badge, PageHeader, TableWrap } from '../components/ui'

export default function Dashboard({ embedded = false }) {
  const { data, error, loading, reload } = useApi(api.dashboard, [])

  const runDiscovery = async () => { await api.runDiscovery(); reload() }

  return (
    <div>
      {!embedded ? (
        <PageHeader
          title="Dashboard"
          subtitle="Live posture across cloud, IPAM, firewall, CMDB and Terraform sources."
        >
          <button className="btn secondary" onClick={runDiscovery}>Re-run discovery</button>
        </PageHeader>
      ) : (
        <div className="row between" style={{ marginBottom: 16 }}>
          <h3 className="panel-kicker" style={{ margin: 0 }}>Posture overview</h3>
          <button type="button" className="btn-ghost" onClick={runDiscovery}>↻ Re-run discovery</button>
        </div>
      )}

      {!embedded && (
        <div className="hero-strip">
          <p>
            <strong>NetGraph Copilot</strong> maps your network, surfaces risk, and helps you propose safe Terraform changes — always with human approval.
          </p>
        </div>
      )}

      <ErrorMsg error={error} />
      {loading && <Loading what="dashboard" />}
      {data && (
        <>
          <div className="grid cards" style={{ marginBottom: 24 }}>
            <StatCard label="Total assets" value={data.total_assets} icon="◉" />
            <StatCard label="Subnets" value={data.total_subnets} icon="▦" />
            <StatCard label="VPCs / VNets" value={data.total_vpcs} icon="⬡" />
            <StatCard label="Applications" value={data.total_applications} icon="◫" />
            <StatCard label="Unknown assets" value={data.unknown_assets} tone={data.unknown_assets ? 'warn' : ''} icon="?" />
            <StatCard label="Missing owner tags" value={data.missing_owner_tags} tone={data.missing_owner_tags ? 'warn' : ''} icon="◎" />
            <StatCard label="Internet-facing prod" value={data.internet_facing_prod} tone={data.internet_facing_prod ? 'bad' : 'good'} icon="⛨" />
            <StatCard label="High-risk FW rules" value={data.high_risk_firewall_rules} tone={data.high_risk_firewall_rules ? 'bad' : 'good'} icon="!" />
            <StatCard label="Pending requests" value={data.pending_requests} tone={data.pending_requests ? 'warn' : ''} icon="☰" />
            <StatCard label="Policy-failed requests" value={data.policy_failed_requests} tone={data.policy_failed_requests ? 'bad' : ''} icon="✕" />
          </div>

          <Panel title="Risk findings by severity">
            <div className="severity-row">
              {Object.entries(data.findings_by_severity).map(([sev, n]) => (
                <div key={sev} className="severity-chip">
                  <Badge value={sev} kind={sev} />
                  <span className="severity-count">{n}</span>
                </div>
              ))}
            </div>
          </Panel>

          {!embedded && (
            <Panel title="Recent audit events">
              <TableWrap>
                <table>
                  <thead><tr><th>Time</th><th>Actor</th><th>Role</th><th>Action</th><th>Target</th><th>Result</th></tr></thead>
                  <tbody>
                    {data.recent_audit_events.map((e) => (
                      <tr key={e.id}>
                        <td className="mono">{new Date(e.timestamp).toLocaleTimeString()}</td>
                        <td>{e.actor}</td>
                        <td>{e.role}</td>
                        <td className="mono">{e.action}</td>
                        <td className="mono">{e.target_id || '—'}</td>
                        <td><Badge value={e.result} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </TableWrap>
            </Panel>
          )}
        </>
      )}
    </div>
  )
}
