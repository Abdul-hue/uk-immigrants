import { useState, useEffect, useRef } from 'react'
import ChatMessage from './ChatMessage'

function mapNameToKey(name) {
  const m = {
    DEPORTATION_ORDER: 'has_deportation_order',
    DECEPTION: 'has_used_deception',
    CRIMINALITY: 'has_criminal_conviction',
    IMMIGRATION_DEBT: 'has_immigration_debt',
    OVERSTAY: 'has_overstayed_90_days',
  }
  return m[name] || null
}

function mapNameToLabel(name) {
  const m = {
    DEPORTATION_ORDER: 'Deportation or exclusion order',
    DECEPTION: 'Use of false documents',
    CRIMINALITY: 'Criminal convictions',
    IMMIGRATION_DEBT: 'Outstanding immigration debt',
    OVERSTAY: 'Overstay 90+ days',
  }
  return m[name] || name
}

function analyzeCriminality(text) {
  const t = (text || '').toLowerCase()
  const high = ['prison', 'jail', 'custodial', 'imprisoned', 'years', 'months in', 'violent', 'assault', 'trafficking', 'murder', 'terror']
  const medium = ['conviction', 'guilty', 'court', 'fine', 'probation', 'community service', 'suspended', 'theft', 'fraud']
  const low = ['caution', 'warning', 'minor', 'traffic', 'speeding', 'parking', 'misdemeanor', 'juvenile']
  let sev = 'unknown'
  const matched = []
  high.forEach(k => { if (t.includes(k)) { matched.push(k); sev = 'high' } })
  if (sev === 'unknown') medium.forEach(k => { if (t.includes(k)) { matched.push(k); sev = 'medium' } })
  if (sev === 'unknown') low.forEach(k => { if (t.includes(k)) { matched.push(k); sev = 'low' } })
  return { severity: sev, matched }
}

function getExplanationData(name, details) {
  if (name === 'CRIMINALITY') {
    const a = analyzeCriminality(details)
    let tailored = ''
    if (a.severity === 'high') {
      tailored = 'Based on your details, this appears to involve a custodial sentence. Under S-EC.1.5, 12+ months typically results in automatic refusal. 4–12 months requires assessment.'
    } else if (a.severity === 'medium') {
      tailored = 'This appears to be a non-custodial conviction. Under S-EC.1.6, assessment depends on offense type and time elapsed.'
    } else if (a.severity === 'low') {
      tailored = 'This appears to be a minor offense or caution. Under S-EC.1.7, minor older offenses may not automatically disqualify you.'
    } else {
      tailored = 'We cannot determine severity from the details provided. A solicitor can assess impact based on offense category and timing.'
    }
    return {
      heading: 'Criminal Convictions & UK Entry',
      citation: 'Part Suitability, Section S-EC.1.5',
      tailored,
      body: 'The Home Office assesses nature of offense, sentence, time elapsed, and rehabilitation evidence.'
    }
  }
  if (name === 'DEPORTATION_ORDER') {
    return {
      heading: 'Previous Deportation or Exclusion Order',
      citation: 'Part Suitability, Section S-EC.2.1',
      tailored: '',
      body: 'Individuals subject to a current deportation or exclusion order are automatically refused entry at the entry clearance stage.'
    }
  }
  if (name === 'DECEPTION') {
    return {
      heading: 'Previous Deception in UK Applications',
      citation: 'Part Suitability, Section S-EC.3.1',
      tailored: '',
      body: 'Use of false documents or misrepresentation results in refusal. Ban periods vary based on when the deception occurred.'
    }
  }
  if (name === 'IMMIGRATION_DEBT') {
    return {
      heading: 'Outstanding Immigration Debt',
      citation: 'Part Suitability, Section S-EC.4.1',
      tailored: '',
      body: 'Applicants with unpaid litigation costs or other debts to the Home Office must settle these before a new application can be approved.'
    }
  }
  if (name === 'OVERSTAY') {
    return {
      heading: 'Previous Overstay in the UK',
      citation: 'Part Suitability, Section S-EC.5.1',
      tailored: '',
      body: 'Overstaying a visa by more than 90 days can trigger a re-entry ban. The ban period starts from the date you left the UK.'
    }
  }
  return { heading: 'Eligibility Consideration', citation: '', tailored: '', body: '' }
}

