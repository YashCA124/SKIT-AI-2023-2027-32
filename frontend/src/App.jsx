import { useEffect, useState } from 'react'
import './App.css'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || window.location.origin).replace(/\/+$/, '')
const SESSION_KEY = 'parkwise.auth.session.v1'
const THEME_KEY = 'parkwise.theme.v1'

const ROLES = {
  user: { label: 'Driver', title: 'Driver dashboard', name: 'Aarav Sharma', initials: 'AS' },
  merchant: { label: 'Merchant', title: 'Merchant dashboard', name: 'Priya Mehta', initials: 'PM' },
  admin: { label: 'Administrator', title: 'Admin dashboard', name: 'Jordan Lee', initials: 'JL' },
}

const NAVIGATION = {
  user: [
    { id: 'overview', label: 'Overview', icon: '◫' },
    { id: 'parking', label: 'Find parking', icon: '⌖' },
    { id: 'bookings', label: 'My bookings', icon: '▤' },
  ],
  merchant: [
    { id: 'overview', label: 'Overview', icon: '◫' },
    { id: 'locations', label: 'My locations', icon: '⌖' },
    { id: 'spaces', label: 'Spaces & rates', icon: '▦' },
  ],
  admin: [
    { id: 'overview', label: 'Overview', icon: '◫' },
    { id: 'users', label: 'Users', icon: '♙' },
    { id: 'lots', label: 'Parking lots', icon: '▦' },
  ],
}

const DEMO_LOTS = [
  { id: 1, name: 'Central Plaza Parking', address: '14 MI Road, Jaipur', city: 'Jaipur', rate: 40, available: 18, total: 80, distance: '0.4 km', rating: 4.8, status: 'Open', owner: 'Priya Mehta' },
  { id: 2, name: 'Pink City Hub', address: 'Station Road, Jaipur', city: 'Jaipur', rate: 30, available: 7, total: 45, distance: '1.2 km', rating: 4.6, status: 'Open', owner: 'Rohan Kapoor' },
  { id: 3, name: 'Bapu Bazaar Garage', address: 'Bapu Bazaar, Jaipur', city: 'Jaipur', rate: 25, available: 0, total: 32, distance: '1.8 km', rating: 4.4, status: 'Full', owner: 'Priya Mehta' },
  { id: 4, name: 'C-Scheme Secure Park', address: 'Ashok Marg, Jaipur', city: 'Jaipur', rate: 50, available: 26, total: 60, distance: '2.5 km', rating: 4.9, status: 'Open', owner: 'Nisha Verma' },
]

const DEMO_BOOKINGS = [
  { id: 'PK-2048', lot: 'Central Plaza Parking', spot: 'B-14', date: 'Today, 10:30 AM', until: 'Today, 1:30 PM', amount: 120, status: 'Active' },
  { id: 'PK-1982', lot: 'Pink City Hub', spot: 'A-07', date: 'Yesterday, 4:00 PM', until: 'Yesterday, 6:00 PM', amount: 60, status: 'Completed' },
]

const DEMO_USERS = [
  { id: 'U-1048', name: 'Aarav Sharma', email: 'aarav@example.com', role: 'Driver', joined: '12 Aug 2026', status: 'Active' },
  { id: 'M-0214', name: 'Priya Mehta', email: 'priya@example.com', role: 'Merchant', joined: '08 Aug 2026', status: 'Active' },
  { id: 'U-1032', name: 'Isha Patel', email: 'isha@example.com', role: 'Driver', joined: '02 Aug 2026', status: 'Active' },
  { id: 'M-0208', name: 'Rohan Kapoor', email: 'rohan@example.com', role: 'Merchant', joined: '27 Jul 2026', status: 'Pending' },
  { id: 'U-1011', name: 'Kabir Singh', email: 'kabir@example.com', role: 'Driver', joined: '19 Jul 2026', status: 'Active' },
]

function apiErrorMessage(data, status) {
  const detail = data?.detail
  if (Array.isArray(detail)) return detail.map((issue) => issue.msg).filter(Boolean).join(' ')
  if (typeof detail === 'string') return detail
  return data?.message || `The request failed (HTTP ${status}).`
}

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

async function apiRequest(path, options = {}) {
  const headers = { Accept: 'application/json', ...options.headers }
  if (options.body) headers['Content-Type'] = 'application/json'
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  let data
  try {
    data = await response.json()
  } catch {
    data = null
  }
  if (!response.ok) {
    const error = new Error(apiErrorMessage(data, response.status))
    error.status = response.status
    throw error
  }
  if (data === null && response.status !== 204) throw new Error('The API returned an unreadable response.')
  return data
}

function Alert({ children, kind = 'error' }) {
  if (!children) return null
  return <p className={`notice notice--${kind}`} role={kind === 'error' ? 'alert' : 'status'}>{children}</p>
}

function Brand({ compact = false }) {
  return (
    <div className={`brand${compact ? ' brand--compact' : ''}`}>
      <span className="brand-mark" aria-hidden="true">P</span>
      {!compact && <span>Parkwise</span>}
    </div>
  )
}

