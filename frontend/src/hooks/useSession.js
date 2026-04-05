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
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [hardGateFlags, setHardGateFlags] = useState([])
  const [hardGateQuestions, setHardGateQuestions] = useState([])

  const startSession = async (userInput, nationality) => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    setLoading(true)
    setError(null)
    try {
      const res = await api.startSession(userInput, nationality)
      const data = res.data
      setSessionId(data.session_id)
      setRoute(data.route)
      setFlags(data.flags_2026)
      setFlagWarnings(data.flag_warnings || [])
      setHardGateQuestions(data.hard_gate_questions || [])
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
      setIsSubmitting(false);
    }
  }

  const summarizeDisclosure = (userDetails) => {
    const text = userDetails.toLowerCase();
    if (text.includes('prison') || text.includes('jail') || text.includes('custodial')) {
      return 'Custodial conviction disclosed';
    } else if (text.includes('fine') || text.includes('community') || text.includes('probation')) {
      return 'Non-custodial conviction disclosed';
    } else if (text.includes('deport') || text.includes('exclusion')) {
      return 'Previous deportation or exclusion order disclosed';
    } else if (text.includes('false') || text.includes('document') || text.includes('deception')) {
      return 'Previous use of deception or false documents disclosed';
    } else if (text.includes('debt') || text.includes('owe') || text.includes('home office')) {
      return 'Outstanding immigration debt disclosed';
    } else if (text.includes('overstay')) {
      return 'Previous overstay in the UK disclosed';
    }
    return 'Detailed circumstances provided';
  };

  const submitHardGate = async (answers, forceHardFail = false, detailsMap = null) => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    setLoading(true)
    try {
      const res = await api.submitHardGate(sessionId, answers)
      const data = res.data
      
      // Store flagged_gates from response in session state with user disclosure details where possible
      if (data.flagged_gates && data.flagged_gates.length > 0) {
        const nameToType = (n) => {
          const map = {
            CRIMINALITY: 'criminality',
            DECEPTION: 'deception',
            DEPORTATION: 'deportation',
            DEPORTATION_ORDER: 'deportation',
            IMMIGRATION_DEBT: 'immigration_debt',
            OVERSTAY: 'overstay'
          }
          return map[n] || (n ? n.toLowerCase() : 'other')
        }
        const nameToKey = (n) => {
          const map = {
            CRIMINALITY: 'has_criminal_conviction',
            DECEPTION: 'has_used_deception',
            DEPORTATION: 'has_deportation_order',
            DEPORTATION_ORDER: 'has_deportation_order',
            IMMIGRATION_DEBT: 'has_immigration_debt',
            OVERSTAY: 'has_overstayed_90_days'
          }
          return map[n] || null
        }
        const transformed = data.flagged_gates.map(g => {
          const key = nameToKey(g.gate_name)
          const detailText = (detailsMap && key) ? (detailsMap[key] || '') : ''
          return {
            type: nameToType(g.gate_name),
            paragraph_ref: g.paragraph_ref,
            fail_message: g.fail_message,
            userDetails: detailText,
            userDisclosureSummary: detailText ? summarizeDisclosure(detailText) : ''
          }
        })
        setHardGateFlags(transformed);
      }

      if (data.result === 'HARD_FAIL' || forceHardFail) {
        setStep('hard_fail_complete')
        setError(data.fail_message)
        return data
      }
      
      if (!data.session_can_continue) {
        setStep('error')
        setError(data.fail_message)
        return data
      }

      // Branch on next_step from backend
      if (data.next_step === 'questions') {
        // ONLY call loadNextQuestion if next_step is questions
        await loadNextQuestion(true)
      } else if (data.next_step === 'solicitor_review') {
        // next_step: "solicitor_review" means wait for user choice
        setStep('solicitor_review')
      } else if (data.next_step === 'ended') {
        setStep('hard_fail_complete')
      }
      
      return data
    } catch (err) {
      setError('Hard gate evaluation failed.')
    } finally {
      setLoading(false)
      setIsSubmitting(false);
    }
  }

  const continueToQuestions = async () => {
    // Manually trigger question loading after a flagged gate choice
    if (isSubmitting) return;
    setIsSubmitting(true);
    setLoading(true);
    try {
      await loadNextQuestion(true);
    } finally {
      setLoading(false);
      setIsSubmitting(false);
    }
  };

  const loadNextQuestion = async (isInternal = false) => {
    if (!isInternal && (step !== 'hard_gate' && step !== 'questions' && step !== 'solicitor_review')) return;
    if (!isInternal && isSubmitting) return;
    if (!isInternal) setIsSubmitting(true);
    
    try {
      const res = await api.getNextQuestion(sessionId)
      
      // Check for completion signal
      if (res.data?.complete === true) {
        await loadResult(true)
        return
      }
      
      if (res.status === 204) {
        await loadResult(true)
        return
      }
      
      setCurrentQuestion(res.data)
      setStep('questions')
      
    } catch (err) {
      if (err.response?.status === 204) {
        await loadResult(true)
      } else {
        console.error('Question load error:', err.response || err)
        setError('Failed to load next question.')
      }
    } finally {
      if (!isInternal) setIsSubmitting(false);
    }
  }

  const submitAnswer = async (answer) => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    setLoading(true)
    try {
      const res = await api.submitAnswer(
        sessionId,
        currentQuestion.ref_id, // Use ref_id instead of paragraph_ref
        answer
      )
      if (res.data.next_step === 'complete') {
        await loadResult(true)
      } else {
        await loadNextQuestion(true)
      }
    } catch (err) {
      setError('Failed to submit answer.')
    } finally {
      setLoading(false)
      setIsSubmitting(false);
    }
  }

  const loadResult = async (isInternal = false) => {
    if (!isInternal && isSubmitting) return;
    if (!isInternal) setIsSubmitting(true);
    try {
      const res = await api.getResult(sessionId)
      setResult(res.data)
      setStep('result')
    } finally {
      if (!isInternal) setIsSubmitting(false);
    }
  }

  const clarifySession = async (clarifiedInput, nat) => {
    setNeedsClarification(false)
    setClarifyingQuestion(null)
    await startSession(clarifiedInput, nat)
  }

  return {
    sessionId, route, flags, step, currentQuestion,
    result, loading, error, flagWarnings, hardGateFlags, hardGateQuestions,
    startSession, submitHardGate, submitAnswer, continueToQuestions,
    clarifyingQuestion, needsClarification, clarifySession
  }
}
