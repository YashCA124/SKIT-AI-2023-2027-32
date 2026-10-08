import Brand from '../components/Brand.jsx'
import ThemeToggle from '../components/ThemeToggle.jsx'
import './AuthLayout.css'

export default function AuthLayout({ children }) {
  return (
    <div className="app-shell app-shell--auth">
      <main className="auth-page">
        <section className="auth-intro">
          <p className="eyebrow">Parkwise parking platform</p>
          <h1>Parking that<br /><span>works for you.</span></h1>
          <p className="auth-intro__copy">Sign in to your account to continue. Access to parking, merchant, and administration features depends on the services enabled for your account.</p>
          <div className="auth-trust-note">
            <span aria-hidden="true">↗</span>
            <p><strong>Connected account access</strong><br />Sign-in and registration use the Parkwise API. Dashboard features appear when provided by the connected services.</p>
          </div>
        </section>
        <section className="auth-card">
          <div className="auth-card__top">
            <Brand />
            <div className="auth-card__tools"><span className="secure-label">ACCOUNT ACCESS</span><ThemeToggle /></div>
          </div>
          {children}
        </section>
      </main>
    </div>
  )
}