function ThemeToggle({ theme, onToggle }) {
  const nextTheme = theme === 'dark' ? 'light' : 'dark'
  return (
    <button
      className="theme-toggle"
      type="button"
      onClick={onToggle}
      aria-label={`Switch to ${nextTheme} mode`}
      title={`Switch to ${nextTheme} mode`}
    >
      <span aria-hidden="true">{theme === 'dark' ? '☀' : '☾'}</span>
      <span>{theme === 'dark' ? 'Light mode' : 'Dark mode'}</span>
    </button>
  )
}

function DemoRolePicker({ onPreview }) {
  return (
    <section className="preview-card" aria-labelledby="preview-title">
      <div className="preview-card__heading">
        <div>
          <p className="eyebrow">Presentation mode</p>
          <h2 id="preview-title">Explore the dashboards</h2>
        </div>
        <span className="demo-pill">Demo data</span>
      </div>
      <p className="preview-copy">Open each role's experience instantly. No account or backend needed.</p>
      <div className="role-picker">
        {Object.entries(ROLES).map(([role, details]) => (
          <button className="role-choice" key={role} type="button" onClick={() => onPreview(role)}>
            <span className={`role-choice__icon role-choice__icon--${role}`}>{details.initials}</span>
            <span className="role-choice__text"><strong>{details.label}</strong><small>Preview dashboard</small></span>
            <span className="role-choice__arrow" aria-hidden="true">→</span>
          </button>
        ))}
      </div>
      <p className="demo-disclaimer">Sample names, parking lots, bookings, and metrics are for demonstration only.</p>
    </section>
  )
}

