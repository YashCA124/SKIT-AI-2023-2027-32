import { useEffect, useState } from 'react'
import useAuth from '../../auth/useAuth.js'
import Alert from '../../components/Alert.jsx'
import { getAdminLots, getAdminUsers, promoteUserToMerchant, updateAdminLotStatus } from '../../api/parking.js'
import '../LiveDashboard.css'

function heading(title, description) {
  return <header className="live-page__heading"><div><p className="live-page__eyebrow">Administrator · live records</p><h1>{title}</h1><p>{description}</p></div></header>
}

export default function AdminDashboard({ pageId }) {
  const { session } = useAuth()
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [pendingId, setPendingId] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const isUsersPage = pageId === 'users'

  useEffect(() => {
    let active = true
    async function load() {
      setLoading(true)
      setError('')
      try {
        const result = isUsersPage
          ? await getAdminUsers(session.accessToken)
          : await getAdminLots(session.accessToken)
        if (active) setRecords(isUsersPage ? result.users || [] : result.parking_lots || [])
      } catch (requestError) {
        if (active) setError(requestError.message)
      } finally {
        if (active) setLoading(false)
      }
    }
    load()
    return () => { active = false }
  }, [isUsersPage, session.accessToken, refreshKey])

  async function perform(id, action) {
    setPendingId(id)
    setError('')
    setNotice('')
    try {
      await action()
      setNotice('The record was updated.')
      setRefreshKey((value) => value + 1)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setPendingId(null)
    }
  }

  return (
    <>
      {heading(isUsersPage ? 'User accounts' : 'Parking locations', isUsersPage ? 'Review actual registered accounts and grant merchant access.' : 'Review actual merchant locations and pause or restore listings.')}
      <Alert>{error}</Alert><Alert kind="success">{notice}</Alert>
      {loading ? <p className="live-loading" role="status">Loading records…</p> : records.length ? (
        <div className="live-table-wrap">
          <table className="live-table">
            <thead>{isUsersPage
              ? <tr><th>Name</th><th>Email</th><th>Location</th><th>Role</th><th>Action</th></tr>
              : <tr><th>Location</th><th>Owner</th><th>City</th><th>Availability</th><th>Spaces</th><th>Action</th></tr>}
            </thead>
            <tbody>{records.map((record) => isUsersPage ? (
              <tr key={record.id}>
                <td>{record.name}</td><td>{record.email}</td><td>{record.city}, {record.country}</td>
                <td><span className="live-chip">{record.role === 'M' ? 'Merchant' : 'Driver'}</span></td>
                <td>{record.role === 'U' ? <button className="live-button" type="button" disabled={pendingId !== null} onClick={() => perform(record.id, () => promoteUserToMerchant(session.accessToken, record.id))}>{pendingId === record.id ? 'Updating…' : 'Grant merchant access'}</button> : '—'}</td>
              </tr>
            ) : (
              <tr key={record.id}>
                <td>{record.location_name}</td><td>{record.owner_name || `Account ${record.owner_id}`}</td><td>{record.city}, {record.country}</td>
                <td><span className={record.available === 'ACTIVE' ? 'live-chip' : 'live-chip live-chip--warning'}>{record.available}</span></td>
                <td>{record.available_spots} / {record.total_spots}</td>
                <td><button className="live-button" type="button" disabled={pendingId !== null} onClick={() => perform(record.id, () => updateAdminLotStatus(session.accessToken, record.id, record.available === 'ACTIVE' ? 'BLOCK' : 'ACTIVE'))}>{pendingId === record.id ? 'Updating…' : record.available === 'ACTIVE' ? 'Pause listing' : 'Reactivate'}</button></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      ) : <p className="live-empty">{isUsersPage ? 'No user accounts are registered yet.' : 'No parking locations have been created yet.'}</p>}
    </>
  )
}
