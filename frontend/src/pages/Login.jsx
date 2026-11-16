import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { loginAdmin, loginUser } from '../api/auth.js'
import useAuth from '../auth/useAuth.js'
import Alert from '../components/Alert.jsx'
import AuthLayout from './AuthLayout.jsx'

export default function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const [accountType, setAccountType] = useState(
    ['user', 'merchant', 'admin'].includes(location.state?.accountType)
      ? location.state.accountType
      : 'user',
  )
  const [pending, setPending] = useState(false)
  const [notice, setNotice] = useState('')
  const { authNotice, clearAuthNotice, login } = useAuth()
  const successNotice = location.state?.successNotice || ''

  async function handleSubmit(event) {
    event.preventDefault()
    clearAuthNotice()
    setPending(true)
    setNotice('')

    const form = new FormData(event.currentTarget)
    const isAdmin = accountType === 'admin'
    const expectedRole = { user: 'U', merchant: 'M', admin: 'A' }[accountType]
    const credentials = isAdmin
      ? { username: form.get('username').trim(), password: form.get('password') }
      : { email: form.get('email').trim(), password: form.get('password') }

    try {
      const result = await (isAdmin ? loginAdmin(credentials) : loginUser(credentials))
      if (!result.access_token || !result.refresh_token || !result.user?.id || !result.user?.name) {
        throw new Error('The API response is missing account or session details.')
      }
      if (result.user.role !== expectedRole) {
        throw new Error(accountType === 'merchant'
          ? 'This account does not have merchant access yet. Contact an administrator to enable it.'
          : 'These credentials belong to a different account type. Choose the matching sign-in option.')
      }
      login({
        accessToken: result.access_token,
        refreshToken: result.refresh_token,
        user: result.user,
      })
      navigate(location.state?.from?.pathname || '/account', { replace: true })
    } catch (error) {
      setNotice(error.message)
    } finally {
      setPending(false)
    }
  }

  const adminLogin = accountType === 'admin'
  const visibleNotice = notice || authNotice || successNotice

  return (
    <AuthLayout>
      <div className="account-type-control" role="group" aria-label="Sign-in account type">
        {[
          ['user', 'User'],
          ['merchant', 'Merchant'],
          ['admin', 'Admin'],
        ].map(([type, label]) => (
          <button
            key={type}
            className={accountType === type ? 'account-type-control__active' : ''}
            type="button"
            aria-pressed={accountType === type}
            onClick={() => { clearAuthNotice(); setAccountType(type); setNotice('') }}
          >
            {label}
          </button>
        ))}
      </div>
      <p className="eyebrow">{adminLogin ? 'Administrator access' : accountType === 'merchant' ? 'Merchant access' : 'Driver access'}</p>
      <h2 id="auth-title">Sign in as {adminLogin ? 'administrator' : accountType}</h2>
      <p className="form-intro">Your credentials are sent to the connected Parkwise API.</p>
      <Alert kind={successNotice && !notice && !authNotice ? 'success' : 'error'}>{visibleNotice}</Alert>
      <form onSubmit={handleSubmit}>
        {adminLogin
          ? <label>Username<input name="username" autoComplete="username" required maxLength={100} placeholder="Administrator username" /></label>
          : <label>Email address<input name="email" type="email" autoComplete="email" required maxLength={100} placeholder="you@example.com" /></label>}
        <label>Password<input name="password" type="password" autoComplete="current-password" required /></label>
        <button className="primary-button" type="submit" disabled={pending}>{pending ? 'Please wait…' : 'Sign in'}</button>
      </form>
      {!adminLogin && (
        <p className="switch-prompt">New to Parkwise? <Link className="text-button" to="/register" state={{ accountType }}>Create a {accountType} account</Link></p>
      )}
      {import.meta.env.DEV && (
        <p className="switch-prompt">
          Testing the frontend? <Link className="text-button" to="/__preview">Preview pages without backend</Link>
        </p>
      )}
    </AuthLayout>
  )
}
