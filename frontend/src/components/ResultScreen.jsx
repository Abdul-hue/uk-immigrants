import FlagWarning from './FlagWarning';

export default function ResultScreen({ result, route, sessionId, hardGateFlags = [], flags = [] }) {
  const hasHardGateFlags = hardGateFlags.length > 0;
  const isPass = result.overall_result === 'PASS' && !hasHardGateFlags;
  const isFail = result.overall_result === 'FAIL';
  const isConditional = hasHardGateFlags;

  const HARD_GATE_EXPLANATIONS = { 
    criminality: { 
      heading: "Criminal Convictions & UK Entry", 
      citation: "Part Suitability, Section S-EC.1.5", 
      explanation: `Under Part Suitability (S-EC.1.5 to S-EC.1.9), the UK Home Office assesses criminal convictions based on nature, sentence, and rehabilitation. Convictions resulting in custodial sentences of 12 months or more typically lead to automatic refusal.`, 
      nextSteps: "A qualified immigration solicitor can review your specific conviction details and advise whether any exceptions apply." 
    }, 
    deportation: { 
      heading: "Previous Deportation or Exclusion Order", 
      citation: "Part Suitability, Section S-EC.2.1", 
      explanation: `Under Part Suitability (S-EC.2.1), individuals subject to a current deportation order or exclusion order are automatically refused entry to the UK. This is a mandatory ground for refusal.`, 
      nextSteps: "A solicitor is needed to verify your status with the Home Office before any application can proceed." 
    }, 
    deception: { 
      heading: "Previous Deception in UK Applications", 
      citation: "Part Suitability, Section S-EC.3.1", 
      explanation: `The use of deception in a previous UK immigration application results in automatic refusal. The ban period can range from 1 to 10 years.`, 
      nextSteps: "A solicitor can check whether your ban period has expired and advise on eligibility." 
    }, 
    immigration_debt: { 
      heading: "Outstanding Immigration Debt", 
      citation: "Part Suitability, Section S-EC.4.1", 
      explanation: `Applicants with unpaid litigation costs or other debts to the Home Office must settle these before a new application can be approved.`, 
      nextSteps: "Contact the Home Office debt management team to verify the amount owed and arrange payment." 
    }, 
    overstay: { 
      heading: "Previous Overstay in the UK", 
      citation: "Part Suitability, Section S-EC.5.1", 
      explanation: `Overstaying your visa by more than 90 days can trigger a re-entry ban of 1 to 10 years depending on the duration.`, 
      nextSteps: "A solicitor can calculate whether your ban period has elapsed." 
    } 
  };

  const handleExport = () => {
    window.open(`/api/session/${sessionId}/export`, '_blank')
  }

  return (
    <div className="result-container" style={{ paddingBottom: '3rem' }}>
      {/* Result Header */}
      <div className="card" style={{
        textAlign: 'center',
        background: isPass ? '#f0fdf4' : isFail ? '#fef2f2' : '#fffbeb',
        borderColor: isPass ? '#bbf7d0' : isFail ? '#fecaca' : '#fde68a',
        padding: '2.5rem'
      }}>
        <div style={{ fontSize: '3.5rem', marginBottom: '1rem' }}>
          {isPass ? '✅' : isFail ? '❌' : '⚠️'}
        </div>
        <h2 style={{
          fontSize: '1.875rem', fontWeight: '800', margin: 0,
          color: isPass ? '#166534' : isFail ? '#991b1b' : '#92400e'
        }}>
          Assessment Result
        </h2>
        <p style={{ 
          fontSize: '1.125rem', fontWeight: '600', 
          color: isPass ? '#15803d' : isFail ? '#b91c1c' : '#b45309',
          marginTop: '0.5rem', marginBottom: 0
        }}>
          {isConditional ? 'Further Legal Review Required' : isPass ? 'Potentially Eligible' : 'Likely Ineligible'}
        </p>
        <div className="route-badge" style={{ marginTop: '1.5rem' }}>
          Route: {route?.replace(/_/g, ' ')}
        </div>
      </div>

      <FlagWarning flags={flags} />

      {/* Assessment Summary */}
      <section style={{ margin: '2rem 0' }}>
        <h3 className="form-label" style={{ fontSize: '1.125rem', borderBottom: '2px solid var(--border-light)', paddingBottom: '0.5rem' }}>
          Assessment Summary
        </h3>
        <p style={{ lineHeight: '1.6', marginTop: '1rem' }}>
          Based on your responses, you meet the primary criteria for the {route?.replace(/_/g, ' ')} route. 
          {isConditional && (
            <span style={{ fontWeight: '700', color: '#b45309' }}> However, {hardGateFlags.length} area(s) have been flagged for professional legal review.</span>
          )}
        </p>
      </section>

      {/* Flagged Issues Section */}
      {isConditional && (
        <section style={{ margin: '2rem 0' }}>
          <h3 className="form-label" style={{ fontSize: '1.125rem', color: '#b45309' }}>
            ⚠️ Flagged for Solicitor Review
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
            {hardGateFlags.map((flag, idx) => {
              const gateInfo = HARD_GATE_EXPLANATIONS[flag.type];
              return (
                <div key={idx} className="card" style={{ margin: 0, borderLeft: '4px solid #f59e0b' }}>
                  <div style={{ fontWeight: '700', color: '#1e293b' }}>{gateInfo?.heading}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>Basis: {flag.paragraph_ref || gateInfo?.citation}</div>
                  <div style={{ fontSize: '0.875rem', background: '#f8fafc', padding: '0.75rem', borderRadius: '6px' }}>
                    <strong>Your Disclosure:</strong> {flag.userDetails || flag.userDisclosureSummary || 'Information provided during screening.'}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Passed Checks */}
      <section style={{ margin: '2rem 0' }}>
        <h3 className="form-label" style={{ fontSize: '1.125rem' }}>Route Compliance</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '1rem' }}>
          {result.summary?.filter(item => item.result === 'PASS').map((item, index) => (
            <div key={index} style={{
              display: 'flex', gap: '0.75rem', alignItems: 'flex-start',
              padding: '0.75rem', background: 'white', borderRadius: '8px', border: '1px solid var(--border-light)'
            }}>
              <span style={{ color: 'var(--success)' }}>✓</span>
              <div>
                <div style={{ fontSize: '0.875rem', fontWeight: '600' }}>{item.question}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Confirmed: {item.answer}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Action Area */}
      <div className="card" style={{ background: '#f1f5f9', borderColor: 'transparent', marginTop: '2rem' }}>
        <h3 className="form-label" style={{ color: 'var(--primary)', marginBottom: '1rem' }}>Recommended Next Steps</h3>
        <ul style={{ paddingLeft: '1.25rem', margin: 0, fontSize: '0.9375rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <li>Consult with a qualified UK immigration solicitor.</li>
          <li>Gather evidence supporting your {route?.replace(/_/g, ' ')} application.</li>
          <li>Review the full report for detailed compliance breakdown.</li>
        </ul>
        <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
          <button
            className="btn-primary"
            onClick={() => window.open('https://solicitors.lawsociety.org.uk/', '_blank')}
          >
            Connect with a Solicitor
          </button>
          <button
            className="btn-option"
            onClick={handleExport}
            style={{ flex: 1 }}
          >
            📄 Export Report
          </button>
        </div>
      </div>

      <p className="footer-note" style={{ maxWidth: 'none', textAlign: 'left', background: '#f8fafc', padding: '1rem', borderRadius: '8px' }}>
        ⚖️ <strong>Disclaimer:</strong> {result.disclaimer}
      </p>
    </div>
  )
}
