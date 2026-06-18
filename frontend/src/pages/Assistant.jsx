import React, { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'

const SUGGESTIONS = [
  'Who owns the payroll production subnet?',
  'Can I create 10.42.10.128/25 for HR dev?',
  'Suggest an available subnet for HR dev.',
  'Which production subnets are internet-facing?',
  'Show all firewall rules that allow broad access.',
  'Show risky paths from the internet to sensitive systems.',
  'Create a new dev subnet for the HR application.',
]

function Sources({ m }) {
  if (!m.sources?.length && !m.related_assets?.length) return null
  return (
    <div className="meta">
      {m.risk_level && <span>risk: <span className={`badge ${m.risk_level}`}>{m.risk_level}</span> </span>}
      {m.confidence && <span> · confidence: {m.confidence}</span>}
      {m.sources?.length > 0 && <div>sources: <span className="mono">{m.sources.join(' · ')}</span></div>}
      {m.related_assets?.length > 0 && <div>related: <span className="mono">{m.related_assets.join(', ')}</span></div>}
      {m.recommended_action && <div>↳ {m.recommended_action}</div>}
    </div>
  )
}

function Proposal({ p }) {
  if (!p) return null
  return (
    <div className="panel" style={{ marginTop: 10 }}>
      <div className="row between"><strong>Terraform PR proposal</strong>
        <Link to={`/change/prs/${p.pull_request_id}`}>open PR →</Link></div>
      <div className="mono" style={{ margin: '6px 0' }}>{p.branch}</div>
      {p.explanation && <p style={{ color: 'var(--muted)' }}>{p.explanation}</p>}
      <pre>{p.terraform}</pre>
      <div className="row">reviewers: {(p.reviewers || []).map((r) => <span key={r} className="badge neutral">{r}</span>)}</div>
      <p style={{ color: 'var(--muted)', marginTop: 8 }}>Status: {p.status} — requires human approval before merge.</p>
    </div>
  )
}

export default function Assistant() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [convId, setConvId] = useState(null)
  const [busy, setBusy] = useState(false)
  const endRef = useRef(null)

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, busy])

  const send = async (text) => {
    const q = (text ?? input).trim()
    if (!q || busy) return
    setInput(''); setBusy(true)
    setMessages((m) => [...m, { role: 'user', answer: q }])
    try {
      const res = await api.ask({ question: q, conversation_id: convId, user: 'demo-user' })
      setConvId(res.conversation_id)
      setMessages((m) => [...m, { role: 'assistant', ...res }])
    } catch (e) {
      setMessages((m) => [...m, { role: 'assistant', answer: `Error: ${e.message}`, risk_level: 'high' }])
    } finally { setBusy(false) }
  }

  return (
    <div className="copilot-page">
      <div className="content-head">
        <h2 className="content-title">Copilot</h2>
        <p className="content-sub">Ask the network in natural language, or request a safe Terraform PR proposal. Every answer is grounded in evidence; every proposal is policy-checked and requires human approval.</p>
      </div>

      <div className="chat">
        <div className="suggestions">
          {SUGGESTIONS.map((s) => <button key={s} className="btn secondary" onClick={() => send(s)}>{s}</button>)}
        </div>
        <div className="messages">
          {messages.length === 0 && <p className="loading">Try a suggestion above, or ask your own question.</p>}
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              <div className="bubble">
                <div style={{ whiteSpace: 'pre-wrap' }}>{m.answer}</div>
                {m.role === 'assistant' && <Sources m={m} />}
                {m.role === 'assistant' && <Proposal p={m.proposal} />}
              </div>
            </div>
          ))}
          {busy && <div className="msg assistant"><div className="bubble loading">thinking…</div></div>}
          <div ref={endRef} />
        </div>
        <div className="chat-input">
          <input value={input} placeholder="Ask about ownership, risk, CIDRs, Terraform…"
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()} />
          <button className="btn" onClick={() => send()} disabled={busy}>Send</button>
        </div>
      </div>
    </div>
  )
}
