import { apiRequest } from './client.js'

function request(path, accessToken, options = {}) {
  return apiRequest(path, {
    ...options,
    headers: {
      Authorization: `Bearer ${accessToken}`,
      ...options.headers,
    },
  })
}

function post(path, accessToken, body) {
  return request(path, accessToken, { method: 'POST', body: JSON.stringify(body) })
}

function patch(path, accessToken, body) {
  return request(path, accessToken, { method: 'PATCH', body: JSON.stringify(body) })
}

function remove(path, accessToken) {
  return request(path, accessToken, { method: 'DELETE' })
}

export function getAccount(accessToken) {
  return request('/api/account', accessToken)
}

export function getParkingLots(accessToken, city = '') {
  const query = city ? `?city=${encodeURIComponent(city)}` : ''
  return request(`/api/parking/lots${query}`, accessToken)
}

export function getBookings(accessToken) {
  return request('/api/bookings', accessToken)
}

export function createBooking(accessToken, spotId) {
  return post('/api/bookings', accessToken, { spot_id: spotId })
}

export function endBooking(accessToken, bookingId) {
  return post(`/api/bookings/${bookingId}/end`, accessToken, {})
}

export function simulatePayment(accessToken, paymentId, outcome) {
  return post(`/api/payments/${paymentId}/simulate`, accessToken, { outcome })
}

export function getMerchantLots(accessToken) {
  return request('/api/merchant/lots', accessToken)
}

export function createMerchantLot(accessToken, lot) {
  return post('/api/merchant/lots', accessToken, lot)
}

export function updateMerchantLot(accessToken, lotId, changes) {
  return patch(`/api/merchant/lots/${lotId}`, accessToken, changes)
}

export function getAdminUsers(accessToken) {
  return request('/api/admin/users', accessToken)
}

export function updateAdminUserRole(accessToken, userId, role) {
  return patch(`/api/admin/users/${userId}/role`, accessToken, { role })
}

export function deleteAdminMerchant(accessToken, userId) {
  return remove(`/api/admin/users/${userId}`, accessToken)
}

export function getAdminLots(accessToken) {
  return request('/api/admin/parking-lots', accessToken)
}

export function updateAdminLotStatus(accessToken, lotId, available) {
  return patch(`/api/admin/parking-lots/${lotId}`, accessToken, { available })
}

export function updateAdminLot(accessToken, lotId, changes) {
  return patch(`/api/admin/parking-lots/${lotId}/details`, accessToken, changes)
}

export function deleteAdminLot(accessToken, lotId) {
  return remove(`/api/admin/parking-lots/${lotId}`, accessToken)
}
