import React, { useMemo, useState, useRef, useCallback } from 'react'

const TYPE_ORDER = [
  'business_unit', 'team', 'application', 'cloud_account', 'vpc', 'subnet',
  'workload', 'security_group', 'firewall_rule', 'route', 'ipam_range',
  'terraform_file', 'owner', 'risk_finding',
]

// Infrastructure spine — shown in Overview mode (much less clutter).
const SPINE_TYPES = new Set([
  'cloud_account', 'application', 'vpc', 'subnet', 'workload', 'firewall_rule',
])

const TYPE_STYLE = {
  cloud_account: { fill: '#0ea5e9', stroke: '#38bdf8', glow: '#0ea5e980', label: 'Cloud' },
  route: { fill: '#0ea5e9', stroke: '#38bdf8', glow: '#0ea5e980', label: 'Route' },
  application: { fill: '#8b5cf6', stroke: '#c4b5fd', glow: '#8b5cf680', label: 'Application' },
  vpc: { fill: '#8b5cf6', stroke: '#c4b5fd', glow: '#8b5cf680', label: 'VPC' },
  business_unit: { fill: '#8b5cf6', stroke: '#c4b5fd', glow: '#8b5cf680', label: 'Business unit' },
  firewall_rule: { fill: '#f97316', stroke: '#fdba74', glow: '#f9731680', label: 'Firewall' },
  security_group: { fill: '#f97316', stroke: '#fdba74', glow: '#f9731680', label: 'Security group' },
  workload: { fill: '#10b981', stroke: '#6ee7b7', glow: '#10b98180', label: 'Compute' },
  team: { fill: '#10b981', stroke: '#6ee7b7', glow: '#10b98180', label: 'Team' },
  owner: { fill: '#10b981', stroke: '#6ee7b7', glow: '#10b98180', label: 'Owner' },
  subnet: { fill: '#ec4899', stroke: '#f9a8d4', glow: '#ec489980', label: 'Subnet' },
  ipam_range: { fill: '#ec4899', stroke: '#f9a8d4', glow: '#ec489980', label: 'IPAM' },
  terraform_file: { fill: '#64748b', stroke: '#94a3b8', glow: '#64748b80', label: 'Terraform' },
  risk_finding: { fill: '#ef4444', stroke: '#fca5a5', glow: '#ef444480', label: 'Finding' },
}

const LEGEND = [
  { label: 'Cloud', color: '#38bdf8', glow: '#0ea5e980' },
  { label: 'Application', color: '#c4b5fd', glow: '#8b5cf680' },
  { label: 'Firewall', color: '#fdba74', glow: '#f9731680' },
  { label: 'Compute', color: '#6ee7b7', glow: '#10b98180' },
  { label: 'Subnet', color: '#f9a8d4', glow: '#ec489980' },
]

const MIN_ROW_GAP = 96
const COL_WIDTH = 168
const PAD_X = 100
const PAD_Y = 80

function nodeStyle(type) {
  return TYPE_STYLE[type] || { fill: '#64748b', stroke: '#94a3b8', glow: '#64748b80', label: type }
}

function shortLabel(label, max = 22) {
  if (!label) return '—'
  const parts = String(label).split('/')
  const s = parts[parts.length - 1].replace(/\.tf$/, '')
  return s.length > max ? `${s.slice(0, max - 1)}…` : s
}

function NodeLabels({ name, sub, r, emphasis }) {
  const labelY = r + 18
  const subY = r + 32
  const fontSize = emphasis ? 12 : 10
  const subSize = 8
  const padX = 6
  const w = Math.max(name.length * (fontSize * 0.58), sub ? sub.length * (subSize * 0.62) : 0) + padX * 2
  const h = sub ? 34 : 18
  const x = -w / 2
  const y = r + 6

  return (
    <g pointerEvents="none">
      <rect
        x={x}
        y={y}
        width={w}
        height={h}
        rx={5}
        fill="rgba(2, 8, 23, 0.88)"
        stroke="rgba(148, 163, 184, 0.2)"
        strokeWidth={1}
      />
      <text
        textAnchor="middle"
        y={labelY}
        fontSize={fontSize}
        fill={emphasis ? '#f8fafc' : '#e2e8f0'}
        fontWeight="600"
      >
        {name}
      </text>
      {sub && (
        <text
          textAnchor="middle"
          y={subY}
          fontSize={subSize}
          fill="#94a3b8"
          fontFamily="var(--font-mono)"
        >
          {sub}
        </text>
      )}
    </g>
  )
}

function nodeRadius(countInColumn) {
  if (countInColumn <= 4) return 26
  if (countInColumn <= 8) return 22
  if (countInColumn <= 14) return 18
  return 14
}

