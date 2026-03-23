export default function ResultScreen({ result, route }) {
  const isPass = result.overall_result === 'PASS'
  const isFail = result.overall_result === 'FAIL'

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      {/* Result banner */}
      <div style={{
        background: isPass ? '#dcfce7' : isFail 
                    ? '#fee2e2' : '#fef3c7',
        border: `2px solid ${isPass ? '#16a34a' 
                : isFail ? '#dc2626' : '#f59e0b'}`,
        borderRadius: '12px', padding: '24px',
        textAlign: 'center', marginBottom: '24px'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '8px' }}>
          {isPass ? '✅' : isFail ? '❌' : '⚠️'}
        </div>
        <h2 style={{
          fontSize: '24px', fontWeight: '700',
          color: isPass ? '#16a34a' 
                 : isFail ? '#dc2626' : '#d97706'
        }}>
          {isPass ? 'Potentially Eligible' 
           : isFail ? 'Likely Ineligible' 
           : 'Further Review Needed'}
        </h2>
        <p style={{ color: '#6b7280', marginTop: '8px' }}>
          Route: {route?.replace('_', ' ')}
        </p>
      </div>

      {/* Failed rules */}
      {result.rules_failed?.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ color: '#dc2626', marginBottom: '8px' }}>
            ❌ Failed Checks
          </h3>
          {result.rules_failed.map(ref => (
            <div key={ref} style={{
              padding: '10px 14px', background: '#fee2e2',
              borderRadius: '6px', marginBottom: '6px',
              fontSize: '14px', color: '#991b1b'
            }}>
              {ref}
            </div>
          ))}
        </div>
      )}

      {/* Passed rules */}
      {result.rules_passed?.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ color: '#16a34a', marginBottom: '8px' }}>
            ✅ Passed Checks
          </h3>
          {result.rules_passed.map(ref => (
            <div key={ref} style={{
              padding: '10px 14px', background: '#dcfce7',
              borderRadius: '6px', marginBottom: '6px',
              fontSize: '14px', color: '#166534'
            }}>
              {ref}
            </div>
          ))}
        </div>
      )}

      {/* Document checklist */}
      {result.checklist_items?.length > 0 && (
        <div style={{
          background: '#f8fafc', border: '1px solid #e2e8f0',
          borderRadius: '12px', padding: '20px',
          marginBottom: '20px'
        }}>
          <h3 style={{ 
            color: '#1e40af', marginBottom: '12px' 
          }}>
            📋 Documents You Will Need
          </h3>
          {result.checklist_items.map((item, i) => (
            <div key={i} style={{
              display: 'flex', gap: '10px',
              padding: '8px 0',
              borderBottom: i < result.checklist_items.length - 1 
                ? '1px solid #e5e7eb' : 'none'
            }}>
              <span>📄</span>
              <span style={{ fontSize: '14px' }}>{item}</span>
            </div>
          ))}
        </div>
      )}

      {/* Disclaimer */}
      <div style={{
        background: '#f1f5f9', borderRadius: '8px',
        padding: '16px', fontSize: '12px',
        color: '#64748b', lineHeight: '1.6'
      }}>
        ⚖️ {result.disclaimer}
      </div>
    </div>
  )
}