export default function HardGateScreen({ questions = [], step, flaggedGates = [], onSubmit, onContinue, loading }) {
  const filtered = (questions || [])
    .filter(q => !!mapNameToKey(q.name))
    .sort((a, b) => (a.gate_order ?? 0) - (b.gate_order ?? 0))

  const [idx, setIdx] = useState(0)
  const total = filtered.length
  const progressPct = total > 0 ? Math.round((idx / total) * 100) : 0
  const [answers, setAnswers] = useState({
    has_deportation_order: false,
    has_used_deception: false,
    has_criminal_conviction: false,
    has_immigration_debt: false,
    has_overstayed_90_days: false
  })
  const [messages, setMessages] = useState(filtered.length > 0 ? [{ sender: 'assistant', text: filtered[0].question }] : [])
  const messagesEndRef = useRef(null)
  const [subStep, setSubStep] = useState('QUESTION')
  const [probeText, setProbeText] = useState('')
  const [detailsByKey, setDetailsByKey] = useState({})
  const [explanation, setExplanation] = useState(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (filtered.length > 0) {
      setIdx(0)
      setMessages([{ sender: 'assistant', text: filtered[0].question }])
      setSubStep('QUESTION')
      setProbeText('')
      setDetailsByKey({})
      setAnswers({
        has_deportation_order: false,
        has_used_deception: false,
        has_criminal_conviction: false,
        has_immigration_debt: false,
        has_overstayed_90_days: false
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [questions])

  const handleAnswer = async (val) => {
    const gate = filtered[idx]
    if (!gate) return
    const key = mapNameToKey(gate.name)
    if (!key) return
    setAnswers(prev => ({ ...prev, [key]: val }))
    setMessages(prev => [...prev, { sender: 'user', text: val ? 'Yes' : 'No' }])
    if (val) {
      setSubStep('PROBE')
      setMessages(prev => [...prev, { sender: 'assistant', text: 'I understand. To check this against UK Home Office eligibility criteria, can you tell us a bit more about what this relates to?' }])
      return
    }
    const nextIndex = idx + 1
    if (nextIndex < filtered.length) {
      setIdx(nextIndex)
      setMessages(prev => [...prev, { sender: 'assistant', text: filtered[nextIndex].question }])
    } else {
      await onSubmit({ ...answers, [key]: val }, false, detailsByKey)
    }
  }

  const handleProbeSubmit = async () => {
    const gate = filtered[idx]
    if (!gate) return
    const key = mapNameToKey(gate.name)
    if (!key) return
    const text = probeText.trim()
    if (!text) return
    setDetailsByKey(prev => ({ ...prev, [key]: text }))
    setMessages(prev => [...prev, { sender: 'user', text }])
    setProbeText('')
    const data = getExplanationData(gate.name, text)
    setExplanation(data)
    setSubStep('EXPLANATION')
  }

  if (step === 'solicitor_review') {
    return (
      <div className="card" style={{ borderColor: 'var(--warning)', background: '#fffbeb' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <h2 style={{ color: '#92400e', margin: 0, fontSize: '1.25rem' }}>Legal Review Required</h2>
          <span className="route-badge" style={{ background: '#fef3c7', color: '#92400e', borderColor: '#fde68a' }}>Action Needed</span>
        </div>
        <p style={{ color: '#92400e', fontSize: '0.9375rem', marginBottom: '1rem' }}>
          The following items have been flagged for professional assessment:
        </p>
        <ul style={{ margin: '0 0 1.5rem 0', paddingLeft: '1.25rem', color: '#92400e', fontSize: '0.9375rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {flaggedGates && flaggedGates.length > 0 ? flaggedGates.map((g, i) => (
            <li key={i} style={{ fontWeight: '600' }}>{mapNameToLabel((g.type || g.name || '').toString().toUpperCase())}</li>
          )) : <li>Suitability requirements</li>}
        </ul>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <button
            className="btn-primary"
            onClick={() => onSubmit(answers, true)}
            disabled={loading}
          >
            Connect with a Solicitor
          </button>
          <button
            className="btn-option"
            onClick={() => onContinue()}
            disabled={loading}
          >
            Continue Assessment Anyway
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="hard-gate-container">
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <span className="form-label" style={{ margin: 0, fontSize: '0.75rem', textTransform: 'uppercase' }}>Suitability Pre-checks</span>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '600' }}>{Math.min(idx + 1, total)} / {total}</span>
        </div>
        <div style={{ height: '6px', background: '#e2e8f0', borderRadius: '999px', overflow: 'hidden' }}>
          <div style={{ width: `${progressPct}%`, height: '100%', background: 'var(--primary)', transition: 'width 0.4s ease' }} />
        </div>
      </div>

      <div className="chat-history" style={{ maxHeight: '400px', overflowY: 'auto', marginBottom: '1.5rem' }}>
        {messages.map((msg, index) => (
          <ChatMessage key={index} message={msg.text} sender={msg.sender} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="card" style={{ marginTop: 'auto' }}>
        {subStep === 'QUESTION' && (
          <div className="options-grid">
            <button
              className="btn-option primary"
              onClick={() => handleAnswer(true)}
              disabled={loading}
            >
              Yes
            </button>
            <button
              className="btn-option"
              onClick={() => handleAnswer(false)}
              disabled={loading}
            >
              No
            </button>
          </div>
        )}

        {subStep === 'PROBE' && (
          <div className="input-group">
            <textarea
              value={probeText}
              onChange={e => setProbeText(e.target.value)}
              placeholder="Please provide brief details..."
              rows={3}
              autoFocus
            />
            <button
              className="btn-primary"
              onClick={handleProbeSubmit}
              disabled={!probeText.trim()}
              style={{ marginTop: '1rem' }}
            >
              Confirm Details →
            </button>
          </div>
        )}

        {subStep === 'EXPLANATION' && explanation && (
          <div style={{ animation: 'fadeIn 0.4s ease-out' }}>
            <div className="alert alert-warning">
              <span>⚖️</span>
              <div>
                <span className="alert-title">{explanation.heading}</span>
                <p className="alert-message" style={{ fontSize: '0.8125rem', opacity: 0.8, marginBottom: '0.5rem' }}>{explanation.citation}</p>
                {explanation.tailored && (
                  <p className="alert-message" style={{ fontWeight: '600', marginBottom: '0.5rem' }}>{explanation.tailored}</p>
                )}
                <p className="alert-message">{explanation.body}</p>
              </div>
            </div>
            <button
              className="btn-primary"
              onClick={async () => {
                const nextIndex = idx + 1
                if (nextIndex < filtered.length) {
                  setIdx(nextIndex)
                  setMessages(prev => [...prev, { sender: 'assistant', text: filtered[nextIndex].question }])
                  setSubStep('QUESTION')
                  setExplanation(null)
                } else {
                  await onSubmit(answers, false, detailsByKey)
                }
              }}
            >
              I Understand, Continue →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
