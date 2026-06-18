import React from 'react'
import { api } from '../api/client'
import { useApi } from '../components/useApi'
import { Loading, ErrorMsg, PageHeader, TableWrap } from '../components/ui'

export default function Firewall() {
  const { data, error, loading } = useApi(api.firewallRules, [])
  return (
    <div>
      <PageHeader
        title="Firewall Rules"
        subtitle="North-south and east-west rules with risk classification and explanations."
      />
      <ErrorMsg error={error} />
      {loading && <Loading what="firewall rules" />}
      {data && (
        <TableWrap>
          <table>
            <thead>
              <tr><th>Source</th><th>Destination</th><th>Port</th><th>Proto</th><th>Action</th><th>Owner</th><th>Risk</th><th>Explanation</th></tr>
            </thead>
            <tbody>
              {data.map((f) => (
                <tr key={f.id}>
                  <td className="mono">{f.source_cidr}</td>
                  <td className="mono">{f.destination_cidr}</td>
                  <td className="mono">{f.port}</td>
                  <td>{f.protocol}</td>
                  <td>{f.action}</td>
                  <td>{f.owner || <span className="badge high">none</span>}</td>
                  <td><span className={`badge ${f.risk_level}`}>{f.risk_level}</span></td>
                  <td style={{ maxWidth: 320 }}>{f.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableWrap>
      )}
    </div>
  )
}
