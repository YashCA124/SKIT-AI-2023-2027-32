import { useEffect, useState } from 'react'
import useAuth from '../../auth/useAuth.js'
import Alert from '../../components/Alert.jsx'
import { createMerchantLot, getMerchantLots, updateMerchantLot } from '../../api/parking.js'
import { formatRate } from '../../utils/formatRate.js'
import '../LiveDashboard.css'

function heading(title, description) {
  return <header className="live-page__heading"><div><p className="live-page__eyebrow">Merchant workspace · live data</p><h1>{title}</h1><p>{description}</p></div></header>
}

function LotSummary({ lot }) {
  return (
    <div>
      <div className="live-card__top"><div><h2>{lot.location_name}</h2><p className="live-card__address">{lot.address}, {lot.city}, {lot.state}</p></div><span className={lot.available === 'ACTIVE' ? 'live-chip' : 'live-chip live-chip--warning'}>{lot.available}</span></div>
      <div className="live-card__facts"><span>{formatRate(lot.price, lot.currency)} / hour</span><span>{lot.available_spots} of {lot.total_spots} spaces available</span><span>{lot.floor_count} floors</span></div>
    </div>
  )
}

function CreateLotForm({ accessToken, onCreated }) {
  const [pending, setPending] = useState(false)
  const [locationPending, setLocationPending] = useState(false)
  const [location, setLocation] = useState({ latitude: '', longitude: '' })
  const [error, setError] = useState('')

  function useCurrentLocation() {
    if (!navigator.geolocation) {
      setError('Location access is not supported by this browser. Enter coordinates manually.')
      return
    }
    setLocationPending(true)
    setError('')
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setLocation({ latitude: coords.latitude, longitude: coords.longitude })
        setLocationPending(false)
      },
      (failure) => {
        setError(failure.code === failure.PERMISSION_DENIED
          ? 'Location permission was denied. Enter coordinates manually or allow access.'
          : 'Could not determine your location. Enter coordinates manually or try again.')
        setLocationPending(false)
      },
      { timeout: 10000, maximumAge: 60000 },
    )
  }

  async function submit(event) {
    event.preventDefault()
    const formElement = event.currentTarget
    setPending(true)
    setError('')
    const form = new FormData(formElement)
    const payload = {
      location_name: form.get('location_name').trim(),
      price: Number(form.get('price')),
      currency: form.get('currency').trim().toUpperCase(),
      country: form.get('country').trim().toUpperCase(),
      city: form.get('city').trim(),
      state: form.get('state').trim(),
      address: form.get('address').trim(),
      pincode: form.get('pincode').trim(),
      latitude: Number(location.latitude || form.get('latitude')),
      longitude: Number(location.longitude || form.get('longitude')),
      floors: [{ floor_id: Number(form.get('floor_id')), total_spots: Number(form.get('total_spots')) }],
    }
    try {
      await createMerchantLot(accessToken, payload)
      formElement.reset()
      setLocation({ latitude: '', longitude: '' })
      onCreated()
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setPending(false)
    }
  }

  return (
    <section className="live-card">
      <h2>Add a parking location</h2>
      <p>Enter real location details and capacity. The system creates exactly the floors and spaces you specify.</p>
      <Alert>{error}</Alert>
      <form className="live-form" onSubmit={submit}>
        <div className="live-form__grid">
          <label className="live-form__wide">Location name<input name="location_name" required minLength={2} maxLength={120} /></label>
          <label>Hourly rate<input name="price" type="number" min="0" step="0.01" required /></label>
          <label>Currency code<input name="currency" placeholder="INR" minLength={3} maxLength={3} pattern="[A-Za-z]{3}" required /></label>
          <label>Country code<input name="country" placeholder="IN" minLength={2} maxLength={2} pattern="[A-Za-z]{2}" required /></label>
          <label>City<input name="city" required maxLength={100} /></label>
          <label>State / region<input name="state" required maxLength={100} /></label>
          <label className="live-form__wide">Street address<input name="address" required maxLength={255} /></label>
          <label>Postal code<input name="pincode" required maxLength={20} /></label>
          <label>Floor number (0 = ground)<input name="floor_id" type="number" min="-10" max="100" defaultValue="0" required /></label>
          <label>Spaces on this floor<input name="total_spots" type="number" min="1" max="500" defaultValue="10" required /></label>
          <label>Latitude<input name="latitude" type="number" step="any" min="-90" max="90" value={location.latitude} onChange={(event) => setLocation((current) => ({ ...current, latitude: event.target.value }))} required /></label>
          <label>Longitude<input name="longitude" type="number" step="any" min="-180" max="180" value={location.longitude} onChange={(event) => setLocation((current) => ({ ...current, longitude: event.target.value }))} required /></label>
        </div>
        <div className="live-actions"><button className="live-button" type="button" onClick={useCurrentLocation} disabled={locationPending}>{locationPending ? 'Finding location…' : 'Use my current location'}</button><button className="live-button live-button--primary" type="submit" disabled={pending || locationPending}>{pending ? 'Saving…' : 'Create location'}</button></div>
      </form>
    </section>
  )
}

