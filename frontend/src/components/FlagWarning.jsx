export default function FlagWarning({ flags }) {
  if (!flags || flags.length === 0) return null
  
  const flagMessages = {
    'B2_ENGLISH_UPDATE': {
      label: '2026 English Update',
      message: 'English requirement raised to B2 level from 8 Jan 2026.',
      type: 'warning'
    },
    'SETTLEMENT_10YR': {
      label: '2026 Settlement Change', 
      message: 'Settlement now requires 10 years on this route from April 2026.',
      type: 'warning'
    },
    'ETA_MANDATORY': {
      label: 'ETA Required',
      message: 'Your nationality requires an ETA from 25 Feb 2026.',
      type: 'error'
    }
  }

  return (
    <div className="flag-container">
      {flags.map(flag => {
        const info = flagMessages[flag]
        if (!info) return null
        return (
          <div key={flag} className={`alert alert-${info.type}`}>
            <span style={{ fontSize: '1.25rem' }}>
              {info.type === 'error' ? '🚫' : '⚠️'}
            </span>
            <div>
              <span className="alert-title">{info.label}</span>
              <p className="alert-message">{info.message}</p>
            </div>
          </div>
        )
      })}
    </div>
  )
}
