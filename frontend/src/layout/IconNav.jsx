import React from 'react'
import { NavLink } from 'react-router-dom'
import { IconNetwork, IconMessage, IconWaypoints, IconShieldAlert, IconGitPR } from '../components/icons'

const TABS = [
  { to: '/', label: 'Topology', short: 'Topo', end: true, Icon: IconNetwork, color: '#22d3ee' },
  { to: '/copilot', label: 'Copilot', short: 'Copi', Icon: IconMessage, color: '#a78bfa' },
  { to: '/reachability', label: 'Reachability', short: 'Reac', Icon: IconWaypoints, color: '#34d399' },
  { to: '/drift', label: 'Drift', short: 'Drif', Icon: IconShieldAlert, color: '#fbbf24' },
  { to: '/change', label: 'Change', short: 'Chan', Icon: IconGitPR, color: '#fb7185' },
]

export default function IconNav() {
  return (
    <nav className="icon-nav">
      {TABS.map(({ to, label, short, end, Icon, color }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          title={label}
          className={({ isActive }) => `icon-nav-btn${isActive ? ' active' : ''}`}
          style={{ '--tab-color': color }}
        >
          {({ isActive }) => (
            <>
              {isActive && <span className="icon-nav-indicator" style={{ backgroundColor: color }} />}
              <Icon size={20} stroke={isActive ? 2 : 1.5} color={isActive ? color : '#64748b'} />
              <span className="icon-nav-label" style={{ color: isActive ? color : '#475569' }}>{short}</span>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )
}