export default function MerchantDashboard({ pageId }) {
  const { session } = useAuth()
  const [lots, setLots] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)
  const [pendingId, setPendingId] = useState(null)
  const [rateDrafts, setRateDrafts] = useState({})

  useEffect(() => {
    let active = true
    async function load() {
      setLoading(true)
      setError('')
      try {
        const result = await getMerchantLots(session.accessToken)
        if (active) setLots(result.parking_lots || [])
      } catch (requestError) {
        if (active) setError(requestError.message)
      } finally {
        if (active) setLoading(false)
      }
    }
    load()
    return () => { active = false }
  }, [session.accessToken, refreshKey])

  async function changeLot(lot, changes) {
    setPendingId(lot.id)
    setError('')
    setNotice('')
    try {
      await updateMerchantLot(session.accessToken, lot.id, changes)
      setNotice(`${lot.location_name} was updated.`)
      setRefreshKey((value) => value + 1)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setPendingId(null)
    }
  }

  return (
    <>
      {heading(pageId === 'locations' ? 'My locations' : 'Spaces and rates', pageId === 'locations' ? 'Create real parking inventory and review your locations.' : 'Update hourly rates and listing status for your locations.')}
      <Alert>{error}</Alert><Alert kind="success">{notice}</Alert>
      {pageId === 'locations' && <CreateLotForm accessToken={session.accessToken} onCreated={() => { setNotice('Parking location created.'); setRefreshKey((value) => value + 1) }} />}
      <section style={{ marginTop: 22 }}>
        {loading ? <p className="live-loading" role="status">Loading your locations…</p> : lots.length ? (
          <div className="live-page__grid">
            {lots.map((lot) => (
              <article className="live-card" key={lot.id}>
                <LotSummary lot={lot} />
                {pageId === 'spaces' && (
                  <div className="live-card__floors">
                    <div className="live-card__facts">{lot.floors.map((floor) => <span key={floor.id}>{floor.label}: {floor.available_spots}/{floor.total_spots} spaces</span>)}</div>
                    <label className="live-form">Hourly rate ({lot.currency})<input aria-label={`Hourly rate for ${lot.location_name}`} value={rateDrafts[lot.id] ?? lot.price} min="0" step="0.01" type="number" onChange={(event) => setRateDrafts((current) => ({ ...current, [lot.id]: event.target.value }))} /></label>
                    <div className="live-actions">
                      <button className="live-button live-button--primary" type="button" disabled={pendingId !== null} onClick={() => changeLot(lot, { price: Number(rateDrafts[lot.id] ?? lot.price) })}>Save rate</button>
                      <button className="live-button" type="button" disabled={pendingId !== null} onClick={() => changeLot(lot, { available: lot.available === 'ACTIVE' ? 'BLOCK' : 'ACTIVE' })}>{pendingId === lot.id ? 'Saving…' : lot.available === 'ACTIVE' ? 'Pause listing' : 'Reactivate listing'}</button>
                    </div>
                  </div>
                )}
              </article>
            ))}
          </div>
        ) : <p className="live-empty">{pageId === 'locations' ? 'You have not added any parking locations yet.' : 'No parking locations are assigned to this merchant account yet.'}</p>}
      </section>
    </>
  )
}
