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

export function promoteUserToMerchant(accessToken, userId) {
  return patch(`/api/admin/users/${userId}/role`, accessToken, { role: 'M' })
}

export function getAdminLots(accessToken) {
  return request('/api/admin/parking-lots', accessToken)
}

export function updateAdminLotStatus(accessToken, lotId, available) {
  return patch(`/api/admin/parking-lots/${lotId}`, accessToken, { available })
}
