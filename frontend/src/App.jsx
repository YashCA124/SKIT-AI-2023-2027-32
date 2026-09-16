import { useEffect, useState } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || window.location.origin

function App() {
  const [status, setStatus] = useState('checking')
  const [message, setMessage] = useState('Checking service health...')
  const [details, setDetails] = useState(null)

  useEffect(() => {
    let isMounted = true

    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/health`, {
          headers: {
            Accept: 'application/json',
          },
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        const data = await response.json()

        if (isMounted) {
          setStatus('online')
          setMessage('Backend is healthy')
          setDetails(data)
        }
      } catch (error) {
        if (isMounted) {
          setStatus('offline')
          setMessage('Backend unavailable')
          setDetails({ error: error.message })
        }
      }
    }

    checkHealth()

    return () => {
      isMounted = false
    }
  }, [])

  return (
    <div className="app-shell">
      <header className="status-bar">
        <span className={`status-badge status-badge--${status}`}>
          {status === 'online' ? 'Healthy' : status === 'offline' ? 'Offline' : 'Checking'}
        </span>
        <span className="status-text">{message}</span>
      </header>

      <main className="card">
        <p className="eyebrow">Parking App</p>
        <h1>Deployment Status</h1>
        <p className="subtext">Frontend mode: {import.meta.env.MODE}</p>

        {details && (
          <div className="meta">
            {details.service && (
              <p>
                <strong>Service:</strong> {details.service}
              </p>
            )}
            {details.environment && (
              <p>
                <strong>Environment:</strong> {details.environment}
              </p>
            )}
            {details.timestamp && (
              <p>
                <strong>Last check:</strong> {new Date(details.timestamp).toLocaleString()}
              </p>
            )}
            {details.error && (
              <p className="error">
                <strong>Issue:</strong> {details.error}
              </p>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

export default App
