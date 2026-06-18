import React from 'react'
import { api } from '../api/client'
import { useApi } from '../components/useApi'
import { Loading, ErrorMsg, Badge, PageHeader, TableWrap } from '../components/ui'

export default function Audit() {
  const { data, error, loading } = useApi(api.audit, [])
  return (
    <div>
      <PageHeader
        title="Audit Log"
        subtitle="Every discovery run, policy evaluation, approval, PR and Copilot action is recorded. Requires auditor / admin / reviewer role."
      />
      <ErrorMsg error={error} />
      {loading && <Loading what="audit events" />}
      {data && (
        <TableWrap>
          <table>
            <thead><tr><th>Time</th><th>Actor</th><th>Role</th><th>Action</th><th>Target</th><th>Request</th><th>PR</th><th>Result</th></tr></thead>
            <tbody>
              {data.map((e) => (
                <tr key={e.id}>
                  <td className="mono">{new Date(e.timestamp).toLocaleString()}</td>
                  <td>{e.actor}</td>
                  <td>{e.role}</td>
                  <td className="mono">{e.action}</td>
                  <td className="mono">{e.target_id || '—'}</td>
                  <td className="mono">{e.request_id || '—'}</td>
                  <td className="mono">{e.pr_id || '—'}</td>
                  <td><Badge value={e.result || 'success'} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableWrap>
      )}
    </div>
  )
}
