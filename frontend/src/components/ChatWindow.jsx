import { useState } from 'react'
import { useSession } from '../hooks/useSession'
import FlagWarning from './FlagWarning'
import HardGateScreen from './HardGateScreen'
import QuestionCard from './QuestionCard'
import ResultScreen from './ResultScreen'

export default function ChatWindow() {
  const [userInput, setUserInput] = useState('')
  const [nationality, setNationality] = useState('')
  const session = useSession()

  const handleStart = async () => {
    if (!userInput.trim() || !nationality.trim()) return
    await session.startSession(userInput, nationality.toUpperCase())
  }

  if (session.step === 'start') {
    return (
      <div style={{ maxWidth: '600px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <h1 style={{ 
            fontSize: '28px', fontWeight: '700',
            color: '#111827', marginBottom: '8px'
          }}>
            🇬🇧 UK Visa Eligibility Check
          </h1>
          <p style={{ color: '#6b7280' }}>
            Answer a few questions to find out if you may be 
            eligible for a UK visa.
          </p>
        </div>

        <div style={{
          background: 'white', borderRadius: '12px',
          border: '1px solid #e5e7eb', padding: '24px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
        }}>
          <label style={{ 
            display: 'block', fontWeight: '600',
            marginBottom: '8px', color: '#374151'
          }}>
            Why are you interested in coming to the UK?
          </label>
          <textarea
            value={userInput}
            onChange={e => setUserInput(e.target.value)}
            placeholder="e.g. I have a job offer from a company in London..."
            rows={3}
            style={{
              width: '100%', padding: '12px',
              borderRadius: '8px', border: '1px solid #d1d5db',
              fontSize: '15px', resize: 'vertical',
              boxSizing: 'border-box', marginBottom: '16px'
            }}
          />

          <label style={{ 
            display: 'block', fontWeight: '600',
            marginBottom: '8px', color: '#374151'
          }}>
            Your nationality (2-letter code, e.g. PK, US, IN)
          </label>
          <input
            value={nationality}
            onChange={e => setNationality(e.target.value)}
            placeholder="e.g. PK"
            maxLength={2}
            style={{
              width: '100%', padding: '12px',
              borderRadius: '8px', border: '1px solid #d1d5db',
              fontSize: '15px', boxSizing: 'border-box',
              marginBottom: '20px', textTransform: 'uppercase'
            }}
          />

          <button
            onClick={handleStart}
            disabled={session.loading || !userInput || !nationality}
            style={{
              width: '100%', padding: '14px',
              background: '#1e40af', color: 'white',
              border: 'none', borderRadius: '8px',
              fontSize: '16px', fontWeight: '600',
              cursor: session.loading ? 'not-allowed' : 'pointer'
            }}
          >
            {session.loading ? 'Analysing...' : 'Check My Eligibility →'}
          </button>
        </div>

        <p style={{
          fontSize: '11px', color: '#9ca3af',
          textAlign: 'center', marginTop: '16px'
        }}>
          This is a Preliminary Self-Assessment only. 
          Not legal advice.
        </p>
      </div>
    )
  }

  if (session.step === 'clarify') {
    return (
      <div style={{ maxWidth: '600px', margin: '0 auto' }}>
        <div style={{
          background: 'white', borderRadius: '12px',
          border: '1px solid #e5e7eb', padding: '24px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
        }}>
          <p style={{ color: '#6b7280', marginBottom: '8px',
            fontSize: '14px' }}>
            One more detail needed:
          </p>
          <h3 style={{ color: '#111827', marginBottom: '20px',
            fontSize: '18px' }}>
            {session.clarifyingQuestion}
          </h3>
          <textarea
            value={userInput}
            onChange={e => setUserInput(e.target.value)}
            placeholder="Please provide more detail..."
            rows={3}
            style={{
              width: '100%', padding: '12px',
              borderRadius: '8px', border: '1px solid #d1d5db',
              fontSize: '15px', resize: 'vertical',
              boxSizing: 'border-box', marginBottom: '16px'
            }}
          />
          <button
            onClick={() => session.clarifySession(
              userInput, nationality
            )}
            disabled={session.loading || !userInput}
            style={{
              width: '100%', padding: '14px',
              background: '#1e40af', color: 'white',
              border: 'none', borderRadius: '8px',
              fontSize: '16px', fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            {session.loading ? 'Analysing...' : 'Continue →'}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>

      {session.route && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{
            background: '#eff6ff', borderRadius: '8px',
            padding: '12px 16px', marginBottom: '12px',
            display: 'flex', alignItems: 'center', gap: '8px'
          }}>
            <span>🎯</span>
            <span style={{ fontWeight: '600', color: '#1e40af' }}>
              Route: {session.route.replace(/_/g, ' ')}
            </span>
          </div>
          <FlagWarning flags={session.flags} />
        </div>
      )}

      {session.step === 'error' && (
        <div style={{
          background: '#fee2e2', border: '1px solid #dc2626',
          borderRadius: '12px', padding: '24px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '48px' }}>🚫</div>
          <h2 style={{ color: '#dc2626', marginTop: '12px' }}>
            Application Cannot Proceed
          </h2>
          <p style={{ color: '#7f1d1d', marginTop: '8px' }}>
            {session.error}
          </p>
          <p style={{
            fontSize: '12px', color: '#9ca3af', marginTop: '16px'
          }}>
            Please consult a qualified immigration solicitor.
          </p>
        </div>
      )}

      {session.step === 'hard_gate' && (
        <HardGateScreen
          onSubmit={session.submitHardGate}
          loading={session.loading}
        />
      )}

      {session.step === 'questions' && session.currentQuestion && (
        <QuestionCard
          question={session.currentQuestion}
          onAnswer={session.submitAnswer}
          loading={session.loading}
        />
      )}

      {session.step === 'result' && session.result && (
        <ResultScreen
          result={session.result}
          route={session.route}
        />
      )}

      {session.step === 'questions' && !session.currentQuestion
       && !session.loading && (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <p style={{ color: '#6b7280' }}>Loading questions...</p>
        </div>
      )}

    </div>
  )
}
