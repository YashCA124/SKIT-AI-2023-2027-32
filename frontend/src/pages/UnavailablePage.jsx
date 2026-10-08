import './UnavailablePage.css'

export default function UnavailablePage({ page }) {
  return (
    <section className="unavailable-page">
      <span className="unavailable-page__icon" aria-hidden="true">—</span>
      <p className="eyebrow">API endpoint unavailable</p>
      <h1>{page.title}</h1>
      <p>{page.description}</p>
      <div className="unavailable-page__detail">
        <strong>This is not a sign-in problem.</strong>
        <span>The current FastAPI application does not mount an endpoint for this page. No sample records or simulated actions are shown here.</span>
      </div>
    </section>
  )
}
