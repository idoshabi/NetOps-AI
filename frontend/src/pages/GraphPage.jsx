import React from 'react'
import { api } from '../api/client'
import { useApi } from '../components/useApi'
import { Loading, ErrorMsg, Panel, PageHeader, TableWrap } from '../components/ui'
import GraphView from '../components/GraphView'

export default function GraphPage() {
  const { data, error, loading } = useApi(api.graph, [])
  const risky = useApi(api.riskyPaths, [])

  return (
    <div>
      <PageHeader
        title="Network Graph"
        subtitle="Applications, VPCs, subnets, workloads, firewall rules, routes, IPAM, owners and Terraform files. Click a node to inspect it; click a legend type to focus."
      />
      <ErrorMsg error={error} />
      {loading && <Loading what="graph" />}
      {data && <GraphView graph={data} />}

      <div style={{ height: 16 }} />
      <Panel title="Risky internet → sensitive paths">
        {risky.data && risky.data.length === 0 && <p>No internet-facing paths into sensitive subnets detected.</p>}
        {risky.data && risky.data.length > 0 && (
          <TableWrap><table>
            <thead><tr><th>Firewall rule</th><th>Source</th><th>Target subnet</th><th>Risk</th></tr></thead>
            <tbody>
              {risky.data.map((p, i) => (
                <tr key={i}>
                  <td className="mono">{p.rule_name} ({p.firewall_rule})</td>
                  <td className="mono">{p.source}</td>
                  <td className="mono">{p.target_cidr}</td>
                  <td><span className={`badge ${p.risk_level}`}>{p.risk_level}</span></td>
                </tr>
              ))}
            </tbody>
          </table></TableWrap>
        )}
      </Panel>
    </div>
  )
}
