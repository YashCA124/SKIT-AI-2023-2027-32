import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { loginAdmin, loginUser } from '../api/auth.js'
import useAuth from '../auth/useAuth.js'
import Alert from '../components/Alert.jsx'
import AuthLayout from './AuthLayout.jsx'
import './Login.css'

export default function Login() {
  const [accountType, setAccountType] = useState('user')
  const [pending, setPending] = useState(false)
  const [notice, setNotice] = useState('')
  const navigate = useNavigate()
  const location = useLocation()
  const { authNotice, clearAuthNotice, login } = useAuth()
  const successNotice = location.state?.successNotice || ''

  async function handleSubmit(event) {
    event.preventDefault()
    clearAuthNotice()
    setPending(true)
    setNotice('')

    const form = new FormData(event.currentTarget)
    const isAdmin = accountType === 'admin'
    const credentials = isAdmin
      ? { username: form.get('username').trim(), password: form.get('password') }
      : { email: form.get('email').trim(), password: form.get('password') }

    try {
      const result = await (isAdmin ? loginAdmin(credentials) : loginUser(credentials))
      if (!result.access_token || !result.refresh_token || !result.user?.id || !result.user?.name) {
        throw new Error('The API response is missing account or session details.')
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
      {!adminLogin && (
        <div className="account-type-control" aria-label="Account type">
          <button className={accountType === 'user' ? 'account-type-control__active' : ''} type="button" onClick={() => { clearAuthNotice(); setAccountType('user'); setNotice('') }}>User / Merchant</button>
          <button className={accountType === 'admin' ? 'account-type-control__active' : ''} type="button" onClick={() => { clearAuthNotice(); setAccountType('admin'); setNotice('') }}>Administrator</button>
        </div>
      )}
      {adminLogin && (
        <div className="account-type-control" aria-label="Account type">
          <button type="button" onClick={() => { clearAuthNotice(); setAccountType('user'); setNotice('') }}>User / Merchant</button>
          <button className="account-type-control__active" type="button" onClick={() => { clearAuthNotice(); setAccountType('admin'); setNotice('') }}>Administrator</button>
        </div>
      )}
      <p className="eyebrow">{adminLogin ? 'Administrator access' : 'Welcome back'}</p>
      <h2 id="auth-title">{adminLogin ? 'Sign in as administrator' : 'Sign in to your account'}</h2>
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
        <p className="switch-prompt">New to Parkwise? <Link className="text-button" to="/register">Create an account</Link></p>
      )}
      {import.meta.env.DEV && (
        <p className="switch-prompt">
          Testing the frontend? <Link className="text-button" to="/__preview">Preview pages without backend</Link>
        </p>
      )}
    </AuthLayout>
  )
}
