import { Navigate, Outlet, useLocation } from 'react-router-dom'
import useAuth from './useAuth.js'
import './ProtectedRoute.css'

export default function ProtectedRoute({ requiredRole }) {
  const { session, isChecking } = useAuth()
  const location = useLocation()

  if (isChecking) {
    return <main className="real-account" aria-live="polite">Checking your saved session…</main>
  }
  if (!session) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  if (requiredRole && session.user.role !== requiredRole && !(import.meta.env.DEV && session.isPreview)) {
    return <Navigate to="/account" replace />
  }
  return <Outlet />
}
