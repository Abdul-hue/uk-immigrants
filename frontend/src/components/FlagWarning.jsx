export default function FlagWarning({ flags }) {
  if (!flags || flags.length === 0) return null
  
  const flagMessages = {
    'B2_ENGLISH_UPDATE': {
      label: '2026 English Update',
      message: 'English requirement raised to B2 level from 8 Jan 2026.',
      color: '#f59e0b'
    },
    'SETTLEMENT_10YR': {
      label: '2026 Settlement Change', 
      message: 'Settlement now requires 10 years on this route from April 2026.',
      color: '#f59e0b'
    },
    'ETA_MANDATORY': {
      label: 'ETA Required',
      message: 'Your nationality requires an ETA from 25 Feb 2026.',
      color: '#ef4444'
    }
  }

  return (
    <div style={{ marginBottom: '16px' }}>
      {flags.map(flag => {
        const info = flagMessages[flag]
        if (!info) return null
        return (
          <div key={flag} style={{
            background: '#fef3c7',
            border: `1px solid ${info.color}`,
            borderRadius: '8px',
            padding: '12px',
            marginBottom: '8px',
            display: 'flex',
            gap: '8px'
          }}>
            <span>⚠️</span>
            <div>
              <strong style={{ color: info.color }}>
                {info.label}
              </strong>
              <p style={{ margin: '4px 0 0', fontSize: '14px' }}>
                {info.message}
              </p>
            </div>
          </div>
        )
      })}
    </div>
  )
}
