import { useEffect, useState } from 'react'
import {
  logoutCurrent,
  logoutRefresh,
  refreshSession,
  verifySession,
} from '../api/auth.js'
import AuthContext from './authContext.js'

const SESSION_KEY = 'parkwise.auth.session.v1'

function readSavedSession() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(SESSION_KEY) || 'null')
    return saved?.accessToken && saved?.refreshToken && saved?.user?.id && saved?.user?.name
      ? saved
      : null
  } catch {
    try {
      sessionStorage.removeItem(SESSION_KEY)
    } catch {
      // Invalid or inaccessible storage will be handled by sign-in.
    }
    return null
  }
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(readSavedSession)
  const [isChecking, setIsChecking] = useState(Boolean(session))
  const [sessionNotice, setSessionNotice] = useState('')
  const [authNotice, setAuthNotice] = useState('')
  const [logoutNotice, setLogoutNotice] = useState('')
  const [logoutPending, setLogoutPending] = useState(false)

  useEffect(() => {
    if (!session) return undefined
    let cancelled = false

    async function restoreSession() {
      try {
        await verifySession(session.accessToken)
      } catch (error) {
        if (![401, 403].includes(error.status)) {
          if (!cancelled) {
            setSessionNotice('Could not verify the saved session because the API is unavailable. The tab session is retained.')
          }
          return
        }

        try {
          const refreshed = await refreshSession(session.refreshToken)
          if (!refreshed.access_token) {
            if (!cancelled) {
              setSessionNotice('Could not refresh the saved session: the API did not return a refreshed access token.')
            }
            return
          }

          const updated = { ...session, accessToken: refreshed.access_token }
          await verifySession(updated.accessToken)
          if (cancelled) return
          if (updated.accessToken !== session.accessToken) setSession(updated)
          try {
            sessionStorage.setItem(SESSION_KEY, JSON.stringify(updated))
          } catch {
            setSessionNotice('The session was refreshed, but this browser could not save the updated session for this tab.')
          }
        } catch (refreshError) {
          if (cancelled) return
          if ([401, 403].includes(refreshError.status)) {
            try {
              sessionStorage.removeItem(SESSION_KEY)
            } catch {
              setAuthNotice('The saved session could not be cleared from this browser. Sign in again after closing this tab.')
            }
            setSession(null)
          } else {
            setSessionNotice(`Could not refresh the saved session: ${refreshError.message}`)
          }
        }
      } finally {
        if (!cancelled) setIsChecking(false)
      }
    }

    restoreSession()
    return () => {
      cancelled = true
    }
  }, [session])

  function login(nextSession, storageNotice = '') {
    setAuthNotice('')
    setSessionNotice(storageNotice)
    setIsChecking(true)
    setSession(nextSession)
    try {
      sessionStorage.setItem(SESSION_KEY, JSON.stringify(nextSession))
    } catch {
      setSessionNotice('Signed in, but this browser could not save the session for this tab.')
    }
  }

  async function logout() {
    if (!session) return
    setLogoutPending(true)
    setLogoutNotice('')
    const results = await Promise.allSettled([
      logoutCurrent(session.accessToken),
      logoutRefresh(session.refreshToken),
    ])
    const failures = results.filter((result) => (
      result.status === 'rejected' && ![401, 403].includes(result.reason?.status)
    ))
    if (failures.length) {
      const messages = failures.map((result) => result.reason?.message || 'An unknown sign-out error occurred.')
      setLogoutNotice(`Sign out could not be completed: ${messages.join(' ')}`)
      setLogoutPending(false)
      return
    }

    try {
      sessionStorage.removeItem(SESSION_KEY)
    } catch {
      setAuthNotice('You are signed out on the server, but this browser could not clear the saved tab session.')
    }
    setSession(null)
    setLogoutPending(false)
  }

  const value = {
    session,
    isChecking,
    sessionNotice,
    authNotice,
    logoutNotice,
    logoutPending,
    login,
    logout,
    clearAuthNotice: () => setAuthNotice(''),
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
