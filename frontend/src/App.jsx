import { useCallback, useEffect, useState } from 'react'
import './App.css'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || window.location.origin).replace(/\/+$/, '')
const SESSION_KEY = 'parkwise.auth.session.v1'

class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function readResponse(response) {
  let data

  try {
    data = await response.json()
  } catch {
    data = null
  }

  if (!response.ok) {
    const detail = data?.detail
    const message = Array.isArray(detail)
      ? detail.map((issue) => issue.msg).filter(Boolean).join(' ')
      : typeof detail === 'string'
        ? detail
        : data?.message

    throw new ApiError(message || `The request failed (HTTP ${response.status}).`, response.status)
  }

  if (data === null) {
    throw new Error('The API returned an unreadable response.')
  }

  return data
}

async function apiRequest(path, options = {}) {
  const headers = { Accept: 'application/json', ...options.headers }

  if (options.body) {
    headers['Content-Type'] = 'application/json'
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  return readResponse(response)
}

function Brand() {
  return (
    <div className="brand">
      <span className="brand-mark" aria-hidden="true">P</span>
      <span>Parkwise</span>
    </div>
  )
}

function Alert({ children, kind = 'error' }) {
  if (!children) return null

  return (
    <p className={`notice notice--${kind}`} role={kind === 'error' ? 'alert' : 'status'}>
      {children}
    </p>
  )
}

function LoginForm({ onSubmit, onRegister, pending, notice, noticeType }) {
  return (
    <section className="auth-card" aria-labelledby="login-title">
      <p className="eyebrow">Welcome back</p>
      <h2 id="login-title">Sign in</h2>
      <p className="form-intro">Use your Parkwise account to continue.</p>
      <Alert kind={noticeType}>{notice}</Alert>
      <form onSubmit={onSubmit}>
        <label>
          Email address
          <input
            name="email"
            type="email"
            autoComplete="email"
            required
            maxLength={100}
            placeholder="you@example.com"
          />
        </label>
        <label>
          Password
          <input
            name="password"
            type="password"
            autoComplete="current-password"
            required
          />
        </label>
        <button className="primary-button" type="submit" disabled={pending}>
          {pending ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
      <p className="switch-prompt">
        New to Parkwise?{' '}
        <button className="text-button" type="button" onClick={onRegister}>
          Create an account
        </button>
      </p>
    </section>
  )
}

function getBrowserLocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Location access is not supported by this browser.'))
      return
    }

    navigator.geolocation.getCurrentPosition(
      ({ coords }) => resolve({ latitude: coords.latitude, longitude: coords.longitude }),
      (error) => {
        const message = error.code === error.PERMISSION_DENIED
          ? 'Location permission was denied. Allow location access or turn off the location option.'
          : error.code === error.TIMEOUT
            ? 'Location lookup timed out. Please try again.'
            : 'Your location is unavailable. Please try again or turn off the location option.'
        reject(new Error(message))
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 },
    )
  })
}

