import { useState } from 'react';

export default function QuestionCard({ question, onAnswer, loading }) {
  const [answer, setAnswer] = useState('');
  const [error, setError] = useState('');

  const isSocQuestion = question.question_text?.toLowerCase().includes('soc 2020');

  const handleLocalSubmit = () => {
    if (loading) return;

    if (isSocQuestion) {
      if (!/^\d{4}$/.test(answer)) {
        setError('Please enter a valid 4-digit SOC code.');
        return;
      }
    }

    if (!answer && question.answer_type !== 'boolean') {
      setError('Please provide an answer.');
      return;
    }

    setError('');
    onAnswer(answer);
  };

  return (
    <div className="card question-card">
      <h3 className="question-text">{question.question_text}</h3>
      
      {question.answer_type === 'boolean' && (
        <div className="options-grid">
          <button
            className="btn-option primary"
            onClick={() => !loading && onAnswer('Yes')}
            disabled={loading}
          >
            Yes
          </button>
          <button
            className="btn-option"
            onClick={() => !loading && onAnswer('No')}
            disabled={loading}
          >
            No
          </button>
        </div>
      )}

      {question.answer_type === 'select' && question.answer_options && (
        <div className="input-group">
          <select
            className="form-input"
            value={answer}
            onChange={(e) => {
              setAnswer(e.target.value);
              setError('');
            }}
            disabled={loading}
            style={{ width: '100%', padding: '0.875rem', borderRadius: '8px', border: '1px solid var(--border-light)' }}
          >
            <option value="">Select an option...</option>
            {question.answer_options.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
          {error && <div className="error-message">⚠️ {error}</div>}
          <button
            className="btn-primary"
            onClick={handleLocalSubmit}
            disabled={loading || !answer}
            style={{ marginTop: '1rem' }}
          >
            {loading ? 'Submitting...' : 'Continue →'}
          </button>
        </div>
      )}

      {['text', 'number', 'currency'].includes(question.answer_type) && (
        <div className="input-group">
          <input
            type={question.answer_type === 'currency' ? 'number' : 'text'}
            value={answer}
            onChange={e => {
              setAnswer(e.target.value);
              setError('');
            }}
            placeholder={isSocQuestion ? "e.g. 2135" : "Type your answer..."}
            disabled={loading}
          />
          {error && <div className="error-message">⚠️ {error}</div>}
          <button
            className="btn-primary"
            onClick={handleLocalSubmit}
            disabled={loading || !answer}
            style={{ marginTop: '1rem' }}
          >
            {loading ? 'Submitting...' : 'Continue →'}
          </button>
        </div>
      )}
    </div>
  );
}
