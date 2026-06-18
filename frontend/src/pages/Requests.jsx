import React from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useApi } from '../components/useApi'
import { Loading, ErrorMsg, Badge, PageHeader, TableWrap } from '../components/ui'

export default function Requests({ embedded = false }) {
  const { data, error, loading } = useApi(api.listRequests, [])
  return (
    <div>
      {!embedded && (
        <PageHeader title="Subnet Requests" subtitle="All requests with policy status and workflow state." />
      )}
      <ErrorMsg error={error} />
      {loading && <Loading what="requests" />}
      {data && (
        <TableWrap><table>
          <thead><tr><th>ID</th><th>CIDR</th><th>App</th><th>Env</th><th>Requester</th><th>Risk</th><th>Status</th><th></th></tr></thead>
          <tbody>
            {data.map((r) => (
              <tr key={r.id}>
                <td className="mono">{r.id}</td>
                <td className="mono">{r.requested_cidr}</td>
                <td>{r.application}</td>
                <td>{r.environment}</td>
                <td>{r.requester_name}</td>
                <td>{r.policy_result?.risk_level ? <Badge value={r.policy_result.risk_level} kind={r.policy_result.risk_level} /> : '—'}</td>
                <td><Badge value={r.status} /></td>
                <td><Link to={embedded ? `/change/requests/${r.id}` : `/requests/${r.id}`}>review →</Link></td>
              </tr>
            ))}
          </tbody>
        </table></TableWrap>
      )}
    </div>
  )
}
