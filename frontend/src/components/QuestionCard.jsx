import { useState } from 'react'
import * as api from '../api/client'

export default function QuestionCard({ 
  question, onAnswer, loading 
}) {
  const [answer, setAnswer] = useState('')
  const [explanation, setExplanation] = useState(null)
  const [loadingExplain, setLoadingExplain] = useState(false)

  const handleExplain = async () => {
    setLoadingExplain(true)
    try {
      const res = await api.explainRule(
        question.paragraph_ref,
        question.question_text
      )
      setExplanation(res.data.explanation)
    } catch {
      setExplanation('Unable to load explanation.')
    } finally {
      setLoadingExplain(false)
    }
  }

  const renderInput = () => {
    if (question.answer_type === 'boolean') {
      return (
        <div style={{ display: 'flex', gap: '12px' }}>
          {['Yes', 'No'].map(opt => (
            <button key={opt}
              onClick={() => setAnswer(opt.toLowerCase())}
              style={{
                flex: 1, padding: '12px',
                borderRadius: '8px', border: '2px solid',
                cursor: 'pointer', fontSize: '16px',
                fontWeight: '500',
                background: answer === opt.toLowerCase()
                  ? '#1e40af' : 'white',
                color: answer === opt.toLowerCase()
                  ? 'white' : '#374151',
                borderColor: answer === opt.toLowerCase()
                  ? '#1e40af' : '#d1d5db'
              }}
            >{opt}</button>
          ))}
        </div>
      )
    }

    if (question.answer_type === 'select' && 
        question.answer_options) {
      return (
        <select
          value={answer}
          onChange={e => setAnswer(e.target.value)}
          style={{
            width: '100%', padding: '12px',
            borderRadius: '8px', border: '1px solid #d1d5db',
            fontSize: '16px', background: 'white'
          }}
        >
          <option value="">Select an option...</option>
          {question.answer_options.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      )
    }

    return (
      <input
        type={question.answer_type === 'currency' 
              ? 'number' : 'text'}
        value={answer}
        onChange={e => setAnswer(e.target.value)}
        placeholder={
          question.answer_type === 'currency' 
          ? 'Enter amount in £' : 'Your answer...'
        }
        style={{
          width: '100%', padding: '12px',
          borderRadius: '8px', border: '1px solid #d1d5db',
          fontSize: '16px', boxSizing: 'border-box'
        }}
      />
    )
  }

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      {/* Progress bar */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{
          display: 'flex', justifyContent: 'space-between',
          marginBottom: '6px', fontSize: '13px', color: '#6b7280'
        }}>
          <span>Question {question.question_number} of {question.total_questions}</span>
          <span>{Math.round((question.question_number / question.total_questions) * 100)}%</span>
        </div>
        <div style={{
          height: '6px', background: '#e5e7eb',
          borderRadius: '999px', overflow: 'hidden'
        }}>
          <div style={{
            height: '100%', background: '#1e40af',
            borderRadius: '999px',
            width: `${(question.question_number / question.total_questions) * 100}%`,
            transition: 'width 0.3s ease'
          }}/>
        </div>
      </div>

      {/* Question */}
      <div style={{
        background: 'white', borderRadius: '12px',
        border: '1px solid #e5e7eb', padding: '24px',
        marginBottom: '16px', boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
      }}>
        {question.heading_context && (
          <p style={{ 
            fontSize: '12px', color: '#6b7280',
            textTransform: 'uppercase', letterSpacing: '0.05em',
            marginBottom: '8px'
          }}>
            {question.heading_context}
          </p>
        )}
        <h3 style={{ 
          fontSize: '18px', fontWeight: '600',
          color: '#111827', marginBottom: '20px', lineHeight: '1.5'
        }}>
          {question.question_text}
        </h3>

        {renderInput()}

        {/* Explain button */}
        <button
          onClick={handleExplain}
          disabled={loadingExplain}
          style={{
            marginTop: '12px', background: 'none',
            border: 'none', color: '#3b82f6',
            cursor: 'pointer', fontSize: '13px',
            padding: '0', textDecoration: 'underline'
          }}
        >
          {loadingExplain ? 'Loading...' : '💬 What does this mean?'}
        </button>

        {explanation && (
          <div style={{
            marginTop: '12px', padding: '12px',
            background: '#eff6ff', borderRadius: '8px',
            fontSize: '14px', color: '#1e40af',
            lineHeight: '1.6'
          }}>
            {explanation}
          </div>
        )}
      </div>

      <button
        onClick={() => onAnswer(answer)}
        disabled={loading || !answer || answer.trim() === ''}
        style={{
          width: '100%', padding: '14px',
          background: (!answer || answer.trim() === '' || loading) ? '#9ca3af' : '#1e40af',
          color: 'white', border: 'none',
          borderRadius: '8px', fontSize: '16px',
          fontWeight: '600',
          cursor: (!answer || answer.trim() === '' || loading) ? 'not-allowed' : 'pointer'
        }}
      >
        {loading ? 'Saving...' : 'Next Question →'}
      </button>

      <p style={{
        fontSize: '11px', color: '#9ca3af',
        textAlign: 'center', marginTop: '12px'
      }}>
        Ref: {question.paragraph_ref} | 
        This is a Preliminary Self-Assessment only.
      </p>
    </div>
  )
}
