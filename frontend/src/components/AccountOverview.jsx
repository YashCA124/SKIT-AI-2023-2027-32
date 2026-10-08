import { Link } from 'react-router-dom'
import { getRoleDetails, ROLE_PAGES } from '../config/rolePages.js'
import ServiceStatus from './ServiceStatus.jsx'
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

  const knownModules = [
    { title: 'Driver parking and bookings', description: 'The source includes a user dashboard, but the active API does not mount its route.' },
    { title: 'Merchant locations and rates', description: 'Merchant dashboard routes are not mounted by the active API.' },
    { title: 'Administrator users and lots', description: 'Administrator dashboard routes are not mounted by the active API.' },
    { title: 'Payments', description: 'No payment API or payment provider is configured in this project.' },
  ]

  return (
    <>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Account overview</p>
          <h1>Welcome, {session.user.name}</h1>
          <p className="section-description">{import.meta.env.DEV && session.isPreview ? `Viewing the development preview as ${role.label}.` : `Signed in through the connected Parkwise API as ${role.label}.`}</p>
        </div>
        <span className="account-role-badge">{role.label}</span>
      </div>
      <section className="real-account__card">
        <h2>Account details</h2>
        <dl>
          <div><dt>Name</dt><dd>{session.user.name}</dd></div>
          <div><dt>Account ID</dt><dd>{session.user.id}</dd></div>
          <div><dt>Account type</dt><dd>{role.label}</dd></div>
        </dl>
      </section>
      <section className="module-status-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Connected features</p>
            <h2>Feature availability</h2>
            <p className="section-description">These areas are unavailable because the current FastAPI app does not expose their dashboard or payment routes.</p>
          </div>
        </div>
        <div className="module-status-grid">
          {knownModules.map((module) => (
            <article className="module-status-card" key={module.title}>
              <span className="module-status-card__status">Not available</span>
              <h3>{module.title}</h3>
              <p>{module.description}</p>
            </article>
          ))}
        </div>
      </section>
      <ServiceStatus />
    </>
  )
}
