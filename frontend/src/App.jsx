import { useCallback, useEffect, useState } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || window.location.origin

function App() {
  const [status, setStatus] = useState('checking')
  const [details, setDetails] = useState(null)
  const [lastChecked, setLastChecked] = useState(null)

  const checkHealth = useCallback(async (signal) => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        headers: { Accept: 'application/json' },
        signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()

      if (!signal?.aborted) {
        setStatus('online')
        setDetails(data)
        setLastChecked(new Date())
      }
    } catch (error) {
      if (!signal?.aborted && error.name !== 'AbortError') {
        setStatus('offline')
        setDetails({ error: error.message })
        setLastChecked(new Date())
      }
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    const request = window.setTimeout(() => checkHealth(controller.signal), 0)

    return () => {
      window.clearTimeout(request)
      controller.abort()
    }
  }, [checkHealth])

  const statusCopy = {
    checking: { label: 'Checking', message: 'Checking service health…' },
    online: { label: 'Healthy', message: 'All systems operational' },
    offline: { label: 'Offline', message: 'Unable to reach the backend' },
  }
  const currentStatus = statusCopy[status]

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">P</span>
          <span>Parkwise</span>
        </div>
        <span className="environment-tag">{import.meta.env.MODE}</span>
      </header>

      <main className="dashboard">
        <section className="hero">
          <p className="eyebrow">System overview</p>
          <h1>Service status</h1>
          <p className="subtext">A quick look at the parking platform’s availability.</p>
        </section>

        <section className={`status-card status-card--${status}`} aria-live="polite">
          <div className="status-heading">
            <span className="status-indicator" aria-hidden="true" />
            <div>
              <p className="status-label">{currentStatus.label}</p>
              <p className="status-message">{currentStatus.message}</p>
            </div>
          </div>
          <button
            className="refresh-button"
            type="button"
            onClick={() => {
              setStatus('checking')
              checkHealth()
            }}
            disabled={status === 'checking'}
          >
            {status === 'checking' ? 'Checking…' : 'Check again'}
          </button>
        </section>

        <section className="details-card" aria-label="Service details">
          <div className="detail-row">
            <span>Service</span>
            <strong>{details?.service || 'Parking API'}</strong>
          </div>
          <div className="detail-row">
            <span>Environment</span>
            <strong>{details?.environment || import.meta.env.MODE}</strong>
          </div>
          <div className="detail-row">
            <span>Last checked</span>
            <strong>{lastChecked ? lastChecked.toLocaleTimeString() : 'Not checked yet'}</strong>
          </div>
          {details?.error && <p className="error">Issue: {details.error}</p>}
        </section>
      </main>

      <footer className="footer">Parking platform · API endpoint {API_BASE_URL}/health</footer>
    </div>
  )
}

export default App
