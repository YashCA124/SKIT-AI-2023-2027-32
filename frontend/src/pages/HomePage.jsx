import { Link } from 'react-router-dom'
import Brand from '../components/Brand.jsx'
import ThemeToggle from '../components/ThemeToggle.jsx'
import useAuth from '../auth/useAuth.js'
import './HomePage.css'

function ParkingIllustration() {
  return (
    <div className="home-illustration" aria-label="Illustration of a parking destination and route" role="img">
      <div className="home-illustration__glow" />
      <div className="home-route home-route--one" />
      <div className="home-route home-route--two" />
      <div className="home-pin home-pin--start"><span /></div>
      <div className="home-pin home-pin--end"><span>P</span></div>
      <div className="home-lot-card">
        <div className="home-lot-card__icon" aria-hidden="true">
          <svg viewBox="0 0 32 32" focusable="false"><path d="M8 27V5h9a7 7 0 0 1 0 14h-9m0-7h8a2 2 0 1 0 0-4h-8" /></svg>
        </div>
        <div>
          <strong>Your next stop</strong>
          <span>Parking, made simpler</span>
        </div>
        <span className="home-lot-card__arrow" aria-hidden="true">↗</span>
      </div>
      <span className="home-illustration__spark home-illustration__spark--one" aria-hidden="true">✳</span>
      <span className="home-illustration__spark home-illustration__spark--two" aria-hidden="true">✦</span>
    </div>
  )
}

export default function HomePage() {
  const { session } = useAuth()
  const accountPath = session ? '/account' : '/login'
  const accountLabel = session ? 'Go to account' : 'Sign in'

  return (
    <main className="home-page">
      <header className="home-header">
        <Brand />
        <nav className="home-nav" aria-label="Main navigation">
          <a href="#how-it-works">How it works</a>
          <a href="#built-for">Who it’s for</a>
        </nav>
        <div className="home-header__actions">
          <ThemeToggle />
          <Link className="home-sign-in" to={accountPath}>{accountLabel}</Link>
        </div>
      </header>

      <section className="home-hero">
        <div className="home-hero__copy">
          <p className="home-eyebrow"><span /> A smarter way to think about parking</p>
          <h1>Make room for<br /><span>better journeys.</span></h1>
          <p className="home-hero__description">
            Parkwise brings drivers and parking providers together, making the
            search for a place to park feel a little more straightforward.
          </p>
          <div className="home-hero__actions">
            <Link className="home-button home-button--primary" to={session ? '/account' : '/register'}>
              {session ? 'Open your account' : 'Get started'} <span aria-hidden="true">→</span>
            </Link>
            <a className="home-button home-button--secondary" href="#how-it-works">Discover Parkwise</a>
          </div>
          <p className="home-hero__note">One account for drivers, parking providers, and administrators.</p>
        </div>
        <ParkingIllustration />
      </section>

      <div className="home-status" role="note">
        <span className="home-status__dot" aria-hidden="true" />
        <p><strong>Early access:</strong> Account registration and sign-in are available. Live parking search and booking are not connected yet.</p>
        <Link to={accountPath}>Explore account access <span aria-hidden="true">→</span></Link>
      </div>

      <section className="home-how" id="how-it-works">
        <div className="home-section-heading">
          <p className="home-eyebrow">A simpler parking experience</p>
          <h2>Less circling. More getting there.</h2>
          <p>Parkwise is being built around the parts of parking that should feel easy.</p>
        </div>
        <div className="home-feature-grid">
          <article className="home-feature-card">
            <span className="home-feature-card__number">01</span>
            <div className="home-feature-card__icon" aria-hidden="true">⌖</div>
            <h3>Find a place</h3>
            <p>Explore a clearer way to discover parking around the places you need to be.</p>
          </article>
          <article className="home-feature-card">
            <span className="home-feature-card__number">02</span>
            <div className="home-feature-card__icon" aria-hidden="true">▤</div>
            <h3>Stay organized</h3>
            <p>Keep parking plans and account details together in one straightforward experience.</p>
          </article>
          <article className="home-feature-card">
            <span className="home-feature-card__number">03</span>
            <div className="home-feature-card__icon" aria-hidden="true">⌂</div>
            <h3>Support providers</h3>
            <p>Give parking providers a place to manage their locations as the platform grows.</p>
          </article>
        </div>
      </section>

      <section className="home-audience" id="built-for">
        <div>
          <p className="home-eyebrow">Designed for the whole parking journey</p>
          <h2>One platform.<br />Different perspectives.</h2>
          <p>Whether you’re looking for a spot or managing a parking location, Parkwise is designed to bring the experience into one place.</p>
        </div>
        <div className="home-audience__roles">
          <article><span aria-hidden="true">↗</span><div><h3>For drivers</h3><p>A more organized way to approach parking.</p></div></article>
          <article><span aria-hidden="true">⌂</span><div><h3>For providers</h3><p>A focused workspace for parking locations.</p></div></article>
          <article><span aria-hidden="true">◎</span><div><h3>For administrators</h3><p>Tools to support a well-managed platform.</p></div></article>
        </div>
      </section>

      <section className="home-cta">
        <div>
          <p className="home-eyebrow">Your next journey starts here</p>
          <h2>Come find your place with Parkwise.</h2>
        </div>
        <Link className="home-button home-button--light" to={session ? '/account' : '/register'}>
          {session ? 'Go to your account' : 'Create your account'} <span aria-hidden="true">→</span>
        </Link>
      </section>

      <footer className="home-footer">
        <Brand />
        <p>Parking, with a little more peace of mind.</p>
        <span>© {new Date().getFullYear()} Parkwise</span>
      </footer>
    </main>
  )
}
