import { useState } from 'react'
import useAuth from '../../auth/useAuth.js'
import DemoPageHeader from '../../demo/DemoPageHeader.jsx'
import '../../demo/DemoUI.css'

function DemoStats({ items }) {
  return (
    <div className="demo-stat-grid">
      {items.map((item) => <article className="demo-stat" key={item.label}><span>{item.label}</span><strong>{item.value}</strong></article>)}
    </div>
  )
}

function ParkingSearch({ data, updateData }) {
  const [query, setQuery] = useState('')
  const [notice, setNotice] = useState('')
  const normalizedQuery = query.trim().toLowerCase()
  const lots = data.lots.filter((lot) => lot.isListed !== false && `${lot.name} ${lot.address} ${lot.city}`.toLowerCase().includes(normalizedQuery))

  function bookParking(lot) {
    let booked = false
    updateData((current) => {
      const selectedLot = current.lots.find((item) => item.id === lot.id)
      if (!selectedLot || selectedLot.status !== 'Open' || selectedLot.available < 1) return current
      booked = true
      const bookingNumber = current.nextBookingNumber
      return {
        ...current,
        nextBookingNumber: bookingNumber + 1,
        lots: current.lots.map((item) => item.id === lot.id ? { ...item, available: item.available - 1 } : item),
        bookings: [{
          id: `DEMO-B${String(2100 + bookingNumber).padStart(4, '0')}`,
          lotId: lot.id,
          lotName: lot.name,
          spot: `D-${String(bookingNumber).padStart(2, '0')}`,
          time: 'Just now (demo)',
          until: 'In 2 hours (demo)',
          amount: lot.rate * 2,
          status: 'Active',
        }, ...current.bookings],
      }
    })
    setNotice(booked
      ? `Demo booking created at ${lot.name}. No reservation or payment was sent to a server.`
      : 'That demo lot no longer has an available space.')
  }

  return (
    <>
      <DemoPageHeader eyebrow="Driver · Sample inventory" title="Find parking" description="Search the fictional lots, compare hourly rates, and create a simulated two-hour booking." notice={notice} />
      <DemoStats items={[
        { label: 'Sample locations', value: data.lots.length },
        { label: 'Open spaces', value: data.lots.reduce((total, lot) => total + lot.available, 0) },
        { label: 'Active demo bookings', value: data.bookings.filter((booking) => booking.status === 'Active').length },
      ]} />
      <div className="demo-toolbar"><h2>Nearby sample locations</h2><input className="demo-search" aria-label="Search sample parking locations" placeholder="Search locations…" value={query} onChange={(event) => setQuery(event.target.value)} /></div>
      {lots.length ? (
        <div className="demo-card-grid">
          {lots.map((lot) => (
            <article className="demo-card" key={lot.id}>
              <div className="demo-card__top">
                <div><h2>{lot.name}</h2><p className="demo-card__subtle">{lot.address}, {lot.city}</p></div>
                <span className={`demo-status${lot.status === 'Open' && lot.available > 0 ? '' : ' demo-status--warning'}`}>{lot.available > 0 ? lot.status : 'Full'}</span>
              </div>
              <div className="demo-card__details"><span>{lot.available} of {lot.total} spaces</span><span>₹{lot.rate} / hour</span><span>{lot.floor} floors</span></div>
              <button className="demo-button demo-button--primary" type="button" disabled={lot.status !== 'Open' || lot.available < 1} onClick={() => bookParking(lot)}>
                {lot.status === 'Open' && lot.available > 0 ? 'Book for 2 hours' : 'Unavailable'}
              </button>
            </article>
          ))}
        </div>
      ) : <p className="demo-empty">No sample locations match “{query}”. Try another search.</p>}
      <p className="demo-disclaimer">Fictional presentation data. Booking buttons only change this temporary demo state; no real parking is reserved or charged.</p>
    </>
  )
}

function DemoBookings({ data, updateData }) {
  const [notice, setNotice] = useState('')

  function cancelBooking(booking) {
    updateData((current) => ({
      ...current,
      bookings: current.bookings.map((item) => item.id === booking.id && item.status === 'Active' ? { ...item, status: 'Cancelled' } : item),
      lots: current.lots.map((lot) => lot.id === booking.lotId && booking.status === 'Active' ? { ...lot, available: Math.min(lot.total, lot.available + 1) } : lot),
    }))
    setNotice(`${booking.id} was cancelled in the demo only. No server or real reservation was changed.`)
  }

  return (
    <>
      <DemoPageHeader eyebrow="Driver · Sample reservations" title="My bookings" description="Review sample reservation states and simulate cancelling an active reservation." notice={notice} />
      <DemoStats items={[
        { label: 'Active', value: data.bookings.filter((booking) => booking.status === 'Active').length },
        { label: 'Completed', value: data.bookings.filter((booking) => booking.status === 'Completed').length },
        { label: 'Cancelled', value: data.bookings.filter((booking) => booking.status === 'Cancelled').length },
      ]} />
      {data.bookings.length ? (
        <div className="demo-card-grid">
          {data.bookings.map((booking) => (
            <article className="demo-card" key={booking.id}>
              <div className="demo-card__top"><div><h2>{booking.lotName}</h2><p className="demo-card__subtle">{booking.id} · Space {booking.spot}</p></div><span className={`demo-status${booking.status === 'Active' ? '' : ' demo-status--muted'}`}>{booking.status}</span></div>
              <div className="demo-card__details"><span>{booking.time}</span><span>Until {booking.until}</span><span>₹{booking.amount} (sample)</span></div>
              {booking.status === 'Active' && <button className="demo-button" type="button" onClick={() => cancelBooking(booking)}>Cancel demo booking</button>}
            </article>
          ))}
        </div>
      ) : <p className="demo-empty">There are no sample bookings yet. Use Find parking to create one.</p>}
      <p className="demo-disclaimer">All bookings and amounts are fictional examples. Cancellation is simulated and does not contact the backend.</p>
    </>
  )
}

function DemoPayments({ data }) {
  return (
    <>
      <DemoPageHeader eyebrow="Driver · Sample history" title="Payments" description="This page demonstrates how a payment history could be presented. It does not connect to a payment provider." />
      <div className="demo-stat-grid"><article className="demo-stat"><span>Sample transactions</span><strong>{data.payments.length}</strong></article><article className="demo-stat"><span>Sample total</span><strong>₹{data.payments.reduce((sum, payment) => sum + payment.amount, 0)}</strong></article><article className="demo-stat"><span>Real payment service</span><strong>Not connected</strong></article></div>
      <div className="demo-table-wrap">
        <table className="demo-table">
          <thead><tr><th>Reference</th><th>Date</th><th>Parking</th><th>Method</th><th>Amount</th><th>Status</th></tr></thead>
          <tbody>{data.payments.map((payment) => <tr key={payment.id}><td>{payment.id}</td><td>{payment.date}</td><td>{payment.description}</td><td>{payment.method}</td><td>₹{payment.amount}</td><td><span className="demo-status">{payment.status} · sample</span></td></tr>)}</tbody>
        </table>
      </div>
      <p className="demo-disclaimer">These are fictional sample transactions for a presentation. No card details, payment requests, or charges are processed.</p>
    </>
  )
}

export default function DevUserDemoPage({ pageId }) {
  const { session, updatePreviewData } = useAuth()
  const data = session.demoData
  if (pageId === 'bookings') return <DemoBookings data={data} updateData={updatePreviewData} />
  if (pageId === 'payments') return <DemoPayments data={data} />
  return <ParkingSearch data={data} updateData={updatePreviewData} />
}
