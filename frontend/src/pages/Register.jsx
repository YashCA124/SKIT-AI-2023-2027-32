import { useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { registerUser } from '../api/auth.js'
import useAuth from '../auth/useAuth.js'
import Alert from '../components/Alert.jsx'
import AuthLayout from './AuthLayout.jsx'
import './Register.css'

function getBrowserLocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Location access is not supported by this browser.'))
      return
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => resolve({ latitude: coords.latitude, longitude: coords.longitude }),
      (error) => reject(new Error(error.code === error.PERMISSION_DENIED
        ? 'Location permission was denied. Allow location access or turn off the location option.'
        : error.code === error.TIMEOUT
          ? 'Location lookup timed out. Please try again.'
          : 'Your location is unavailable. Please try again or turn off the location option.')),
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 },
    )
  })
}

export default function Register() {
  const [pending, setPending] = useState(false)
  const [notice, setNotice] = useState('')
  const [shareLocation, setShareLocation] = useState(false)
  const [location, setLocation] = useState(null)
  const [locationPending, setLocationPending] = useState(false)
  const locationRequestId = useRef(0)
  const navigate = useNavigate()
  const { authNotice, clearAuthNotice } = useAuth()

  async function handleLocationChange(event) {
    const shouldShare = event.target.checked
    const requestId = ++locationRequestId.current
    setShareLocation(shouldShare)
    setNotice('')
    setLocation(null)
    if (!shouldShare) {
      setLocationPending(false)
      return
    }

    clearAuthNotice()
    setLocationPending(true)
    try {
      const coordinates = await getBrowserLocation()
      if (requestId === locationRequestId.current) setLocation(coordinates)
    } catch (error) {
      if (requestId === locationRequestId.current) {
        setShareLocation(false)
        setNotice(error.message)
      }
    } finally {
      if (requestId === locationRequestId.current) setLocationPending(false)
    }
  }

  async function handleSubmit(event) {
    event.preventDefault()
    clearAuthNotice()
    setPending(true)
    setNotice('')
    const form = new FormData(event.currentTarget)

    try {
      const payload = {
        name: form.get('name').trim(),
        email: form.get('email').trim(),
        phone_no: form.get('phone_no').trim(),
        password: form.get('password'),
        address: form.get('address').trim(),
        pincode: form.get('pincode').trim(),
        city: form.get('city').trim(),
        state: form.get('state').trim(),
        country: form.get('country').trim().toUpperCase(),
        location_permission_granted: shareLocation && Boolean(location),
      }
      if (shareLocation && location) Object.assign(payload, location)
      const result = await registerUser(payload)
      navigate('/login', { replace: true, state: { successNotice: result.message || 'Account created. Sign in to continue.' } })
    } catch (error) {
      setNotice(error.message)
    } finally {
      setPending(false)
    }
  }

  return (
    <AuthLayout>
      <p className="eyebrow">Create an account</p>
      <h2 id="auth-title">Register with Parkwise</h2>
      <p className="form-intro">Enter your details to register through the connected API.</p>
      <Alert kind={notice ? 'error' : location ? 'success' : 'error'}>{notice || authNotice || (location ? 'Location permission granted. Your coordinates will be included with registration.' : '')}</Alert>
      <form onSubmit={handleSubmit}>
        <label>Full name<input name="name" autoComplete="name" required maxLength={100} placeholder="Your name" /></label>
        <label>Phone number<input name="phone_no" type="tel" autoComplete="tel" required maxLength={20} placeholder="+91 98765 43210" /></label>
        <label>Email address<input name="email" type="email" autoComplete="email" required maxLength={100} placeholder="you@example.com" /></label>
        <label>Password<input name="password" type="password" autoComplete="new-password" required /></label>
        <div className="form-grid">
          <label>City<input name="city" autoComplete="address-level2" required placeholder="Jaipur" /></label>
          <label>State<input name="state" autoComplete="address-level1" required placeholder="Rajasthan" /></label>
          <label className="form-field--wide">Country code<input name="country" autoComplete="country" required minLength={2} maxLength={2} pattern="[A-Za-z]{2}" placeholder="IN" /></label>
          <label className="form-field--wide">Street address <span>(optional)</span><input name="address" autoComplete="street-address" maxLength={200} placeholder="House number and street" /></label>
          <label className="form-field--wide">Postal code <span>(optional)</span><input name="pincode" autoComplete="postal-code" maxLength={10} placeholder="Postal code" /></label>
          <label className="checkbox-field form-field--wide">
            <input type="checkbox" checked={shareLocation} onChange={handleLocationChange} />
            <span>Allow Parkwise to use my current location</span>
          </label>
          {locationPending && <p className="field-hint form-field--wide" role="status">Requesting permission to use your current location…</p>}
          <p className="field-hint form-field--wide">Optional. If not shared, your city and address details are submitted instead.</p>
        </div>
        <button className="primary-button" type="submit" disabled={pending || locationPending}>{pending ? 'Please wait…' : 'Create account'}</button>
      </form>
      <p className="switch-prompt">Already have an account? <Link className="text-button" to="/login">Sign in</Link></p>
    </AuthLayout>
  )
}