function RegistrationForm({ onSubmit, onLogin, pending, notice, noticeType }) {
  const [shareLocation, setShareLocation] = useState(false)

  return (
    <section className="auth-card" aria-labelledby="register-title">
      <p className="eyebrow">Get started</p>
      <h2 id="register-title">Create account</h2>
      <p className="form-intro">A few details to set up your Parkwise account.</p>
      <Alert kind={noticeType}>{notice}</Alert>
      <form
        onSubmit={async (event) => {
          event.preventDefault()
          const formData = new FormData(event.currentTarget)
          const payload = {
            name: formData.get('name').trim(),
            email: formData.get('email').trim(),
            phone_no: formData.get('phone_no').trim(),
            password: formData.get('password'),
            city: formData.get('city').trim(),
            state: formData.get('state').trim(),
            country: formData.get('country').trim().toUpperCase(),
            location_permission_granted: shareLocation,
          }

          try {
            if (shareLocation) {
              Object.assign(payload, await getBrowserLocation())
            }
            await onSubmit(payload)
          } catch (error) {
            onSubmit(error)
          }
        }}
      >
        <div className="form-grid">
          <label className="form-field--wide">
            Full name
            <input name="name" type="text" autoComplete="name" required maxLength={100} />
          </label>
          <label className="form-field--wide">
            Email address
            <input name="email" type="email" autoComplete="email" required maxLength={100} />
          </label>
          <label className="form-field--wide">
            Phone number
            <input name="phone_no" type="tel" autoComplete="tel" required maxLength={20} />
          </label>
          <label className="form-field--wide">
            Password
            <input name="password" type="password" autoComplete="new-password" required />
          </label>
          <label>
            City
            <input name="city" type="text" autoComplete="address-level2" required />
          </label>
          <label>
            State
            <input name="state" type="text" autoComplete="address-level1" required />
          </label>
          <label className="form-field--wide">
            Country code
            <input
              name="country"
              type="text"
              autoComplete="country"
              required
              minLength={2}
              maxLength={2}
              pattern="[A-Za-z]{2}"
              aria-describedby="country-hint"
            />
            <span className="field-hint" id="country-hint">Two-letter country code, such as IN.</span>
          </label>
        </div>
        <label className="checkbox-field">
          <input
            type="checkbox"
            checked={shareLocation}
            onChange={(event) => setShareLocation(event.target.checked)}
          />
          <span>Allow Parkwise to use my current location during registration</span>
        </label>
        <p className="field-hint location-hint">
          If you leave this off, your city, state, and country are used to determine an approximate location.
        </p>
        <button className="primary-button" type="submit" disabled={pending}>
          {pending ? 'Creating account…' : 'Create account'}
        </button>
      </form>
      <p className="switch-prompt">
        Already have an account?{' '}
        <button className="text-button" type="button" onClick={onLogin}>
          Sign in
        </button>
      </p>
    </section>
  )
}

function ServiceStatus({ status, details, lastChecked, onRefresh }) {
  const statusCopy = {
    checking: { label: 'Checking', message: 'Checking service health…' },
    online: { label: 'Healthy', message: 'The API health endpoint is responding.' },
    offline: { label: 'Unavailable', message: 'Unable to reach the API health endpoint.' },
  }
  const currentStatus = statusCopy[status]

  return (
    <section className="service-panel" aria-labelledby="service-title">
      <div className="service-panel__heading">
        <div>
          <p className="eyebrow">Platform</p>
          <h2 id="service-title">Service status</h2>
        </div>
        <button
          className="secondary-button"
          type="button"
          onClick={onRefresh}
          disabled={status === 'checking'}
        >
          {status === 'checking' ? 'Checking…' : 'Check again'}
        </button>
      </div>
      <div className={`status-card status-card--${status}`} aria-live="polite">
        <span className="status-indicator" aria-hidden="true" />
        <div>
          <p className="status-label">{currentStatus.label}</p>
          <p className="status-message">{currentStatus.message}</p>
        </div>
      </div>
      <dl className="details-list">
        <div className="detail-row">
          <dt>Service</dt>
          <dd>{details?.service || 'Parking API'}</dd>
        </div>
        <div className="detail-row">
          <dt>Environment</dt>
          <dd>{details?.environment || import.meta.env.MODE}</dd>
        </div>
        <div className="detail-row">
          <dt>Last checked</dt>
          <dd>{lastChecked ? lastChecked.toLocaleTimeString() : 'Not checked yet'}</dd>
        </div>
      </dl>
      {details?.error && <Alert>{details.error}</Alert>}
    </section>
  )
}

function getRoleLabel(role) {
  const labels = { U: 'Parking user', M: 'Parking merchant', A: 'Administrator' }
  return labels[role] || role || 'Account'
}