function AuthScreen({ onPreview, onLogin }) {
  const [view, setView] = useState('login')
  const [pending, setPending] = useState(false)
  const [notice, setNotice] = useState('')
  const [noticeKind, setNoticeKind] = useState('error')
  const [shareLocation, setShareLocation] = useState(false)

  async function handleLogin(event) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    setPending(true)
    setNotice('')
    setNoticeKind('error')
    try {
      const result = await apiRequest('/auth/userlogin', {
        method: 'POST',
        body: JSON.stringify({ email: form.get('email').trim(), password: form.get('password') }),
      })
      if (!result.access_token || !result.refresh_token || !result.user?.id || !result.user?.name) {
        throw new Error('The API response is missing account or session details.')
      }
      const session = {
        accessToken: result.access_token,
        refreshToken: result.refresh_token,
        user: result.user,
      }
      let storageNotice = ''
      try {
        sessionStorage.setItem(SESSION_KEY, JSON.stringify(session))
      } catch {
        storageNotice = 'Signed in, but this browser could not save the session for this tab.'
      }
      onLogin(session, storageNotice)
    } catch (error) {
      setNotice(error.message)
    } finally {
      setPending(false)
    }
  }

  async function handleRegistration(event) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const payload = {
      name: form.get('name').trim(),
      email: form.get('email').trim(),
      phone_no: form.get('phone_no').trim(),
      password: form.get('password'),
      city: form.get('city').trim(),
      state: form.get('state').trim(),
      country: form.get('country').trim().toUpperCase(),
      location_permission_granted: shareLocation,
    }
    setPending(true)
    setNotice('')
    setNoticeKind('error')
    try {
      if (shareLocation) Object.assign(payload, await getBrowserLocation())
      const result = await apiRequest('/auth/registration', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      setView('login')
      setNoticeKind('success')
      setNotice(result.message || 'Account created. Sign in to continue.')
    } catch (error) {
      setNotice(error.message)
    } finally {
      setPending(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-intro">
        <p className="eyebrow">A better way to park</p>
        <h1>Arrive easy.<br /><span>Park happy.</span></h1>
        <p className="auth-intro__copy">Find your next parking spot, manage your locations, or keep your platform moving.</p>
        <div className="auth-feature-list">
          <span><i>✓</i> Find parking around you</span>
          <span><i>✓</i> Manage parking locations</span>
          <span><i>✓</i> One platform, every role</span>
        </div>
        <DemoRolePicker onPreview={onPreview} />
      </section>

      <section className="auth-card" aria-labelledby="auth-title">
        <div className="auth-card__top"><Brand /><span className="secure-label">PARKWISE ACCOUNT</span></div>
        <p className="eyebrow">{view === 'login' ? 'Welcome back' : 'Join Parkwise'}</p>
        <h2 id="auth-title">{view === 'login' ? 'Sign in to your account' : 'Create your account'}</h2>
        <p className="form-intro">{view === 'login' ? 'Enter your details to continue.' : 'Your parking journey starts here.'}</p>
        <Alert kind={noticeKind}>{notice}</Alert>
        <form onSubmit={view === 'login' ? handleLogin : handleRegistration}>
          {view === 'register' && (
            <>
              <label>Full name<input name="name" autoComplete="name" required maxLength={100} placeholder="Your name" /></label>
              <label>Phone number<input name="phone_no" type="tel" autoComplete="tel" required maxLength={20} placeholder="+91 98765 43210" /></label>
            </>
          )}
          <label>Email address<input name="email" type="email" autoComplete="email" required maxLength={100} placeholder="you@example.com" /></label>
          <label>Password<input name="password" type="password" autoComplete={view === 'login' ? 'current-password' : 'new-password'} required /></label>
          {view === 'register' && (
            <div className="form-grid">
              <label>City<input name="city" autoComplete="address-level2" required placeholder="Jaipur" /></label>
              <label>State<input name="state" autoComplete="address-level1" required placeholder="Rajasthan" /></label>
              <label className="form-field--wide">Country code<input name="country" autoComplete="country" required minLength={2} maxLength={2} pattern="[A-Za-z]{2}" placeholder="IN" /></label>
              <label className="checkbox-field form-field--wide">
                <input type="checkbox" checked={shareLocation} onChange={(event) => setShareLocation(event.target.checked)} />
                <span>Allow Parkwise to use my current location</span>
              </label>
              <p className="field-hint form-field--wide">Optional. Otherwise, your city and state are used to estimate your location.</p>
            </div>
          )}
          <button className="primary-button" type="submit" disabled={pending}>
            {pending ? 'Please wait…' : view === 'login' ? 'Sign in' : 'Create account'}
          </button>
        </form>
        <p className="switch-prompt">
          {view === 'login' ? 'New to Parkwise?' : 'Already have an account?'}{' '}
          <button className="text-button" type="button" onClick={() => { setNotice(''); setView(view === 'login' ? 'register' : 'login') }}>
            {view === 'login' ? 'Create an account' : 'Sign in'}
          </button>
        </p>
        <div className="auth-divider"><span>PREVIEW WITHOUT SIGN-IN</span></div>
        <button className="demo-link" type="button" onClick={() => onPreview('user')}>Open dashboard demo <span aria-hidden="true">→</span></button>
      </section>
    </main>
  )
}

function MetricCard({ icon, label, value, detail, tone = 'blue' }) {
  return (
    <article className="metric-card">
      <span className={`metric-icon metric-icon--${tone}`} aria-hidden="true">{icon}</span>
      <p className="metric-label">{label}</p>
      <strong className="metric-value">{value}</strong>
      <p className="metric-detail">{detail}</p>
    </article>
  )
}

function SectionHeading({ eyebrow, title, description, action }) {
  return (
    <div className="section-heading">
      <div><p className="eyebrow">{eyebrow}</p><h2>{title}</h2>{description && <p className="section-description">{description}</p>}</div>
      {action}
    </div>
  )
}

function StatusBadge({ children }) {
  const status = children.toLowerCase().replace(/\s+/g, '-')
  return <span className={`status-badge status-badge--${status}`}><i />{children}</span>
}

function ParkingCard({ lot, onBook }) {
  return (
    <article className="parking-card">
      <div className="parking-card__art"><span aria-hidden="true">P</span><small>SECURE PARKING</small><b>⌖</b></div>
      <div className="parking-card__body">
        <div className="parking-card__title"><div><h3>{lot.name}</h3><p>{lot.address}</p></div><span className="rating">★ {lot.rating}</span></div>
        <div className="parking-card__facts"><span>⌖ {lot.distance}</span><span>◷ ₹{lot.rate}/hr</span><span className={lot.available ? 'available-text' : 'full-text'}>{lot.available} spots</span></div>
        <button className="primary-button primary-button--small" disabled={!lot.available} onClick={() => onBook(lot)} type="button">
          {lot.available ? 'Book a spot' : 'Currently full'}
        </button>
      </div>
    </article>
  )
}

function UserDashboard({ page, onNavigate, lots, setLots, bookings, setBookings, notice, setNotice }) {
  const [query, setQuery] = useState('')
  const visibleLots = lots.filter((lot) => `${lot.name} ${lot.address}`.toLowerCase().includes(query.toLowerCase()))
  const bookLot = (lot) => {
    const booking = { id: `DEMO-${Date.now().toString().slice(-4)}`, lot: lot.name, spot: 'C-12', date: 'Today, 2:00 PM', until: 'Today, 4:00 PM', amount: lot.rate * 2, status: 'Active' }
    setBookings((items) => [booking, ...items])
    setLots((items) => items.map((item) => item.id === lot.id ? { ...item, available: Math.max(0, item.available - 1), status: item.available === 1 ? 'Full' : item.status } : item))
    setNotice(`Demo booking confirmed at ${lot.name}.`)
  }
  const cancelBooking = (bookingId) => {
    const booking = bookings.find((item) => item.id === bookingId)
    setBookings((items) => items.map((item) => item.id === bookingId ? { ...item, status: 'Cancelled' } : item))
    if (booking) {
      setLots((items) => items.map((lot) => lot.name === booking.lot
        ? { ...lot, available: Math.min(lot.total, lot.available + 1), status: 'Open' }
        : lot))
    }
    setNotice('Demo booking cancelled.')
  }

  if (page === 'parking') {
    return <><SectionHeading eyebrow="Find your spot" title="Parking near you" description="Explore sample Jaipur locations. All availability shown is demo data." /><div className="search-row"><label className="search-box"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search by location or name" aria-label="Search parking lots" /></label><span className="filter-chip">⌖ Jaipur</span><span className="demo-pill">SAMPLE RESULTS</span></div><div className="parking-grid">{visibleLots.map((lot) => <ParkingCard key={lot.id} lot={lot} onBook={bookLot} />)}</div>{visibleLots.length === 0 && <EmptyState title="No sample locations found" text="Try another search term." />}</>
  }

  if (page === 'bookings') {
    return <><SectionHeading eyebrow="Your activity" title="My bookings" description="Your sample parking activity for the demo." /><div className="table-card"><div className="table-scroll"><table><thead><tr><th>BOOKING</th><th>PARKING LOCATION</th><th>WHEN</th><th>AMOUNT</th><th>STATUS</th><th /></tr></thead><tbody>{bookings.map((booking) => <tr key={booking.id}><td><strong>{booking.id}</strong><small>Spot {booking.spot}</small></td><td>{booking.lot}</td><td>{booking.date}<small>Until {booking.until}</small></td><td>₹{booking.amount}</td><td><StatusBadge>{booking.status}</StatusBadge></td><td>{booking.status === 'Active' && <button className="table-action" onClick={() => cancelBooking(booking.id)} type="button">Cancel</button>}</td></tr>)}</tbody></table></div>{bookings.length === 0 && <EmptyState title="No bookings yet" text="Find a parking spot to create a demo booking." />}</div></>
  }

  return (
    <>
      <SectionHeading eyebrow="Thursday, 8 October" title="Good afternoon, Aarav" description="Here’s what’s happening with your parking." action={<span className="demo-pill">DEMO ACCOUNT</span>} />
      <div className="metric-grid">
        <MetricCard icon="⌖" label="Nearby locations" value="24" detail="Within 5 km of you" tone="blue" />
        <MetricCard icon="▣" label="Available spots" value="186" detail="Across sample locations" tone="green" />
        <MetricCard icon="▤" label="Your bookings" value={bookings.filter((booking) => booking.status === 'Active').length} detail="Active reservations" tone="purple" />
        <MetricCard icon="◷" label="Hours parked" value="12.5" detail="This month" tone="orange" />
      </div>
      <div className="content-columns">
        <section className="panel">
          <SectionHeading eyebrow="Around you" title="Popular parking" action={<button className="inline-link" onClick={() => onNavigate('parking')} type="button">Explore all →</button>} />
          <div className="compact-lot-list">{lots.slice(0, 3).map((lot) => <div className="compact-lot" key={lot.id}><span className="lot-symbol">P</span><div className="compact-lot__main"><strong>{lot.name}</strong><small>{lot.distance} away · {lot.available} spots</small></div><strong className="compact-lot__price">₹{lot.rate}<small>/hr</small></strong></div>)}</div>
        </section>
        <section className="panel">
          <SectionHeading eyebrow="Coming up" title="Next booking" />
          {bookings.find((booking) => booking.status === 'Active') ? <div className="next-booking"><span className="booking-date"><b>08</b><small>OCT</small></span><div><strong>{bookings.find((booking) => booking.status === 'Active').lot}</strong><small>{bookings.find((booking) => booking.status === 'Active').date}</small><small>Spot {bookings.find((booking) => booking.status === 'Active').spot}</small></div><StatusBadge>Active</StatusBadge></div> : <EmptyState title="Nothing booked yet" text="Your next reservation will show here." />}
        </section>
      </div>
      <p className="demo-footnote">All figures and locations on this preview are illustrative sample data, not live parking inventory.</p>
      <Alert kind="success">{notice}</Alert>
    </>
  )
}

function EmptyState({ title, text }) {
  return <div className="empty-state"><span aria-hidden="true">◌</span><strong>{title}</strong><p>{text}</p></div>
}

function MerchantDashboard({ page, lots, setLots, notice, setNotice }) {
  const merchantLots = lots.filter((lot) => lot.owner === 'Priya Mehta')
  const toggleLot = (lotId) => {
    setLots((items) => items.map((lot) => lot.id === lotId ? { ...lot, status: lot.status === 'Open' ? 'Closed' : 'Open' } : lot))
    setNotice('Demo location status updated.')
  }
  const adjustRate = (lotId, rate) => setLots((items) => items.map((lot) => lot.id === lotId ? { ...lot, rate: Math.max(0, Number(rate) || 0) } : lot))
  const addLocation = () => {
    const nextId = Math.max(...lots.map((lot) => lot.id)) + 1
    setLots((items) => [...items, { id: nextId, name: 'New sample location', address: 'Your demo address, Jaipur', city: 'Jaipur', rate: 35, available: 12, total: 24, distance: '—', rating: 5.0, status: 'Open', owner: 'Priya Mehta' }])
    setNotice('Sample location added to this demo.')
  }

  return (
    <>
      <SectionHeading eyebrow="Merchant workspace" title={page === 'overview' ? 'Your locations at a glance' : page === 'locations' ? 'My locations' : 'Spaces & rates'} description="Manage your sample parking inventory. Changes stay in this demo session." action={page === 'locations' && <button className="primary-button primary-button--small" onClick={addLocation} type="button">＋ Add location</button>} />
      {page === 'overview' && <div className="metric-grid">
        <MetricCard icon="⌖" label="Locations" value={merchantLots.length} detail="Across your portfolio" tone="blue" />
        <MetricCard icon="▦" label="Total spaces" value={merchantLots.reduce((sum, lot) => sum + lot.total, 0)} detail="Across all locations" tone="purple" />
        <MetricCard icon="✓" label="Available now" value={merchantLots.reduce((sum, lot) => sum + lot.available, 0)} detail="Sample open spaces" tone="green" />
        <MetricCard icon="₹" label="Today's revenue" value="₹8,450" detail="Illustrative demo metric" tone="orange" />
      </div>}
      {page === 'overview' && <div className="content-columns">
        <section className="panel"><SectionHeading eyebrow="Your portfolio" title="Location performance" /><div className="compact-lot-list">{merchantLots.map((lot) => <div className="compact-lot" key={lot.id}><span className="lot-symbol">P</span><div className="compact-lot__main"><strong>{lot.name}</strong><small>{lot.available} available of {lot.total} spaces</small></div><StatusBadge>{lot.status}</StatusBadge></div>)}</div></section>
        <section className="panel"><SectionHeading eyebrow="This week" title="Activity summary" /><div className="activity-summary"><div><span>Reservations</span><strong>126</strong><small className="positive-change">↑ 12% vs last week</small></div><div><span>Occupancy</span><strong>74%</strong><small>Average across locations</small></div><div><span>Customer rating</span><strong>4.8 <span className="rating-star">★</span></strong><small>From 92 sample reviews</small></div></div></section>
      </div>}
      {(page === 'locations' || page === 'spaces') && <div className="table-card"><div className="table-scroll"><table><thead><tr><th>LOCATION</th><th>SPACES</th><th>AVAILABILITY</th><th>HOURLY RATE</th><th>STATUS</th><th>ACTION</th></tr></thead><tbody>{merchantLots.map((lot) => <tr key={lot.id}><td><strong>{lot.name}</strong><small>{lot.address}</small></td><td>{lot.total}</td><td><div className="availability-cell"><span>{lot.available} available</span><span className="availability-track"><i style={{ width: `${Math.max(4, lot.available / lot.total * 100)}%` }} /></span></div></td><td>{page === 'spaces' ? <label className="rate-input">₹<input type="number" min="0" value={lot.rate} onChange={(event) => adjustRate(lot.id, event.target.value)} aria-label={`Hourly rate for ${lot.name}`} />/hr</label> : `₹${lot.rate}/hr`}</td><td><StatusBadge>{lot.status}</StatusBadge></td><td><button className="table-action" onClick={() => toggleLot(lot.id)} type="button">{lot.status === 'Open' ? 'Close' : 'Open'}</button></td></tr>)}</tbody></table></div>{merchantLots.length === 0 && <EmptyState title="No sample locations" text="Add a location to preview merchant controls." />}</div>}
      <Alert kind="success">{notice}</Alert>
      <p className="demo-footnote">Revenue, ratings, occupancy, and inventory are sample figures for the presentation preview.</p>
    </>
  )
}

function AdminDashboard({ page, onNavigate, lots, setLots, users, setUsers, notice, setNotice }) {
  const [query, setQuery] = useState('')
  const filteredUsers = users.filter((user) => `${user.name} ${user.email} ${user.role}`.toLowerCase().includes(query.toLowerCase()))
  const filteredLots = lots.filter((lot) => `${lot.name} ${lot.address} ${lot.owner}`.toLowerCase().includes(query.toLowerCase()))
  const toggleUser = (userId) => {
    setUsers((items) => items.map((user) => user.id === userId ? { ...user, status: user.status === 'Active' ? 'Suspended' : 'Active' } : user))
    setNotice('Demo user status updated.')
  }
  const toggleLot = (lotId) => {
    setLots((items) => items.map((lot) => lot.id === lotId ? { ...lot, status: lot.status === 'Open' ? 'Closed' : 'Open' } : lot))
    setNotice('Demo parking lot status updated.')
  }

  return (
    <>
      <SectionHeading eyebrow="Platform administration" title={page === 'overview' ? 'Platform overview' : page === 'users' ? 'User directory' : 'Parking locations'} description="Review sample platform activity. Admin actions are local to this demo." action={page !== 'overview' && <label className="search-box search-box--compact"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={`Search ${page}…`} aria-label={`Search ${page}`} /></label>} />
      {page === 'overview' && <>
        <div className="metric-grid">
          <MetricCard icon="♙" label="Total users" value="2,481" detail="Drivers on the platform" tone="blue" />
          <MetricCard icon="⌖" label="Merchants" value="84" detail="Registered operators" tone="purple" />
          <MetricCard icon="▦" label="Parking locations" value={lots.length} detail="Sample directory records" tone="green" />
          <MetricCard icon="▤" label="Bookings today" value="316" detail="Illustrative demo activity" tone="orange" />
        </div>
        <div className="content-columns">
          <section className="panel"><SectionHeading eyebrow="Recently joined" title="New users" action={<button className="inline-link" onClick={() => onNavigate('users')} type="button">View users →</button>} /><div className="compact-lot-list">{users.slice(0, 4).map((user) => <div className="compact-lot" key={user.id}><span className={`avatar avatar--${user.role === 'Merchant' ? 'merchant' : 'user'}`}>{user.name.split(' ').map((part) => part[0]).join('')}</span><div className="compact-lot__main"><strong>{user.name}</strong><small>{user.role} · joined {user.joined}</small></div><StatusBadge>{user.status}</StatusBadge></div>)}</div></section>
          <section className="panel"><SectionHeading eyebrow="Platform health" title="Operations snapshot" /><div className="operation-list"><div><span className="operation-dot operation-dot--green" />API demo environment <strong>Preview mode</strong></div><div><span className="operation-dot operation-dot--blue" />Sample locations <strong>{lots.length}</strong></div><div><span className="operation-dot operation-dot--orange" />Pending reviews <strong>3</strong></div></div></section>
        </div>
      </>}
      {page === 'users' && <div className="table-card"><div className="table-scroll"><table><thead><tr><th>USER</th><th>ROLE</th><th>JOINED</th><th>STATUS</th><th>ACTION</th></tr></thead><tbody>{filteredUsers.map((user) => <tr key={user.id}><td><strong>{user.name}</strong><small>{user.id} · {user.email}</small></td><td><span className="role-tag">{user.role}</span></td><td>{user.joined}</td><td><StatusBadge>{user.status}</StatusBadge></td><td><button className="table-action" onClick={() => toggleUser(user.id)} type="button">{user.status === 'Active' ? 'Suspend' : 'Restore'}</button></td></tr>)}</tbody></table></div>{filteredUsers.length === 0 && <EmptyState title="No users match" text="Try a different search." />}</div>}
      {page === 'lots' && <div className="table-card"><div className="table-scroll"><table><thead><tr><th>PARKING LOCATION</th><th>OPERATOR</th><th>SPACES</th><th>RATE</th><th>STATUS</th><th>ACTION</th></tr></thead><tbody>{filteredLots.map((lot) => <tr key={lot.id}><td><strong>{lot.name}</strong><small>{lot.address}</small></td><td>{lot.owner}</td><td>{lot.available} / {lot.total}</td><td>₹{lot.rate}/hr</td><td><StatusBadge>{lot.status}</StatusBadge></td><td><button className="table-action" onClick={() => toggleLot(lot.id)} type="button">{lot.status === 'Open' ? 'Close' : 'Reopen'}</button></td></tr>)}</tbody></table></div>{filteredLots.length === 0 && <EmptyState title="No parking locations match" text="Try a different search." />}</div>}
      <Alert kind="success">{notice}</Alert>
      <p className="demo-footnote">Platform totals and sample records are illustrative and do not represent live system data.</p>
    </>
  )
}

function DemoDashboard({ role, onRoleChange, onExit, theme, onThemeToggle }) {
  const [page, setPage] = useState('overview')
  const [lots, setLots] = useState(() => DEMO_LOTS.map((lot) => ({ ...lot })))
  const [bookings, setBookings] = useState(() => DEMO_BOOKINGS.map((booking) => ({ ...booking })))
  const [users, setUsers] = useState(() => DEMO_USERS.map((user) => ({ ...user })))
  const [notice, setNotice] = useState('')
  const roleDetails = ROLES[role]
  const activePage = NAVIGATION[role].some((item) => item.id === page) ? page : 'overview'

  return (
    <div className="workspace">
      <aside className="sidebar">
        <div className="sidebar-brand"><Brand /><span className="sidebar-collapse" aria-hidden="true">‹</span></div>
        <div className="workspace-switch"><span className={`workspace-avatar workspace-avatar--${role}`}>{roleDetails.initials}</span><span><strong>{roleDetails.label} workspace</strong><small>Parkwise demo</small></span><span className="switch-chevron">⌄</span></div>
        <p className="nav-label">WORKSPACE</p>
        <nav className="side-nav" aria-label={`${roleDetails.label} dashboard`}>
          {NAVIGATION[role].map((item) => <button className={`nav-item${activePage === item.id ? ' nav-item--active' : ''}`} key={item.id} onClick={() => { setPage(item.id); setNotice('') }} type="button"><span className="nav-item__icon" aria-hidden="true">{item.icon}</span>{item.label}{item.id === 'bookings' && <span className="nav-counter">{bookings.filter((booking) => booking.status === 'Active').length}</span>}</button>)}
        </nav>
        <div className="sidebar-bottom"><div className="demo-side-note"><span>✦</span><strong>Presentation preview</strong><p>Changes are temporary and won't affect real accounts.</p></div><button className="switch-role-button" onClick={onRoleChange} type="button">⇄ Switch dashboard</button></div>
      </aside>
      <div className="workspace-main">
        <header className="workspace-topbar">
          <div className="breadcrumbs"><span>Parkwise</span><b>/</b><strong>{roleDetails.title}</strong></div>
          <div className="topbar-actions"><span className="demo-pill demo-pill--top">DEMO · SAMPLE DATA</span><ThemeToggle theme={theme} onToggle={onThemeToggle} /><span className="topbar-divider" /><div className="profile-menu"><span className={`avatar avatar--${role}`}>{roleDetails.initials}</span><span><strong>{roleDetails.name}</strong><small>{roleDetails.label}</small></span><button className="profile-menu__exit" onClick={onExit} type="button">Exit demo</button></div></div>
        </header>
        <main className="workspace-content">
          <div className="demo-banner"><span>ⓘ</span><p><strong>Interactive demo mode</strong> — sample data only. Any changes you make are temporary and stay in this browser session.</p></div>
          {role === 'user' && <UserDashboard page={activePage} onNavigate={setPage} lots={lots} setLots={setLots} bookings={bookings} setBookings={setBookings} notice={notice} setNotice={setNotice} />}
          {role === 'merchant' && <MerchantDashboard page={activePage} lots={lots} setLots={setLots} notice={notice} setNotice={setNotice} />}
          {role === 'admin' && <AdminDashboard page={activePage} onNavigate={setPage} lots={lots} setLots={setLots} users={users} setUsers={setUsers} notice={notice} setNotice={setNotice} />}
        </main>
        <footer className="workspace-footer">PARKWISE · INTERACTIVE DEMO · NOT CONNECTED TO LIVE INVENTORY</footer>
      </div>
    </div>
  )
}

function ServiceStatus() {
  const [checkVersion, setCheckVersion] = useState(0)
  const [status, setStatus] = useState({ health: 'checking', readiness: 'checking', details: null, lastChecked: null, error: '' })

  useEffect(() => {
    const controller = new AbortController()
    async function checkServices() {
      const [health, readiness] = await Promise.allSettled([
        apiRequest('/health', { signal: controller.signal }),
        apiRequest('/ready', { signal: controller.signal }),
      ])
      if (controller.signal.aborted) return
      const details = health.status === 'fulfilled' ? health.value : null
      setStatus({
        health: health.status === 'fulfilled' ? 'healthy' : 'unavailable',
        readiness: readiness.status === 'fulfilled'
          ? readiness.value.database_configured ? 'configured' : 'not configured'
          : 'unavailable',
        details,
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
        <div><dt>Service</dt><dd>{status.details?.service || 'Parking API'}</dd></div>
        <div><dt>Environment</dt><dd>{status.details?.environment || import.meta.env.MODE}</dd></div>
        <div><dt>Database configuration</dt><dd>{status.readiness}</dd></div>
        <div><dt>Last checked</dt><dd>{status.lastChecked ? status.lastChecked.toLocaleTimeString() : 'Not checked yet'}</dd></div>
      </dl>
      {status.error && <Alert>{status.error}</Alert>}
      {status.readiness === 'unavailable' && <Alert>Readiness information could not be retrieved.</Alert>}
    </section>
  )
}

function RealAccount({ session, onLogout, onDemo, notice, pending }) {
  return (
    <main className="real-account">
      <div className="real-account__head"><span className="demo-pill">LIVE ACCOUNT</span><button className="secondary-button" onClick={onLogout} disabled={pending} type="button">{pending ? 'Signing out…' : 'Sign out'}</button></div>
      <Alert>{notice}</Alert>
      <p className="eyebrow">Your account</p><h1>Welcome, {session.user.name}</h1>
      <p className="section-description">Signed in using the connected Parkwise API.</p>
      <section className="real-account__card"><h2>Account details</h2><dl><div><dt>Name</dt><dd>{session.user.name}</dd></div><div><dt>Account ID</dt><dd>{session.user.id}</dd></div><div><dt>Account type</dt><dd>{session.user.role}</dd></div></dl></section>
      <ServiceStatus />
      <p className="demo-footnote">The live backend currently does not provide all parking dashboard data.</p>
      <button className="demo-link" onClick={onDemo} type="button">Preview the full user dashboard design →</button>
    </main>
  )
}

function App() {
  const [demoRole, setDemoRole] = useState(null)
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem(THEME_KEY) === 'dark' ? 'dark' : 'light'
    } catch {
      return 'light'
    }
  })
  const [realSession, setRealSession] = useState(() => {
    let savedSession
    try {
      savedSession = JSON.parse(sessionStorage.getItem(SESSION_KEY) || 'null')
    } catch {
      try {
        sessionStorage.removeItem(SESSION_KEY)
      } catch {
        // Storage may be disabled by the browser; keep the app usable without restoration.
      }
    }
    return savedSession?.accessToken && savedSession?.refreshToken && savedSession?.user?.id && savedSession?.user?.name
      ? savedSession
      : null
  })
  const [logoutNotice, setLogoutNotice] = useState('')
  const [logoutPending, setLogoutPending] = useState(false)
  const [sessionChecking, setSessionChecking] = useState(Boolean(realSession))
  const [sessionNotice, setSessionNotice] = useState('')

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.documentElement.style.colorScheme = theme
    try {
      localStorage.setItem(THEME_KEY, theme)
    } catch {
      // Theme still applies for this page load when persistent storage is unavailable.
    }
  }, [theme])

  useEffect(() => {
    if (!realSession) return undefined
    let cancelled = false

    async function verifySession() {
      try {
        await apiRequest('/tokenauth/protected', {
          headers: { Authorization: `Bearer ${realSession.accessToken}` },
        })
        return
      } catch (error) {
        if (![401, 403].includes(error.status)) {
          if (!cancelled) setSessionNotice('Could not verify your saved session because the API is unavailable. Your tab session is retained.')
          return
        }
      }

      try {
        const refreshed = await apiRequest('/tokenauth/refresh', {
          method: 'POST',
          headers: { Authorization: `Bearer ${realSession.refreshToken}` },
        })
        if (!refreshed.access_token) throw new Error('The API did not return a refreshed access token.')
        const updatedSession = { ...realSession, accessToken: refreshed.access_token }
        await apiRequest('/tokenauth/protected', {
          headers: { Authorization: `Bearer ${updatedSession.accessToken}` },
        })
        if (cancelled) return
        setRealSession(updatedSession)
        try {
          sessionStorage.setItem(SESSION_KEY, JSON.stringify(updatedSession))
        } catch {
          setSessionNotice('Your session was refreshed, but this browser could not update tab storage.')
        }
      } catch (error) {
        if (cancelled) return
        if ([401, 403].includes(error.status)) {
          try {
            sessionStorage.removeItem(SESSION_KEY)
          } catch {
            setSessionNotice('Your session has expired, but browser storage could not be cleared.')
          }
          setRealSession(null)
        } else {
          setSessionNotice(`Could not refresh your saved session: ${error.message}`)
        }
      }
    }

    verifySession().finally(() => {
      if (!cancelled) setSessionChecking(false)
    })
    return () => { cancelled = true }
  }, [realSession])

  async function logout() {
    setLogoutPending(true)
    setLogoutNotice('')
    if (realSession) {
      const results = await Promise.allSettled([
        apiRequest('/auth/logoutcurrent', { method: 'POST', headers: { Authorization: `Bearer ${realSession.accessToken}` } }),
        apiRequest('/auth/logoutrefresh', { method: 'POST', headers: { Authorization: `Bearer ${realSession.refreshToken}` } }),
      ])
      const failures = results.filter((result) => result.status === 'rejected' && ![401, 403].includes(result.reason?.status))
      if (failures.length) {
        setLogoutNotice(`Sign out could not be completed: ${failures.map((result) => result.reason.message).join(' ')}`)
        setLogoutPending(false)
        return
      }
    }
    sessionStorage.removeItem(SESSION_KEY)
    setRealSession(null)
    setDemoRole(null)
    setLogoutPending(false)
  }

  if (demoRole) return <DemoDashboard key={demoRole} role={demoRole} onRoleChange={() => setDemoRole(null)} onExit={() => setDemoRole(null)} theme={theme} onThemeToggle={() => setTheme((current) => current === 'dark' ? 'light' : 'dark')} />
  if (sessionChecking) return <div className="app-shell"><header className="topbar"><Brand /><ThemeToggle theme={theme} onToggle={() => setTheme((current) => current === 'dark' ? 'light' : 'dark')} /></header><main className="real-account" aria-live="polite">Checking your saved session…</main></div>
  if (realSession) return <div className="app-shell"><header className="topbar"><Brand /><ThemeToggle theme={theme} onToggle={() => setTheme((current) => current === 'dark' ? 'light' : 'dark')} /></header><RealAccount session={realSession} onLogout={logout} onDemo={() => setDemoRole('user')} notice={logoutNotice || sessionNotice} pending={logoutPending} /></div>

  return <div className="app-shell app-shell--auth"><header className="topbar"><Brand /><div className="topbar-tools"><ThemeToggle theme={theme} onToggle={() => setTheme((current) => current === 'dark' ? 'light' : 'dark')} /><span className="environment-tag">PARKING, MADE SIMPLE</span></div></header><AuthScreen onPreview={setDemoRole} onLogin={(session, warning) => { setRealSession(session); setSessionNotice(warning || ''); setDemoRole(null) }} /></div>
}

export default App
