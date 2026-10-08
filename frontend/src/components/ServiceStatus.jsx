import { useEffect, useState } from 'react'
import { apiRequest } from '../api/client.js'
import Alert from './Alert.jsx'
import './ServiceStatus.css'

export default function ServiceStatus() {
  const [checkVersion, setCheckVersion] = useState(0)
  const [status, setStatus] = useState({
    health: 'checking',
    readiness: 'checking',
    service: null,
    environment: null,
    lastChecked: null,
    error: '',
  })

  useEffect(() => {
    const controller = new AbortController()
    async function checkServices() {
      const [health, readiness] = await Promise.allSettled([
        apiRequest('/health', { signal: controller.signal }),
        apiRequest('/ready', { signal: controller.signal }),
      ])
      if (controller.signal.aborted) return
      setStatus({
        health: health.status === 'fulfilled' ? 'healthy' : 'unavailable',
        readiness: readiness.status === 'fulfilled'
          ? readiness.value.database_configured ? 'configured' : 'not configured'
          : 'unavailable',
        service: health.status === 'fulfilled' ? health.value.service : null,
        environment: health.status === 'fulfilled' ? health.value.environment : null,
        lastChecked: new Date(),
        error: health.status === 'rejected' ? health.reason.message : '',
      })
    }
    checkServices()
    return () => controller.abort()
  }, [checkVersion])

  return (
    <section className="service-panel" aria-labelledby="service-title">
      <div className="service-panel__heading">
        <div><p className="eyebrow">Platform</p><h2 id="service-title">Service status</h2></div>
        <button className="secondary-button" type="button" onClick={() => setCheckVersion((version) => version + 1)} disabled={status.health === 'checking'}>
          {status.health === 'checking' ? 'Checking…' : 'Check again'}
        </button>
      </div>
      <div className={`service-state service-state--${status.health}`} role="status">
        <span className="service-state__dot" />
        <span><strong>{status.health === 'checking' ? 'Checking' : status.health === 'healthy' ? 'Healthy' : 'Unavailable'}</strong><small>{status.health === 'healthy' ? 'The API health endpoint is responding.' : status.health === 'checking' ? 'Checking service health…' : 'Unable to reach the API health endpoint.'}</small></span>
      </div>
      <dl className="service-details">
        <div><dt>Service</dt><dd>{status.service || 'Not available'}</dd></div>
        <div><dt>Environment</dt><dd>{status.environment || import.meta.env.MODE}</dd></div>
        <div><dt>Database</dt><dd>{status.readiness}</dd></div>
        <div><dt>Last checked</dt><dd>{status.lastChecked ? status.lastChecked.toLocaleTimeString() : 'Not checked yet'}</dd></div>
      </dl>
      {status.error && <Alert>{status.error}</Alert>}
      {status.readiness === 'unavailable' && <Alert>Readiness information could not be retrieved.</Alert>}
    </section>
  )
}
