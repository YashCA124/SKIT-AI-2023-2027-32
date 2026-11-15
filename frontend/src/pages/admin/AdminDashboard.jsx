import { Fragment, useEffect, useState } from 'react'
import useAuth from '../../auth/useAuth.js'
import Alert from '../../components/Alert.jsx'
import {
  deleteAdminLot,
  deleteAdminMerchant,
  getAdminLots,
  getAdminUsers,
  updateAdminLot,
  updateAdminLotStatus,
  updateAdminUserRole,
} from '../../api/parking.js'
import '../LiveDashboard.css'

function heading(title, description) {
  return <header className="live-page__heading"><div><p className="live-page__eyebrow">Administrator · live records</p><h1>{title}</h1><p>{description}</p></div></header>
}

function initialLotForm(lot) {
  return {
    location_name: lot.location_name,
    price: String(lot.price),
    currency: lot.currency,
    country: lot.country,
    city: lot.city,
    state: lot.state,
    address: lot.address,
    pincode: lot.pincode,
    owner_id: '',
  }
}

export default function AdminDashboard({ pageId }) {
  const { session } = useAuth()
  const [records, setRecords] = useState([])
  const [merchants, setMerchants] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [pendingId, setPendingId] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [editingId, setEditingId] = useState(null)
  const [editForm, setEditForm] = useState(null)
  const isUsersPage = pageId === 'users'

  useEffect(() => {
    let active = true
    async function load() {
      setLoading(true)
      setError('')
      try {
        if (isUsersPage) {
          const result = await getAdminUsers(session.accessToken)
          if (active) setRecords(result.users || [])
        } else {
          const [lotResult, userResult] = await Promise.all([
            getAdminLots(session.accessToken),
            getAdminUsers(session.accessToken),
          ])
          if (active) {
            setRecords(lotResult.parking_lots || [])
            setMerchants((userResult.users || []).filter((user) => user.role === 'M'))
          }
        }
      } catch (requestError) {
        if (active) setError(requestError.message)
      } finally {
        if (active) setLoading(false)
      }
    }
    load()
    return () => { active = false }
  }, [isUsersPage, session.accessToken, refreshKey])

  async function perform(id, action, successMessage) {
    setPendingId(id)
    setError('')
    setNotice('')
    try {
      await action()
      setNotice(successMessage)
      setEditingId(null)
      setEditForm(null)
      setRefreshKey((value) => value + 1)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setPendingId(null)
    }
  }

  function removeMerchant(user) {
    if (!window.confirm(`Permanently delete merchant account ${user.name}? Accounts with parking lots or booking history cannot be deleted.`)) return
    perform(user.id, () => deleteAdminMerchant(session.accessToken, user.id), 'Merchant account deleted.')
  }

  function removeLot(lot) {
    if (!window.confirm(`Permanently delete "${lot.location_name}"? Locations with booking history cannot be deleted.`)) return
    perform(lot.id, () => deleteAdminLot(session.accessToken, lot.id), 'Parking location deleted.')
  }

  async function saveLot(event, lotId) {
    event.preventDefault()
    const changes = {
      ...editForm,
      price: Number(editForm.price),
    }
    if (editForm.owner_id) changes.owner_id = Number(editForm.owner_id)
    else delete changes.owner_id
    await perform(lotId, () => updateAdminLot(session.accessToken, lotId, changes), 'Parking location updated.')
  }

  function editField(name, label, type = 'text') {
    return (
      <label key={name}>
        {label}
        <input
          name={name}
          type={type}
          value={editForm[name]}
          min={type === 'number' ? '0' : undefined}
          step={type === 'number' ? '0.01' : undefined}
          required
          onChange={(event) => setEditForm((current) => ({ ...current, [name]: event.target.value }))}
        />
      </label>
    )
  }

  return (
    <>
      {heading(
        isUsersPage ? 'User accounts' : 'Parking locations',
        isUsersPage
          ? 'Grant or revoke merchant access, or remove eligible merchant accounts.'
          : 'Edit location details, transfer ownership, control listing availability, or remove eligible locations.',
      )}
      <Alert>{error}</Alert><Alert kind="success">{notice}</Alert>
      {loading ? <p className="live-loading" role="status">Loading records…</p> : records.length ? (
        <div className="live-table-wrap">
          <table className="live-table">
            <thead>{isUsersPage
              ? <tr><th>Name</th><th>Email</th><th>Location</th><th>Role</th><th>Actions</th></tr>
              : <tr><th>Location</th><th>Owner</th><th>City</th><th>Availability</th><th>Spaces</th><th>Actions</th></tr>}
            </thead>
            <tbody>{records.map((record) => isUsersPage ? (
              <tr key={record.id}>
                <td>{record.name}</td><td>{record.email}</td><td>{record.city}, {record.country}</td>
                <td><span className="live-chip">{record.role === 'M' ? 'Merchant' : 'Driver'}</span></td>
                <td><div className="live-actions">
                  {record.role === 'U' ? (
                    <button className="live-button" type="button" disabled={pendingId !== null} onClick={() => perform(record.id, () => updateAdminUserRole(session.accessToken, record.id, 'M'), 'Merchant access granted.')}>
                      {pendingId === record.id ? 'Updating…' : 'Grant merchant access'}
                    </button>
                  ) : (
                    <>
                      <button className="live-button" type="button" disabled={pendingId !== null} onClick={() => perform(record.id, () => updateAdminUserRole(session.accessToken, record.id, 'U'), 'Merchant access revoked.')}>
                        {pendingId === record.id ? 'Updating…' : 'Revoke access'}
                      </button>
                      <button className="live-button live-button--danger" type="button" disabled={pendingId !== null} onClick={() => removeMerchant(record)}>
                        Delete merchant
                      </button>
                    </>
                  )}
                </div></td>
              </tr>
            ) : (
              <Fragment key={record.id}>
                <tr key={record.id}>
                  <td>{record.location_name}</td><td>{record.owner_name || `Account ${record.owner_id}`}</td><td>{record.city}, {record.country}</td>
                  <td><span className={record.available === 'ACTIVE' ? 'live-chip' : 'live-chip live-chip--warning'}>{record.available}</span></td>
                  <td>{record.available_spots} / {record.total_spots}</td>
                  <td><div className="live-actions">
                    <button className="live-button" type="button" disabled={pendingId !== null} onClick={() => {
                      setEditingId(editingId === record.id ? null : record.id)
                      setEditForm(editingId === record.id ? null : initialLotForm(record))
                      setError('')
                    }}>
                      {editingId === record.id ? 'Cancel edit' : 'Edit'}
                    </button>
                    <button className="live-button" type="button" disabled={pendingId !== null} onClick={() => perform(record.id, () => updateAdminLotStatus(session.accessToken, record.id, record.available === 'ACTIVE' ? 'BLOCK' : 'ACTIVE'), `Parking location ${record.available === 'ACTIVE' ? 'paused' : 'reactivated'}.`)}>
                      {pendingId === record.id ? 'Updating…' : record.available === 'ACTIVE' ? 'Pause listing' : 'Reactivate'}
                    </button>
                    <button className="live-button live-button--danger" type="button" disabled={pendingId !== null} onClick={() => removeLot(record)}>
                      Delete
                    </button>
                  </div></td>
                </tr>
                {editingId === record.id && editForm && (
                  <tr key={`${record.id}-edit`}>
                    <td colSpan="6">
                      <form className="live-form" onSubmit={(event) => saveLot(event, record.id)}>
                        <div className="live-form__grid">
                          {editField('location_name', 'Location name')}
                          {editField('price', `Hourly rate (${editForm.currency})`, 'number')}
                          {editField('currency', 'Currency code')}
                          {editField('country', 'Country code')}
                          {editField('city', 'City')}
                          {editField('state', 'State')}
                          {editField('address', 'Street address')}
                          {editField('pincode', 'Postal code')}
                          <label>
                            Transfer to merchant
                            <select
                              name="owner_id"
                              value={editForm.owner_id}
                              onChange={(event) => setEditForm((current) => ({ ...current, owner_id: event.target.value }))}
                            >
                              <option value="">Keep current owner</option>
                              {merchants.filter((merchant) => merchant.id !== record.owner_id).map((merchant) => (
                                <option key={merchant.id} value={merchant.id}>{merchant.name} · {merchant.email}</option>
                              ))}
                            </select>
                          </label>
                        </div>
                        <div className="live-actions">
                          <button className="live-button live-button--primary" type="submit" disabled={pendingId !== null}>
                            {pendingId === record.id ? 'Saving…' : 'Save changes'}
                          </button>
                          <button className="live-button" type="button" disabled={pendingId !== null} onClick={() => { setEditingId(null); setEditForm(null) }}>Cancel</button>
                        </div>
                      </form>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}</tbody>
          </table>
        </div>
      ) : <p className="live-empty">{isUsersPage ? 'No user accounts are registered yet.' : 'No parking locations have been created yet.'}</p>}
    </>
  )
}
