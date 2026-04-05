import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
})

export const startSession = (userInput, nationalityIso) =>
  api.post('/session/start', {
    user_input: userInput,
    nationality_iso: nationalityIso
  })

export const submitHardGate = (sessionId, answers) =>
  api.post('/session/hard-gate', {
    session_id: sessionId,
    ...answers
  })

export const getNextQuestion = (sessionId) =>
  api.get(`/questions/next/${sessionId}`)

export const submitAnswer = (sessionId, refId, answer) =>
  api.post('/questions/answer', {
    session_id: sessionId,
    ref_id: refId,
    paragraph_ref: refId, // Keep for backward compatibility
    answer: answer
  })

export const getResult = (sessionId) =>
  api.get(`/questions/result/${sessionId}`)

export const explainRule = (refId, question) =>
  api.post('/explain/', {
    paragraph_ref: refId,
    question: question
  })