function App() {
  const [view, setView] = useState('login')
  const [session, setSession] = useState(null)
  const [restoringSession, setRestoringSession] = useState(true)
  const [pending, setPending] = useState(false)
  const [notice, setNotice] = useState('')
  const [noticeType, setNoticeType] = useState('error')
  const [serviceStatus, setServiceStatus] = useState('checking')
  const [serviceDetails, setServiceDetails] = useState(null)
  const [lastChecked, setLastChecked] = useState(null)

  const checkHealth = useCallback(async (signal) => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        headers: { Accept: 'application/json' },
        signal,
      })
      const data = await readResponse(response)
      if (!signal?.aborted) {
        setServiceStatus('online')
        setServiceDetails(data)
        setLastChecked(new Date())
      }
    } catch (error) {
      if (!signal?.aborted && error.name !== 'AbortError') {
        setServiceStatus('offline')
        setServiceDetails({ error: error.message })
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

  useEffect(() => {
    let cancelled = false

    async function restoreSession() {
      let savedSession
      try {
        const stored = sessionStorage.getItem(SESSION_KEY)
        savedSession = stored ? JSON.parse(stored) : null
      } catch {
        sessionStorage.removeItem(SESSION_KEY)
        if (!cancelled) {
          setNoticeType('error')
          setNotice('The saved session could not be read. Please sign in again.')
          setRestoringSession(false)
        }
        return
      }

      if (
        !savedSession?.accessToken
        || !savedSession?.refreshToken
        || !savedSession?.user?.id
        || !savedSession?.user?.name
      ) {
        if (savedSession) sessionStorage.removeItem(SESSION_KEY)
        if (!cancelled) setRestoringSession(false)
        return
      }

      try {
        await apiRequest('/tokenauth/protected', {
          headers: { Authorization: `Bearer ${savedSession.accessToken}` },
        })
        if (!cancelled) setSession(savedSession)
      } catch (error) {
        if (error.status === 401 || error.status === 403) {
          try {
            const refreshed = await apiRequest('/tokenauth/refresh', {
              method: 'POST',
              headers: { Authorization: `Bearer ${savedSession.refreshToken}` },
            })
            if (!refreshed.access_token) {
              throw new Error('The API did not return a renewed access token.', { cause: error })
            }
            const renewedSession = { ...savedSession, accessToken: refreshed.access_token }
            await apiRequest('/tokenauth/protected', {
              headers: { Authorization: `Bearer ${renewedSession.accessToken}` },
            })
            if (!cancelled) {
              setSession(renewedSession)
              try {
                sessionStorage.setItem(SESSION_KEY, JSON.stringify(renewedSession))
              } catch {
                setNotice('Your session was renewed, but this browser could not save it for this tab.')
              }
            }
          } catch (refreshError) {
            if (!cancelled) {
              if (refreshError.status === 401 || refreshError.status === 403) {
                sessionStorage.removeItem(SESSION_KEY)
                setNotice('Your session has expired. Please sign in again.')
              } else {
                setSession(savedSession)
                setNotice(`Could not renew your session. ${refreshError.message}`)
              }
            }
          }
        } else if (!cancelled) {
          setSession(savedSession)
          setNotice(`Could not verify the saved session. ${error.message}`)
        }
        if (!cancelled) setNoticeType('error')
      } finally {
        if (!cancelled) setRestoringSession(false)
      }
    }

    restoreSession()
    return () => {
      cancelled = true
    }
  }, [])

  async function handleLogin(event) {
    event.preventDefault()
    setPending(true)
    setNoticeType('error')
    setNotice('')

    const formData = new FormData(event.currentTarget)
    const payload = {
      email: formData.get('email').trim(),
      password: formData.get('password'),
    }

    try {
      const result = await apiRequest('/auth/userlogin', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      if (
        !result.access_token
        || !result.refresh_token
        || !result.user?.id
        || !result.user?.name
      ) {
        throw new Error('The API response is missing account or session details.')
      }

      const nextSession = {
        accessToken: result.access_token,
        refreshToken: result.refresh_token,
        user: result.user,
      }
      setSession(nextSession)
      setView('dashboard')

      try {
        sessionStorage.setItem(SESSION_KEY, JSON.stringify(nextSession))
      } catch {
        setNotice('You are signed in, but this browser could not save the session for this tab.')
      }
    } catch (error) {
      setNotice(error.message)
    } finally {
      setPending(false)
    }
  }

  async function handleRegistration(payloadOrError) {
    if (payloadOrError instanceof Error) {
      setNotice(payloadOrError.message)
      return
    }

    setPending(true)
    setNoticeType('error')
    setNotice('')
    try {
      const result = await apiRequest('/auth/registration', {
        method: 'POST',
        body: JSON.stringify(payloadOrError),
      })
      setView('login')
      setNoticeType('success')
      setNotice(result.message || 'Registration successful. Sign in with your new account.')
    } catch (error) {
      setNotice(error.message)
    } finally {
      setPending(false)
    }
  }

  async function handleLogout() {
    if (!session) return
    setPending(true)
    setNoticeType('error')
    setNotice('')

    const logoutRequests = [
      ['/auth/logoutcurrent', session.accessToken],
      ['/auth/logoutrefresh', session.refreshToken],
    ]
    const results = await Promise.allSettled(
      logoutRequests.map(async ([path, token]) => {
        const response = await fetch(`${API_BASE_URL}${path}`, {
          method: 'POST',
          headers: { Accept: 'application/json', Authorization: `Bearer ${token}` },
        })
        if (response.ok || response.status === 401 || response.status === 403) return
        await readResponse(response)
      }),
    )
    const failures = results
      .filter((result) => result.status === 'rejected')
      .map((result) => result.reason.message)

    if (failures.length) {
      setNotice(`Sign out could not be completed: ${failures.join(' ')}`)
    } else {
      setSession(null)
      setView('login')
      try {
        sessionStorage.removeItem(SESSION_KEY)
      } catch {
        setNotice('You are signed out, but this browser could not clear the saved session.')
      }
    }

    setPending(false)
  }

  const beginRegistration = () => {
    setNoticeType('error')
    setNotice('')
    setView('register')
  }
  const beginLogin = () => {
    setNoticeType('error')
    setNotice('')
    setView('login')
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <Brand />
        {session ? (
          <div className="account-actions">
            <span className="environment-tag">{getRoleLabel(session.user.role)}</span>
            <button className="header-button" type="button" onClick={handleLogout} disabled={pending}>
              {pending ? 'Signing out…' : 'Sign out'}
            </button>
          </div>
        ) : (
          <span className="environment-tag">{import.meta.env.MODE}</span>
        )}
      </header>

      {restoringSession ? (
        <main className="loading-state" aria-live="polite">Restoring your session…</main>
      ) : session ? (
        <main className="dashboard">
          <section className="dashboard-heading">
            <div>
              <p className="eyebrow">Your account</p>
              <h1>Welcome, {session.user.name}</h1>
              <p className="subtext">You’re signed in to Parkwise.</p>
            </div>
          </section>
          <Alert kind={noticeType}>{notice}</Alert>
          <div className="dashboard-grid">
            <section className="account-panel" aria-labelledby="account-title">
              <p className="eyebrow">Account details</p>
              <h2 id="account-title">Your profile</h2>
              <dl className="details-list">
                <div className="detail-row">
                  <dt>Name</dt>
                  <dd>{session.user.name}</dd>
                </div>
                <div className="detail-row">
                  <dt>Account ID</dt>
                  <dd>{session.user.id}</dd>
                </div>
                <div className="detail-row">
                  <dt>Account type</dt>
                  <dd>{getRoleLabel(session.user.role)}</dd>
                </div>
              </dl>
            </section>
            <ServiceStatus
              status={serviceStatus}
              details={serviceDetails}
              lastChecked={lastChecked}
              onRefresh={() => {
                setServiceStatus('checking')
                checkHealth()
              }}
            />
          </div>
          <p className="dashboard-note">
            Parking and booking details aren’t available from the current user-facing API.
          </p>
        </main>
      ) : (
        <main className="auth-layout">
          <section className="auth-copy">
            <p className="eyebrow">Parking, made simpler</p>
            <h1>{view === 'register' ? 'Find your place.' : 'Your next stop starts here.'}</h1>
            <p className="subtext">
              Sign in to your account or create one to get started with Parkwise.
            </p>
            <ServiceStatus
              status={serviceStatus}
              details={serviceDetails}
              lastChecked={lastChecked}
              onRefresh={() => {
                setServiceStatus('checking')
                checkHealth()
              }}
            />
          </section>
          {view === 'register' ? (
            <RegistrationForm
              onSubmit={handleRegistration}
              onLogin={beginLogin}
              pending={pending}
              notice={notice}
              noticeType={noticeType}
            />
          ) : (
            <LoginForm
              onSubmit={handleLogin}
              onRegister={beginRegistration}
              pending={pending}
              notice={notice}
              noticeType={noticeType}
            />
          )}
        </main>
      )}

      <footer className="footer">Parkwise · API endpoint {API_BASE_URL}/health</footer>
    </div>
  )
}

export default App
