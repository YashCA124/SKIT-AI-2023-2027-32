import { useState } from 'react'
import useAuth from '../../auth/useAuth.js'
import DemoPageHeader from '../../demo/DemoPageHeader.jsx'
import '../../demo/DemoUI.css'

function DemoUsers({ data, updateData }) {
  const [query, setQuery] = useState('')
  const [notice, setNotice] = useState('')
  const normalizedQuery = query.trim().toLowerCase()
  const users = data.users.filter((user) => `${user.name} ${user.email} ${user.role} ${user.id}`.toLowerCase().includes(normalizedQuery))

  function toggleUser(user) {
    const status = user.status === 'Suspended' ? 'Active' : 'Suspended'
    updateData((current) => ({
      ...current,
      users: current.users.map((item) => item.id === user.id ? { ...item, status } : item),
    }))
    setNotice(`${user.name} is now ${status.toLowerCase()} in the demo only.`)
  }

  return (
    <>
      <DemoPageHeader eyebrow="Administrator · Sample accounts" title="User management" description="Search fictional platform accounts and simulate an account status change." notice={notice} />
      <div className="demo-stat-grid">
        <article className="demo-stat"><span>Sample accounts</span><strong>{data.users.length}</strong></article>
        <article className="demo-stat"><span>Active</span><strong>{data.users.filter((user) => user.status === 'Active').length}</strong></article>
        <article className="demo-stat"><span>Suspended</span><strong>{data.users.filter((user) => user.status === 'Suspended').length}</strong></article>
      </div>
      <div className="demo-toolbar"><h2>Platform accounts</h2><input className="demo-search" aria-label="Search sample users" placeholder="Search name, role, email…" value={query} onChange={(event) => setQuery(event.target.value)} /></div>
      {users.length ? (
        <div className="demo-table-wrap">
          <table className="demo-table">
            <thead><tr><th>Sample account</th><th>Email</th><th>Role</th><th>Status</th><th>Action</th></tr></thead>
            <tbody>{users.map((user) => (
              <tr key={user.id}>
                <td>{user.name}<br /><small>{user.id}</small></td>
                <td>{user.email}</td>
                <td>{user.role}</td>
                <td><span className={`demo-status${user.status === 'Suspended' ? ' demo-status--warning' : user.status === 'Pending' ? ' demo-status--muted' : ''}`}>{user.status}</span></td>
                <td>{user.status === 'Pending' ? <button className="demo-button" type="button" onClick={() => { updateData((current) => ({ ...current, users: current.users.map((item) => item.id === user.id ? { ...item, status: 'Active' } : item) })); setNotice(`${user.name} was activated in the demo only.`) }}>Approve (demo)</button> : <button className="demo-button" type="button" onClick={() => toggleUser(user)}>{user.status === 'Suspended' ? 'Restore (demo)' : 'Suspend (demo)'}</button>}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      ) : <p className="demo-empty">No sample accounts match “{query}”.</p>}
      <p className="demo-disclaimer">All names and accounts are fictional. Approve/suspend actions only alter this temporary demo view; no account access is changed.</p>
    </>
  )
}

function DemoLots({ data, updateData }) {
  const [notice, setNotice] = useState('')

  function toggleListing(lot) {
    const willBeListed = lot.isListed === false
    updateData((current) => ({
      ...current,
      lots: current.lots.map((item) => item.id === lot.id ? { ...item, isListed: willBeListed } : item),
    }))
    setNotice(`${lot.name} is ${willBeListed ? 'listed' : 'hidden'} in the admin demo. No live parking listing changed.`)
  }

  return (
    <>
      <DemoPageHeader eyebrow="Administrator · Sample inventory" title="Parking lot management" description="Review fictional parking inventory and simulate hiding or listing a property." notice={notice} />
      <div className="demo-stat-grid">
        <article className="demo-stat"><span>Sample parking lots</span><strong>{data.lots.length}</strong></article>
        <article className="demo-stat"><span>Listed in demo</span><strong>{data.lots.filter((lot) => lot.isListed !== false).length}</strong></article>
        <article className="demo-stat"><span>Total sample capacity</span><strong>{data.lots.reduce((sum, lot) => sum + lot.total, 0)}</strong></article>
      </div>
      <div className="demo-card-grid">
        {data.lots.map((lot) => (
          <article className="demo-card" key={lot.id}>
            <div className="demo-card__top">
              <div><h2>{lot.name}</h2><p className="demo-card__subtle">{lot.address}, {lot.city}</p></div>
              <span className={`demo-status${lot.isListed === false ? ' demo-status--muted' : lot.available === 0 ? ' demo-status--warning' : ''}`}>{lot.isListed === false ? 'Hidden' : lot.available === 0 ? 'Full' : 'Listed'}</span>
            </div>
            <div className="demo-card__details"><span>{lot.available} available</span><span>{lot.total} total spaces</span><span>₹{lot.rate} / hour</span></div>
            <button className="demo-button" type="button" onClick={() => toggleListing(lot)}>{lot.isListed === false ? 'List lot (demo)' : 'Hide lot (demo)'}</button>
          </article>
        ))}
      </div>
      <p className="demo-disclaimer">All property names, capacity, prices and availability are fictional. Listing controls do not change a real marketplace.</p>
    </>
  )
}

export default function DevAdminDemoPage({ pageId }) {
  const { session, updatePreviewData } = useAuth()
  if (pageId === 'lots') return <DemoLots data={session.demoData} updateData={updatePreviewData} />
  return <DemoUsers data={session.demoData} updateData={updatePreviewData} />
}
