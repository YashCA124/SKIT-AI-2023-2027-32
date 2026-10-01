import { useCallback, useEffect, useState } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || window.location.origin

async function fetchService(path, signal) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Accept: 'application/json' },
    signal,
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  return response.json()
}

function App() {
  const [healthStatus, setHealthStatus] = useState('checking')
  const [healthDetails, setHealthDetails] = useState(null)
  const [readiness, setReadiness] = useState({ status: 'checking', details: null })
  const [lastChecked, setLastChecked] = useState(null)

  const checkServices = useCallback(async (signal) => {
    const [healthResult, readinessResult] = await Promise.allSettled([
      fetchService('/health', signal),
      fetchService('/ready', signal),
    ])

    if (signal?.aborted) {
      return
    }

    if (healthResult.status === 'fulfilled') {
      setHealthStatus('online')
      setHealthDetails(healthResult.value)
    } else {
      setHealthStatus('offline')
      setHealthDetails({
        error: healthResult.reason instanceof Error ? healthResult.reason.message : 'Request failed',
      })
    }

    if (readinessResult.status === 'fulfilled') {
      const details = readinessResult.value
      setReadiness({
        status: details.database_configured ? 'ready' : 'degraded',
        details,
      })
    } else {
      setReadiness({ status: 'unavailable', details: null })
    }

    setLastChecked(new Date())
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    const request = window.setTimeout(() => checkServices(controller.signal), 0)

    return () => {
      window.clearTimeout(request)
      controller.abort()
    }
  }, [checkServices])

  const handleRefresh = () => {
    setHealthStatus('checking')
    setReadiness({ status: 'checking', details: null })
    checkServices()
  }

  const statusCopy = {
    checking: { label: 'Checking', message: 'Checking service health…' },
    online: { label: 'Healthy', message: 'API is responding normally' },
    offline: { label: 'Offline', message: 'Unable to reach the API' },
  }
  const readinessCopy = {
    checking: 'Checking…',
    ready: 'Configured',
    degraded: 'Not configured',
    unavailable: 'Unavailable',
  }
  const currentStatus = statusCopy[healthStatus]

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

        <section className={`status-card status-card--${healthStatus}`} aria-live="polite">
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
            onClick={handleRefresh}
            disabled={healthStatus === 'checking'}
          >
            {healthStatus === 'checking' ? 'Checking…' : 'Check again'}
          </button>
        </section>

        <section className="details-card" aria-label="Service details">
          <div className="detail-row">
            <span>Service</span>
            <strong>{healthDetails?.service || 'Parking API'}</strong>
          </div>
          <div className="detail-row">
            <span>Environment</span>
            <strong>{healthDetails?.environment || import.meta.env.MODE}</strong>
          </div>
          <div className="detail-row">
            <span>Database configuration</span>
            <strong className={`readiness-value readiness-value--${readiness.status}`}>
              {readinessCopy[readiness.status]}
            </strong>
          </div>
          <div className="detail-row">
            <span>Last checked</span>
            <strong>{lastChecked ? lastChecked.toLocaleTimeString() : 'Not checked yet'}</strong>
          </div>
          {healthDetails?.error && <p className="error">API issue: {healthDetails.error}</p>}
          {readiness.status === 'unavailable' && (
            <p className="error">Readiness information could not be retrieved.</p>
          )}
        </section>
      </main>

      <footer className="footer">Parking platform · API endpoints /health and /ready</footer>
    </div>
  )
}

export default App
