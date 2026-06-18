import React from 'react'
import { api } from '../api/client'
import { useApi } from '../components/useApi'
import { Loading, ErrorMsg, PageHeader, TableWrap } from '../components/ui'

export default function Subnets({ embedded = false }) {
  const { data, error, loading } = useApi(api.subnets, [])
  return (
    <div>
      {!embedded ? (
        <PageHeader
          title="Subnet Inventory"
          subtitle="Discovered subnets correlated across cloud, IPAM and Terraform state."
        />
      ) : (
        <h3 className="panel-kicker" style={{ marginBottom: 16 }}>Subnet inventory</h3>
      )}
      <ErrorMsg error={error} />
      {loading && <Loading what="subnets" />}
      {data && (
        <TableWrap>
          <table>
            <thead>
              <tr>
                <th>CIDR</th><th>VPC</th><th>Owner</th><th>App</th><th>Env</th>
                <th>Region</th><th>Data class</th><th>Internet</th><th>Terraform</th>
              </tr>
            </thead>
            <tbody>
              {data.map((s) => (
                <tr key={s.id}>
                  <td className="mono">{s.cidr}</td>
                  <td className="mono">{s.vpc_id}</td>
                  <td>{s.owner || <span className="badge high">missing</span>}</td>
                  <td>{s.application_id || <span className="badge medium">unknown</span>}</td>
                  <td>{s.environment}</td>
                  <td>{s.region}</td>
                  <td>{s.data_classification}</td>
                  <td>{s.internet_facing ? <span className="badge high">yes</span> : 'no'}</td>
                  <td>{s.terraform_managed ? '✓' : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableWrap>
      )}
    </div>
  )
}
