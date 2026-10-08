import { useState } from 'react'
import useAuth from '../../auth/useAuth.js'
import DemoPageHeader from '../../demo/DemoPageHeader.jsx'
import '../../demo/DemoUI.css'

const MERCHANT_LOCATION_IDS = [1, 2]

function MerchantLocations({ data, updateData }) {
  const [notice, setNotice] = useState('')
  const locations = data.lots.filter((lot) => MERCHANT_LOCATION_IDS.includes(lot.id))

  function toggleListing(location) {
    const willBeListed = location.isListed === false
    updateData((current) => ({
      ...current,
      lots: current.lots.map((lot) => lot.id === location.id ? { ...lot, isListed: willBeListed } : lot),
    }))
    setNotice(`${location.name} is now ${willBeListed ? 'listed' : 'hidden'} in the demo. No live marketplace data changed.`)
  }

  return (
    <>
      <DemoPageHeader eyebrow="Merchant · Sample properties" title="My locations" description="Review the merchant’s fictional parking properties and simulate showing or hiding a location." notice={notice} />
      <div className="demo-stat-grid">
        <article className="demo-stat"><span>Sample locations</span><strong>{locations.length}</strong></article>
        <article className="demo-stat"><span>Listed in demo</span><strong>{locations.filter((item) => item.isListed !== false).length}</strong></article>
        <article className="demo-stat"><span>Total sample spaces</span><strong>{locations.reduce((sum, item) => sum + item.total, 0)}</strong></article>
      </div>
      <div className="demo-card-grid">
        {locations.map((location) => (
          <article className="demo-card" key={location.id}>
            <div className="demo-card__top">
              <div><h2>{location.name}</h2><p className="demo-card__subtle">{location.address}, {location.city}</p></div>
              <span className={`demo-status${location.isListed === false ? ' demo-status--muted' : ''}`}>{location.isListed === false ? 'Hidden' : 'Listed'}</span>
            </div>
            <div className="demo-card__details"><span>{location.available} spaces free</span><span>{location.total} total</span><span>₹{location.rate} / hour</span></div>
            <button className="demo-button" type="button" onClick={() => toggleListing(location)}>{location.isListed === false ? 'List location (demo)' : 'Hide location (demo)'}</button>
          </article>
        ))}
      </div>
      <p className="demo-disclaimer">All properties and inventory are fictional. Listing controls only update temporary in-memory demo state.</p>
    </>
  )
}

function MerchantRates({ data, updateData }) {
  const [notice, setNotice] = useState('')
  const locations = data.lots.filter((lot) => MERCHANT_LOCATION_IDS.includes(lot.id))

  function saveRate(event, locationId) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const rate = Number(form.get('rate'))
    if (!Number.isFinite(rate) || rate < 1) {
      setNotice('Enter a sample hourly rate greater than zero.')
      return
    }
    updateData((current) => ({
      ...current,
      lots: current.lots.map((lot) => lot.id === locationId ? { ...lot, rate } : lot),
    }))
    setNotice('Sample rate updated. No live pricing was changed.')
  }

  return (
    <>
      <DemoPageHeader eyebrow="Merchant · Sample pricing" title="Spaces and rates" description="Change an hourly rate to demonstrate merchant pricing controls." notice={notice} />
      <div className="demo-card-grid">
        {locations.map((location) => (
          <article className="demo-card" key={location.id}>
            <div className="demo-card__top"><div><h2>{location.name}</h2><p className="demo-card__subtle">{location.floor} floors · {location.total} sample spaces</p></div><span className="demo-status">{location.available} free</span></div>
            <p className="demo-card__details">Current sample rate: ₹{location.rate} per hour</p>
            <form className="demo-rate-form" onSubmit={(event) => saveRate(event, location.id)}>
              <label htmlFor={`demo-rate-${location.id}`}>New hourly rate (₹)</label>
              <input className="demo-number-input" id={`demo-rate-${location.id}`} name="rate" type="number" min="1" max="10000" step="1" defaultValue={location.rate} required />
              <button className="demo-button demo-button--primary" type="submit">Save sample rate</button>
            </form>
          </article>
        ))}
      </div>
      <p className="demo-disclaimer">Rates and floor counts are fictional. Saving changes only temporary in-memory demo state; no customer is charged.</p>
    </>
  )
}

export default function DevMerchantDemoPage({ pageId }) {
  const { session, updatePreviewData } = useAuth()
  if (pageId === 'spaces') return <MerchantRates data={session.demoData} updateData={updatePreviewData} />
  return <MerchantLocations data={session.demoData} updateData={updatePreviewData} />
}
