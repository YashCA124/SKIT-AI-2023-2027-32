import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getRoleDetails, ROLE_PAGES } from '../config/rolePages.js'
import ServiceStatus from './ServiceStatus.jsx'
import Alert from './Alert.jsx'
import { getAccount } from '../api/parking.js'
import './AccountOverview.css'

export default function AccountOverview({ session }) {
  const role = getRoleDetails(session.user.role)
  if (import.meta.env.DEV && session.isPreview) {
    const pages = ROLE_PAGES[session.user.role] || []
    const demoData = session.demoData
    const sampleCounts = [
      { label: 'Fictional parking locations', value: demoData.lots.length },
      { label: 'Sample bookings', value: demoData.bookings.length },
      { label: 'Sample accounts', value: demoData.users.length },
    ]

    return (
      <>
        <div className="section-heading">
          <div>
            <p className="eyebrow">Interactive presentation demo</p>
            <h1>Welcome, {session.user.name}</h1>
            <p className="section-description">Explore the {role.label.toLowerCase()} screens using fictional data. Use the account menu to open each page.</p>
          </div>
          <span className="account-role-badge">{role.label} demo</span>
        </div>
        <section className="preview-summary" aria-label="Fictional demo summary">
          {sampleCounts.map((item) => <article className="preview-summary__item" key={item.label}><span>{item.label}</span><strong>{item.value}</strong></article>)}
        </section>
        <section className="preview-pages">
          <h2>Explore the demo</h2>
          <div>{pages.map((page) => <Link key={page.id} to={page.path}>{page.label}<span aria-hidden="true">→</span></Link>)}</div>
          <p>Sample data and actions are temporary and stay in this browser tab. No backend, reservation, or payment request is made.</p>
        </section>
      </>
    )
  }

  return <LiveAccountOverview session={session} role={role} />
}

function LiveAccountOverview({ session, role }) {
  const [account, setAccount] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    getAccount(session.accessToken)
      .then((result) => { if (active) setAccount(result) })
      .catch((requestError) => { if (active) setError(requestError.message) })
    return () => { active = false }
  }, [session.accessToken])

  return (
    <>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Account overview</p>
          <h1>Welcome, {session.user.name}</h1>
          <p className="section-description">Signed in through the connected Parkwise API as {role.label}.</p>
        </div>
        <span className="account-role-badge">{role.label}</span>
      </div>
      {error && <Alert>{`Could not load your profile: ${error}`}</Alert>}
      <section className="real-account__card">
        <h2>Account details</h2>
        <dl>
          <div><dt>Name</dt><dd>{account?.name || session.user.name}</dd></div>
          <div><dt>Account ID</dt><dd>{account?.id || session.user.id}</dd></div>
          <div><dt>Account type</dt><dd>{role.label}</dd></div>
          {account?.email && <div><dt>Email</dt><dd>{account.email}</dd></div>}
          {account?.phone_no && <div><dt>Phone</dt><dd>{account.phone_no}</dd></div>}
          {(account?.city || account?.country) && <div><dt>Location</dt><dd>{[account.city, account.state, account.country].filter(Boolean).join(', ')}</dd></div>}
        </dl>
      </section>
      <section className="module-status-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Connected features</p>
            <h2>What you can do</h2>
            <p className="section-description">Parking locations, reservations, and management records are served by the API and saved in the database.</p>
          </div>
        </div>
        <div className="module-status-grid">
          {ROLE_PAGES[session.user.role]?.filter((page) => page.id !== 'payments').map((page) => (
            <article className="module-status-card" key={page.id}>
              <span className="module-status-card__status">Connected</span>
              <h3>{page.label}</h3>
              <p>{page.description}</p>
            </article>
          ))}
          {session.user.role === 'U' && <article className="module-status-card">
            <span className="module-status-card__status">Not connected</span>
            <h3>Payments</h3>
            <p>No payment service is configured; sessions are recorded without charges.</p>
          </article>}
        </div>
      </section>
      <ServiceStatus />
    </>
  )
}
