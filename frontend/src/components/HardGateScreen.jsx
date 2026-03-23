import { useState } from 'react'

const GATES = [
  { key: 'has_deportation_order',
    label: 'Are you subject to a deportation or exclusion order?' },
  { key: 'has_used_deception',
    label: 'Have you used false documents in a UK visa application?' },
  { key: 'has_criminal_conviction',
    label: 'Do you have criminal convictions in any country?' },
  { key: 'has_immigration_debt',
    label: 'Do you owe unpaid costs to the UK Home Office?' },
  { key: 'has_overstayed_90_days',
    label: 'Have you previously overstayed a UK visa by 90+ days?' }
]

export default function HardGateScreen({ onSubmit, loading }) {
  const [answers, setAnswers] = useState({
    has_deportation_order: false,
    has_used_deception: false,
    has_criminal_conviction: false,
    has_immigration_debt: false,
    has_overstayed_90_days: false
  })

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h2 style={{ color: '#1e40af', marginBottom: '8px' }}>
        Eligibility Pre-Check
      </h2>
      <p style={{ color: '#6b7280', marginBottom: '24px' }}>
        Please answer these questions before we continue.
      </p>
      
      {GATES.map(gate => (
        <div key={gate.key} style={{
          background: '#f9fafb',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '12px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span style={{ fontSize: '15px', flex: 1 }}>
            {gate.label}
          </span>
          <div style={{ display: 'flex', gap: '8px' }}>
            {['Yes', 'No'].map(opt => (
              <button
                key={opt}
                onClick={() => setAnswers(prev => ({
                  ...prev,
                  [gate.key]: opt === 'Yes'
                }))}
                style={{
                  padding: '6px 16px',
                  borderRadius: '6px',
                  border: '1px solid',
                  cursor: 'pointer',
                  fontWeight: '500',
                  background: answers[gate.key] === (opt === 'Yes')
                    ? '#1e40af' : 'white',
                  color: answers[gate.key] === (opt === 'Yes')
                    ? 'white' : '#374151',
                  borderColor: answers[gate.key] === (opt === 'Yes')
                    ? '#1e40af' : '#d1d5db'
                }}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>
      ))}

      <button
        onClick={() => onSubmit(answers)}
        disabled={loading}
        style={{
          width: '100%',
          padding: '14px',
          background: '#1e40af',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          fontSize: '16px',
          fontWeight: '600',
          cursor: loading ? 'not-allowed' : 'pointer',
          marginTop: '8px'
        }}
      >
        {loading ? 'Checking...' : 'Continue →'}
      </button>
    </div>
  )
}
