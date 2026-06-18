// Thin API client for the NetOps-AI backend.
// In dev, Vite proxies /api -> http://localhost:8000 (see vite.config.js).
const BASE = import.meta.env.VITE_API_BASE || '/api'

const LS_ACTOR = 'netops-ai.actor'
const LS_ROLE = 'netops-ai.role'

// Mock auth: the active role is stored in localStorage and sent as X-Role.
export function getIdentity() {
  return {
    actor: localStorage.getItem(LS_ACTOR) || localStorage.getItem('netgov.actor') || 'demo-user',
    role: localStorage.getItem(LS_ROLE) || localStorage.getItem('netgov.role') || 'admin',
  }
}
export function setIdentity({ actor, role }) {
  if (actor) localStorage.setItem(LS_ACTOR, actor)
  if (role) localStorage.setItem(LS_ROLE, role)
}

async function request(path, { method = 'GET', body } = {}) {
  const { actor, role } = getIdentity()
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-Actor': actor,
      'X-Role': role,
    },
    body: body ? JSON.stringify(body) : undefined,
  })
  const text = await res.text()
  let data = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      const preview = text.trimStart().slice(0, 40)
      if (preview.startsWith('<!') || preview.startsWith('<html')) {
        throw new Error('API unavailable — backend not reachable. Check VITE_API_BASE or /api proxy.')
      }
      throw new Error(`Invalid API response: ${preview}`)
    }
  }
  if (!res.ok) {
    const detail = (data && data.detail) || res.statusText
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return data
}

export const api = {
  // meta / dashboard
  dashboard: () => request('/dashboard'),
  runDiscovery: () => request('/discovery/run', { method: 'POST' }),
  discoveryStatus: () => request('/discovery/status'),
  // inventory
  subnets: () => request('/subnets'),
  vpcs: () => request('/vpcs'),
  applications: () => request('/applications'),
  owners: () => request('/owners'),
  firewallRules: () => request('/firewall-rules'),
  routes: () => request('/routes'),
  findings: () => request('/security-findings'),
  // graph
  graph: () => request('/graph'),
  graphNode: (id) => request(`/graph/node/${id}`),
  riskyPaths: () => request('/graph/risky-paths'),
  // requests
  listRequests: () => request('/subnet/request'),
  getRequest: (id) => request(`/subnet/request/${id}`),
  createRequest: (body) => request('/subnet/request', { method: 'POST', body }),
  validateRequest: (id) => request(`/subnet/request/${id}/validate`, { method: 'POST' }),
  approveRequest: (id, body) => request(`/subnet/request/${id}/approve`, { method: 'POST', body }),
  rejectRequest: (id, body) => request(`/subnet/request/${id}/reject`, { method: 'POST', body }),
  generatePR: (id) => request(`/subnet/request/${id}/generate-pr`, { method: 'POST' }),
  // policy
  evaluatePolicy: (body) => request('/policy/evaluate', { method: 'POST', body }),
  // PRs
  listPRs: () => request('/pull-requests'),
  getPR: (id) => request(`/pull-requests/${id}`),
  approvePR: (id, body) => request(`/pull-requests/${id}/approve`, { method: 'POST', body }),
  rejectPR: (id, body) => request(`/pull-requests/${id}/reject`, { method: 'POST', body }),
  // assistant
  ask: (body) => request('/assistant/ask', { method: 'POST', body }),
  proposeIaC: (body) => request('/assistant/propose-iac', { method: 'POST', body }),
  conversations: () => request('/assistant/conversations'),
  // audit
  audit: () => request('/audit/events'),
}