export default function GraphView({ graph, onSelect, selectedId }) {
  const [viewMode, setViewMode] = useState('overview')
  const [typeFilter, setTypeFilter] = useState('all')
  const [hovered, setHovered] = useState(null)
  const [internalSelected, setInternalSelected] = useState(null)
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 })
  const dragRef = useRef(null)
  const svgRef = useRef(null)

  const selected = selectedId ?? internalSelected

  const visibleTypes = useMemo(() => {
    if (typeFilter !== 'all') return new Set([typeFilter])
    if (viewMode === 'overview') return SPINE_TYPES
    return new Set(TYPE_ORDER.filter((t) => graph.nodes.some((n) => n.type === t)))
  }, [viewMode, typeFilter, graph.nodes])

  const { nodes, edges, pos, viewH, viewW, columns, counts } = useMemo(() => {
    const visibleNodes = graph.nodes.filter((n) => visibleTypes.has(n.type))
    const ids = new Set(visibleNodes.map((n) => n.id))

    const byType = {}
    visibleNodes.forEach((n) => { (byType[n.type] ||= []).push(n) })
    const types = TYPE_ORDER.filter((t) => byType[t])

    const maxCol = Math.max(...types.map((t) => byType[t].length), 1)
    const viewW = PAD_X * 2 + Math.max(types.length, 1) * COL_WIDTH
    const viewH = Math.max(640, PAD_Y * 2 + maxCol * MIN_ROW_GAP + 36)

    const pos = {}
    types.forEach((t, ci) => {
      const list = byType[t]
      const gap = Math.max(MIN_ROW_GAP, (viewH - PAD_Y * 2) / (list.length + 1))
      const startY = PAD_Y + gap
      list.forEach((n, i) => {
        pos[n.id] = { x: PAD_X + ci * COL_WIDTH, y: startY + i * gap, type: t }
      })
    })

    const visibleEdges = graph.edges.filter((e) => ids.has(e.source) && ids.has(e.target))

    return {
      nodes: visibleNodes,
      edges: visibleEdges,
      pos,
      viewH,
      viewW,
      columns: types,
      counts: { nodes: visibleNodes.length, edges: visibleEdges.length, total: graph.nodes.length },
    }
  }, [graph, visibleTypes])

  const pick = (id) => {
    const next = selected === id ? null : id
    setInternalSelected(next)
    onSelect?.(next ? graph.nodes.find((n) => n.id === next) : null)
  }

  const neighborIds = useMemo(() => {
    if (!selected) return new Set()
    const s = new Set([selected])
    edges.forEach((e) => {
      if (e.source === selected) s.add(e.target)
      if (e.target === selected) s.add(e.source)
    })
    return s
  }, [selected, edges])

  const hoveredNode = useMemo(
    () => (hovered ? graph.nodes.find((n) => n.id === hovered) : null),
    [hovered, graph.nodes],
  )

  const onWheel = useCallback((e) => {
    e.preventDefault()
    const factor = e.deltaY > 0 ? 0.92 : 1.08
    setTransform((t) => ({ ...t, k: Math.min(2.5, Math.max(0.35, t.k * factor)) }))
  }, [])

  const onPointerDown = (e) => {
    if (e.target.closest('.graph-node')) return
    dragRef.current = { x: e.clientX, y: e.clientY, tx: transform.x, ty: transform.y }
    e.currentTarget.setPointerCapture(e.pointerId)
  }

  const onPointerMove = (e) => {
    if (!dragRef.current) return
    setTransform((t) => ({
      ...t,
      x: dragRef.current.tx + (e.clientX - dragRef.current.x),
      y: dragRef.current.ty + (e.clientY - dragRef.current.y),
    }))
  }

  const onPointerUp = () => { dragRef.current = null }

  const resetView = () => setTransform({ x: 0, y: 0, k: 1 })

  const colSizes = useMemo(() => {
    const m = {}
    nodes.forEach((n) => { m[n.type] = (m[n.type] || 0) + 1 })
    return m
  }, [nodes])

  return (
    <div className="topology-canvas">
      <div className="graph-toolbar glass-elevated">
        <div className="graph-toolbar-group">
          <span className="graph-toolbar-label">View</span>
          <button type="button" className={`graph-mode-btn${viewMode === 'overview' ? ' on' : ''}`} onClick={() => { setViewMode('overview'); setTypeFilter('all') }}>
            Overview
          </button>
          <button type="button" className={`graph-mode-btn${viewMode === 'full' ? ' on' : ''}`} onClick={() => { setViewMode('full'); setTypeFilter('all') }}>
            Full graph
          </button>
        </div>
        <span className="graph-toolbar-stat">
          {counts.nodes} nodes · {counts.edges} edges
          {viewMode === 'overview' && counts.total > counts.nodes && (
            <span className="graph-toolbar-muted"> ({counts.total - counts.nodes} hidden)</span>
          )}
        </span>
        <button type="button" className="btn-ghost sm graph-reset" onClick={resetView} title="Reset pan & zoom">Reset view</button>
      </div>

      <svg
        ref={svgRef}
        viewBox={`0 0 ${viewW} ${viewH}`}
        width="100%"
        height="100%"
        preserveAspectRatio="xMidYMid meet"
        className="graph-svg"
        onWheel={onWheel}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={onPointerUp}
      >
        <defs>
          {Object.entries(TYPE_STYLE).map(([t, s]) => (
            <radialGradient key={t} id={`nodeGrad-${t}`} cx="30%" cy="30%">
              <stop offset="0%" stopColor={s.stroke} stopOpacity="0.95" />
              <stop offset="100%" stopColor={s.fill} stopOpacity="0.85" />
            </radialGradient>
          ))}
          <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
            <circle cx="1" cy="1" r="0.8" fill="rgba(148,163,184,0.08)" />
          </pattern>
        </defs>

        <rect width={viewW} height={viewH} fill="url(#grid)" />

        <g transform={`translate(${transform.x},${transform.y}) scale(${transform.k})`}>
          {/* Column guides */}
          {columns.map((t, ci) => (
            <text
              key={t}
              x={PAD_X + ci * COL_WIDTH}
              y={28}
              textAnchor="middle"
              fill="#475569"
              fontSize="9"
              fontWeight="600"
              letterSpacing="0.06em"
              style={{ textTransform: 'uppercase' }}
            >
              {t.replace(/_/g, ' ')}
            </text>
          ))}

          {edges.map((e, i) => {
            const a = pos[e.source], b = pos[e.target]
            if (!a || !b) return null
            const hot = selected && (e.source === selected || e.target === selected)
            const near = hovered && (e.source === hovered || e.target === hovered)
            const denied = e.relation?.includes('deny') || e.relation === 'blocks'
            let opacity = 0.08
            if (hot) opacity = 0.9
            else if (near) opacity = 0.35
            else if (!selected && !hovered) opacity = 0.14

            return (
              <line
                key={i}
                x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                stroke={hot ? '#34d399' : denied ? '#f87171' : '#334155'}
                strokeWidth={hot ? 2 : 1}
                strokeDasharray={denied ? '4 4' : undefined}
                opacity={opacity}
              />
            )
          })}

          {nodes.map((n) => {
            const p = pos[n.id]
            if (!p) return null
            const isSel = selected === n.id
            const isHov = hovered === n.id
            const isNbr = neighborIds.has(n.id)
            const dim = selected && !isSel && !isNbr
            const style = nodeStyle(n.type)
            const r = nodeRadius(colSizes[n.type])
            const name = shortLabel(n.label, isSel || isHov ? 28 : 20)
            const sub = n.props?.region
              || (n.props?.cidr ? String(n.props.cidr) : '')
              || (n.props?.environment ? String(n.props.environment) : '')
            const subShort = sub ? shortLabel(sub, 18) : ''

            return (
              <g
                key={n.id}
                className="graph-node"
                transform={`translate(${p.x},${p.y})`}
                style={{ cursor: 'pointer' }}
                opacity={dim ? 0.25 : 1}
                onClick={() => pick(n.id)}
                onPointerEnter={() => setHovered(n.id)}
                onPointerLeave={() => setHovered((h) => (h === n.id ? null : h))}
              >
                <title>{n.label}{sub ? ` · ${sub}` : ''}</title>
                {(isSel || isHov) && <circle r={r + 10} fill={style.fill} opacity={0.12} />}
                <circle
                  r={isSel ? r + 2 : r}
                  fill={`url(#nodeGrad-${n.type in TYPE_STYLE ? n.type : 'cloud_account'})`}
                  stroke={isSel ? '#fff' : style.stroke}
                  strokeWidth={isSel ? 2.5 : isHov ? 2 : 1.5}
                />
                <NodeLabels
                  name={name}
                  sub={subShort}
                  r={r}
                  emphasis={isSel || isHov}
                />
              </g>
            )
          })}
        </g>
      </svg>

      {hoveredNode && (
        <div className="graph-tooltip glass-elevated">
          <strong>{hoveredNode.label}</strong>
          <span className="badge neutral">{hoveredNode.type.replace(/_/g, ' ')}</span>
          {hoveredNode.props?.cidr && <div className="mono">{hoveredNode.props.cidr}</div>}
        </div>
      )}

      <div className="graph-legend glass-elevated">
        {LEGEND.map((l) => (
          <span key={l.label} className="legend-item">
            <span className="legend-dot" style={{ backgroundColor: l.color, boxShadow: `0 0 6px ${l.glow}` }} />
            {l.label}
          </span>
        ))}
        <span className="legend-divider" />
        <span className="legend-item muted">Scroll to zoom · drag to pan</span>
      </div>

      {viewMode === 'full' && (
        <div className="graph-type-filter glass-elevated">
          <button type="button" className={`legend-filter${typeFilter === 'all' ? ' on' : ''}`} onClick={() => setTypeFilter('all')}>All layers</button>
          {TYPE_ORDER.filter((t) => graph.nodes.some((n) => n.type === t)).map((t) => (
            <button
              key={t}
              type="button"
              className={`legend-filter${typeFilter === t ? ' on' : ''}`}
              onClick={() => setTypeFilter(typeFilter === t ? 'all' : t)}
            >
              <span className="legend-dot" style={{ backgroundColor: nodeStyle(t).stroke }} />
              {t.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
