import { useState, useEffect, useRef } from 'react';
import { useSession } from '../hooks/useSession';
import FlagWarning from './FlagWarning';
import HardGateScreen from './HardGateScreen';
import QuestionCard from './QuestionCard';
import ResultScreen from './ResultScreen';
import ChatMessage from './ChatMessage';

export default function ChatWindow() {
  const [userInput, setUserInput] = useState('');
  const [nationality, setNationality] = useState('');
  const [messages, setMessages] = useState([]);
  const [hardGateConversationComplete, setHardGateConversationComplete] = useState(false);
  const session = useSession();
  const lastAddedRef = useRef(null);

  useEffect(() => {
    if (session.route && messages.length === 0) {
      setMessages([
        { sender: 'assistant', text: `Great — I can see you're looking into ${session.route.replace(/_/g, ' ')}. Let me ask you a few questions to see if you're likely to be eligible. I'll guide you through everything step by step.` }
      ]);
    } else if (session.currentQuestion && session.currentQuestion.ref_id !== lastAddedRef.current) {
      lastAddedRef.current = session.currentQuestion.ref_id;
      setMessages(prev => [...prev, { 
        sender: 'assistant', 
        text: session.currentQuestion.question_text,
        hint: session.currentQuestion.plain_english_hint
      }]);
    } else if (session.step === 'clarify' && lastAddedRef.current !== 'clarify') {
      lastAddedRef.current = 'clarify';
      setMessages(prev => [...prev, { sender: 'assistant', text: session.clarifyingQuestion }]);
    }
  }, [session.route, session.currentQuestion, session.clarifyingQuestion, session.step]);

  const handleAnswer = (answer) => {
    if (session.loading) return;
    setMessages(prev => [...prev, { sender: 'user', text: answer }]);
    session.submitAnswer(answer);
  };

  const handleStart = async () => {
    if (!userInput.trim() || !nationality.trim()) return;
    await session.startSession(userInput, nationality.toUpperCase());
  };

  if (session.step === 'start') {
    return (
      <div className="chat-container">
        <header className="hero-section">
          <h1 className="hero-title">
            🇬🇧 UK Visa Eligibility
          </h1>
          <p className="hero-subtitle">
            AI-powered assessment to find your ideal immigration path in minutes.
          </p>
        </header>

        <div className="form-card">
          <div className="form-group">
            <label className="form-label">
              Why are you interested in coming to the UK?
            </label>
            <textarea
              value={userInput}
              onChange={e => setUserInput(e.target.value)}
              placeholder="e.g. I have a job offer from a company in London..."
              rows={3}
            />
          </div>

          <div className="form-group">
            <label className="form-label">
              Your nationality
            </label>
            <input
              value={nationality}
              onChange={e => setNationality(e.target.value)}
              placeholder="e.g. PK, US, IN"
              maxLength={2}
              style={{ textTransform: 'uppercase' }}
            />
          </div>

          <button
            className="btn-primary"
            onClick={handleStart}
            disabled={session.loading || !userInput || !nationality}
          >
            {session.loading ? (
              <>Analysing Intent...</>
            ) : (
              <>Check My Eligibility →</>
            )}
          </button>
        </div>

        <p className="footer-note">
          This is a Preliminary Self-Assessment only. Not legal advice.
        </p>
      </div>
    );
  }

  return (
    <div className="chat-container">
      {session.route && (
        <div style={{ marginBottom: '1rem' }}>
          <div className="route-badge">
            <span>🎯</span>
            <span>Route: {session.route.replace(/_/g, ' ')}</span>
          </div>
          {session.step !== 'result' && <FlagWarning flags={session.flags} />}
        </div>
      )}

      <div className="card chat-history">
        {messages.map((msg, index) => (
          <ChatMessage key={index} message={msg.text} sender={msg.sender} hint={msg.hint} />
        ))}
      </div>

      {session.step === 'error' && !hardGateConversationComplete && (
        <div className="card" style={{ borderColor: 'var(--error)', background: '#fffafb' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>⚠️</div>
          <h2 style={{ color: 'var(--error)', marginTop: 0 }}>
            Application Cannot Proceed
          </h2>
          <div style={{ background: 'white', padding: '1.25rem', borderRadius: '8px', border: '1px solid #fee2e2' }}>
            <p style={{ marginBottom: '1rem', color: '#7f1d1d' }}>
              {session.error}
            </p>
            <p style={{ fontWeight: '600', color: 'var(--primary)' }}>
              Recommendation: Consult a qualified immigration solicitor to review your specific situation.
            </p>
          </div>
        </div>
      )}

      {(session.step === 'hard_gate' || session.step === 'hard_fail_complete' || session.step === 'solicitor_review') && (
        <HardGateScreen
          onSubmit={session.submitHardGate}
          onContinue={session.continueToQuestions}
          questions={session.hardGateQuestions}
          step={session.step}
          flaggedGates={session.hardGateFlags}
          loading={session.loading}
          onHardGateConversationComplete={setHardGateConversationComplete}
        />
      )}

      {session.step === 'questions' && session.currentQuestion && session.step !== 'hard_fail_complete' && (
        <QuestionCard
          question={session.currentQuestion}
          onAnswer={handleAnswer}
          loading={session.loading}
        />
      )}

      {session.step === 'result' && session.result && session.step !== 'hard_fail_complete' && (
        <ResultScreen
          result={session.result}
          route={session.route}
          sessionId={session.sessionId}
          hardGateFlags={session.hardGateFlags}
          flags={session.flags}
        />
      )}

      {session.step === 'questions' && !session.currentQuestion
       && !session.loading && session.step !== 'hard_fail_complete' && (
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <p className="hero-subtitle">Preparing your assessment questions...</p>
        </div>
      )}
    </div>
  );
}
