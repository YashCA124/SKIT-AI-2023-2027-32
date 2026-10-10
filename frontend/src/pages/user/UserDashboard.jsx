import { useEffect, useState } from 'react'
import useAuth from '../../auth/useAuth.js'
import Alert from '../../components/Alert.jsx'
import { createBooking, endBooking, getBookings, getParkingLots } from '../../api/parking.js'
import { formatRate } from '../../utils/formatRate.js'
import '../LiveDashboard.css'

function heading(eyebrow, title, description) {
  return <header className="live-page__heading"><div><p className="live-page__eyebrow">{eyebrow}</p><h1>{title}</h1><p>{description}</p></div></header>
}

function UserParking({ accessToken }) {
  const [cityInput, setCityInput] = useState('')
  const [city, setCity] = useState('')
  const [lots, setLots] = useState([])
  const [loading, setLoading] = useState(true)
  const [pendingSpot, setPendingSpot] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    let active = true
    async function load() {
      setLoading(true)
      setError('')
      try {
        const result = await getParkingLots(accessToken, city)
        if (active) setLots(result.parking_lots || [])
      } catch (requestError) {
        if (active) setError(requestError.message)
      } finally {
        if (active) setLoading(false)
      }
    }
    load()
    return () => { active = false }
  }, [accessToken, city, refreshKey])

  async function book(space) {
    setPendingSpot(space.id)
    setError('')
    setNotice('')
    try {
      const booking = await createBooking(accessToken, space.id)
      setNotice(`Parking started at ${booking.lot.name}, space ${booking.spot_label}. No payment was charged.`)
      setRefreshKey((value) => value + 1)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setPendingSpot(null)
    }
  }

  return (
    <>
      {heading('Driver · live inventory', 'Find parking', 'Search active locations and reserve an actual available space.')}
      <p className="live-note">Reservations are saved in the database. This local build does not process or collect payments.</p>
      <Alert>{error}</Alert>
      <Alert kind="success">{notice}</Alert>
      <form className="live-inline-search" onSubmit={(event) => { event.preventDefault(); setCity(cityInput.trim()) }}>
        <label className="sr-only" htmlFor="parking-city-search">Filter by city</label>
        <input id="parking-city-search" value={cityInput} onChange={(event) => setCityInput(event.target.value)} placeholder="Filter by city" />
        <button className="live-button live-button--primary" type="submit">Search</button>
      </form>
      {loading ? <p className="live-loading" role="status">Loading available parking…</p> : lots.length ? (
        <div className="live-page__grid" style={{ marginTop: 18 }}>
          {lots.map((lot) => (
            <article className="live-card" key={lot.id}>
              <div className="live-card__top"><div><h2>{lot.location_name}</h2><p className="live-card__address">{lot.address}, {lot.city}, {lot.state}</p></div><span className={lot.available_spots ? 'live-chip' : 'live-chip live-chip--warning'}>{lot.available_spots} available</span></div>
              <div className="live-card__facts"><span>{formatRate(lot.price, lot.currency)} / hour</span><span>{lot.floor_count} floors</span><span>{lot.total_spots} spaces</span></div>
              {lot.available_spaces?.length > 0 ? (
                <div className="live-actions">
                  {lot.available_spaces.map((space) => <button className="live-button live-button--primary" disabled={pendingSpot !== null} key={space.id} onClick={() => book(space)} type="button">{pendingSpot === space.id ? 'Reserving…' : `Start at ${space.label}`}</button>)}
                </div>
              ) : <p>No reservable spaces are currently available at this location.</p>}
            </article>
          ))}
        </div>
      ) : <p className="live-empty" style={{ marginTop: 18 }}>No active parking locations with available spaces match this search.</p>}
    </>
  )
}

function UserBookings({ accessToken }) {
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)
  const [pendingId, setPendingId] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    let active = true
    async function load() {
      setLoading(true)
      setError('')
      try {
        const result = await getBookings(accessToken)
        if (active) setBookings(result.bookings || [])
      } catch (requestError) {
        if (active) setError(requestError.message)
      } finally {
        if (active) setLoading(false)
      }
    }
    load()
    return () => { active = false }
  }, [accessToken, refreshKey])

  async function finish(booking) {
    setPendingId(booking.id)
    setError('')
    setNotice('')
    try {
      await endBooking(accessToken, booking.id)
      setNotice(`Parking ended for booking #${booking.id}.`)
      setRefreshKey((value) => value + 1)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setPendingId(null)
    }
  }

  return (
    <>
      {heading('Driver · saved reservations', 'My bookings', 'View your active and completed parking sessions.')}
      <p className="live-note">Ending an active session records the actual end time and makes the space available again. No charge is collected.</p>
      <Alert>{error}</Alert><Alert kind="success">{notice}</Alert>
      {loading ? <p className="live-loading" role="status">Loading bookings…</p> : bookings.length ? (
        <div className="live-page__grid">
          {bookings.map((booking) => (
            <article className="live-card" key={booking.id}>
              <div className="live-card__top"><div><h2>{booking.lot.name}</h2><p className="live-card__address">{booking.lot.address}</p></div><span className={booking.status === 'ACTIVE' ? 'live-chip' : 'live-chip live-chip--muted'}>{booking.status === 'ACTIVE' ? 'Active' : 'Completed'}</span></div>
              <div className="live-card__facts"><span>Space {booking.spot_label}</span><span>Started {new Date(booking.parking_timestamp).toLocaleString()}</span>{booking.leaving_timestamp && <span>Ended {new Date(booking.leaving_timestamp).toLocaleString()}</span>}</div>
              {booking.total_cost !== null && <p>Calculated parking cost: {formatRate(booking.total_cost, booking.currency)}. No payment was processed.</p>}
              {booking.status === 'ACTIVE' && <button className="live-button live-button--danger" disabled={pendingId !== null} onClick={() => finish(booking)} type="button">{pendingId === booking.id ? 'Ending…' : 'End parking'}</button>}
            </article>
          ))}
        </div>
      ) : <p className="live-empty">You do not have any bookings yet. Find parking to start a session.</p>}
    </>
  )
}

function UserPayments() {
  return (
    <>
      {heading('Driver · billing', 'Payments', 'Payment collection is not connected in this local build.')}
      <div className="live-note live-note--warning"><strong>No payment provider is configured.</strong> Parking sessions are stored, but this app does not collect card or bank details, create transactions, or charge users.</div>
      <p className="live-empty">There is no payment history to show because no transactions have been processed.</p>
    </>
  )
}

export default function UserDashboard({ pageId }) {
  const { session } = useAuth()
  if (pageId === 'bookings') return <UserBookings accessToken={session.accessToken} />
  if (pageId === 'payments') return <UserPayments />
  return <UserParking accessToken={session.accessToken} />
}
