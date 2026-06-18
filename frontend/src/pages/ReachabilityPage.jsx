import React from 'react'
import { api } from '../api/client'
import { useApi } from '../components/useApi'
import { Loading, ErrorMsg, Badge, TableWrap } from '../components/ui'

export default function ReachabilityPage() {
  const risky = useApi(api.riskyPaths, [])
  const fw = useApi(api.firewallRules, [])

  return (
    <div className="content-scroll">
      <div className="content-head">
        <h2 className="content-title">Reachability</h2>
        <p className="content-sub">Path analysis, firewall rules, and risky internet → sensitive flows.</p>
      </div>

      <ErrorMsg error={risky.error || fw.error} />
      {(risky.loading || fw.loading) && <Loading what="reachability" />}

      <div className="content-section">
        <h3 className="panel-kicker">Risky internet → sensitive paths</h3>
        {risky.data && risky.data.length === 0 && (
          <div className="glass-elevated empty-card">No internet-facing paths into sensitive subnets detected.</div>
        )}
        {risky.data && risky.data.length > 0 && (
          <TableWrap>
            <table>
              <thead><tr><th>Firewall rule</th><th>Source</th><th>Target subnet</th><th>Risk</th></tr></thead>
              <tbody>
                {risky.data.map((p, i) => (
                  <tr key={i}>
                    <td className="mono">{p.rule_name} ({p.firewall_rule})</td>
                    <td className="mono">{p.source}</td>
                    <td className="mono">{p.target_cidr}</td>
                    <td><Badge value={p.risk_level} kind={p.risk_level} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableWrap>
        )}
      </div>

      <div className="content-section">
        <h3 className="panel-kicker">Firewall rules</h3>
        {fw.data && (
          <TableWrap>
            <table>
              <thead>
                <tr><th>Source</th><th>Destination</th><th>Port</th><th>Proto</th><th>Action</th><th>Owner</th><th>Risk</th><th>Explanation</th></tr>
              </thead>
              <tbody>
                {fw.data.map((f) => (
                  <tr key={f.id}>
                    <td className="mono">{f.source_cidr}</td>
                    <td className="mono">{f.destination_cidr}</td>
                    <td className="mono">{f.port}</td>
                    <td>{f.protocol}</td>
                    <td>{f.action}</td>
                    <td>{f.owner || <span className="badge high">none</span>}</td>
                    <td><Badge value={f.risk_level} kind={f.risk_level} /></td>
                    <td style={{ maxWidth: 320 }}>{f.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableWrap>
        )}
      </div>
    </div>
  )
}
