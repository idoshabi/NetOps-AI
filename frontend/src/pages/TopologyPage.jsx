import React, { useState } from 'react'
import { api } from '../api/client'
import { useApi } from '../components/useApi'
import { Loading, ErrorMsg } from '../components/ui'
import GraphView from '../components/GraphView'
import TopologyPanel from '../components/TopologyPanel'

export default function TopologyPage() {
  const { data, error, loading, reload } = useApi(api.graph, [])
  const [selected, setSelected] = useState(null)
  const tenant = 'Acme Retail'

  return (
    <div className="topology-layout">
      <section className="topology-sidebar">
        <div className="topology-sidebar-head">
          <h2>Topology</h2>
          <span>Inspect &amp; sync</span>
        </div>
        <TopologyPanel selected={selected} tenant={tenant} onSync={reload} />
      </section>

      <section className="topology-main">
        <ErrorMsg error={error} />
        {loading && <Loading what="topology" />}
        {data && (
          <GraphView graph={data} onSelect={setSelected} selectedId={selected?.id} />
        )}
      </section>
    </div>
  )
}
