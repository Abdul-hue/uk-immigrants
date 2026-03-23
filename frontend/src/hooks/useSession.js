import { useState } from 'react'
import * as api from '../api/client'

export function useSession() {
  const [sessionId, setSessionId] = useState(null)
  const [route, setRoute] = useState(null)
  const [flags, setFlags] = useState([])
  const [step, setStep] = useState('start')
  // steps: start | hard_gate | questions | result | error
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [flagWarnings, setFlagWarnings] = useState([])
  const [clarifyingQuestion, setClarifyingQuestion] = useState(null)
  const [needsClarification, setNeedsClarification] = useState(false)

  const startSession = async (userInput, nationality) => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.startSession(userInput, nationality)
      const data = res.data
      setSessionId(data.session_id)
      setRoute(data.route)
      setFlags(data.flags_2026)
      setFlagWarnings(data.flag_warnings || [])
      setStep('hard_gate')
      return data
    } catch (err) {
      if (err.response?.status === 422) {
        const detail = err.response.data.detail
        if (detail.status === 'NEEDS_CLARIFICATION') {
          setClarifyingQuestion(detail.clarifying_question)
          setNeedsClarification(true)
          setStep('clarify')
          return detail
        }
      }
      setError('Failed to start session. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const submitHardGate = async (answers) => {
    setLoading(true)
    try {
      const res = await api.submitHardGate(sessionId, answers)
      const data = res.data
      if (!data.session_can_continue) {
        setStep('error')
        setError(data.fail_message)
        return data
      }
      // Load first question
      await loadNextQuestion()
      return data
    } catch (err) {
      setError('Hard gate evaluation failed.')
    } finally {
      setLoading(false)
    }
  }

  const loadNextQuestion = async () => {
    try {
      const res = await api.getNextQuestion(sessionId)
      
      // Check for completion signal
      if (res.data?.complete === true) {
        await loadResult()
        return
      }
      
      if (res.status === 204) {
        await loadResult()
        return
      }
      
      setCurrentQuestion(res.data)
      setStep('questions')
      
    } catch (err) {
      if (err.response?.status === 204) {
        await loadResult()
      } else {
        console.error('Question load error:', err.response || err)
        setError('Failed to load next question.')
      }
    }
  }

  const submitAnswer = async (answer) => {
    setLoading(true)
    try {
      const res = await api.submitAnswer(
        sessionId,
        currentQuestion.paragraph_ref,
        answer
      )
      if (res.data.next_step === 'complete') {
        await loadResult()
      } else {
        await loadNextQuestion()
      }
    } catch (err) {
      setError('Failed to submit answer.')
    } finally {
      setLoading(false)
    }
  }

  const loadResult = async () => {
    const res = await api.getResult(sessionId)
    setResult(res.data)
    setStep('result')
  }

  const clarifySession = async (clarifiedInput, nat) => {
    setNeedsClarification(false)
    setClarifyingQuestion(null)
    await startSession(clarifiedInput, nat)
  }

  return {
    sessionId, route, flags, step, currentQuestion,
    result, loading, error, flagWarnings,
    startSession, submitHardGate, submitAnswer,
    clarifyingQuestion, needsClarification, clarifySession
  }
}
