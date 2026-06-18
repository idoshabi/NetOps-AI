export function IconNetwork({ size = 20, stroke = 2, color = 'currentColor' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="16" y="16" width="6" height="6" rx="1" />
      <rect x="2" y="16" width="6" height="6" rx="1" />
      <rect x="9" y="2" width="6" height="6" rx="1" />
      <path d="M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3" />
      <path d="M12 12V8" />
    </svg>
  )
}

export function IconMessage({ size = 20, stroke = 1.5, color = 'currentColor' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z" />
    </svg>
  )
}

export function IconWaypoints({ size = 20, stroke = 1.5, color = 'currentColor' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="m10.586 5.414-5.172 5.172" /><path d="m18.586 13.414-5.172 5.172" /><path d="M6 12h12" />
      <circle cx="12" cy="20" r="2" /><circle cx="12" cy="4" r="2" /><circle cx="20" cy="12" r="2" /><circle cx="4" cy="12" r="2" />
    </svg>
  )
}

export function IconShieldAlert({ size = 20, stroke = 1.5, color = 'currentColor' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" />
      <path d="M12 8v4" /><path d="M12 16h.01" />
    </svg>
  )
}

export function IconGitPR({ size = 20, stroke = 1.5, color = 'currentColor' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="18" cy="18" r="3" /><circle cx="6" cy="6" r="3" />
      <path d="M13 6h3a2 2 0 0 1 2 2v7" /><line x1="6" x2="6" y1="9" y2="21" />
    </svg>
  )
}
