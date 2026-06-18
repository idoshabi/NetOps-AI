import React from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useApi } from '../components/useApi'
import { Loading, ErrorMsg, Badge, PageHeader, TableWrap, EmptyState } from '../components/ui'

export default function PullRequests({ embedded = false }) {
  const { data, error, loading } = useApi(api.listPRs, [])
  return (
    <div>
      {!embedded && (
        <PageHeader
          title="Pull Requests"
          subtitle="Generated Terraform PR proposals. Every PR requires human approval — NetGraph Copilot never self-merges."
        />
      )}
      <ErrorMsg error={error} />
      {loading && <Loading what="pull requests" />}
      {data && (data.length === 0
        ? <EmptyState title="No pull requests yet" hint="Approve a request and generate one, or ask Copilot to propose IaC." />
        : (
          <TableWrap><table>
            <thead><tr><th>ID</th><th>Title</th><th>Branch</th><th>Reviewers</th><th>Status</th><th></th></tr></thead>
            <tbody>
              {data.map((pr) => (
                <tr key={pr.id}>
                  <td className="mono">{pr.id}</td>
                  <td>{pr.title}</td>
                  <td className="mono">{pr.branch}</td>
                  <td>{(pr.reviewers || []).length}</td>
                  <td><Badge value={pr.status} /></td>
                  <td><Link to={embedded ? `/change/prs/${pr.id}` : `/pull-requests/${pr.id}`}>open →</Link></td>
                </tr>
              ))}
            </tbody>
          </table></TableWrap>
        ))}
    </div>
  )
}
