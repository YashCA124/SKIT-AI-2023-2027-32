import { apiRequest } from './client.js'

function bearer(token) {
  return { Authorization: `Bearer ${token}` }
}

export function loginUser(credentials) {
  return apiRequest('/auth/userlogin', {
    method: 'POST',
    body: JSON.stringify(credentials),
  })
}

export function loginAdmin(credentials) {
  return apiRequest('/auth/adminlogin', {
    method: 'POST',
    body: JSON.stringify(credentials),
  })
}

export function registerUser(details) {
  return apiRequest('/auth/registration', {
    method: 'POST',
    body: JSON.stringify(details),
  })
}

export function verifySession(accessToken) {
  return apiRequest('/tokenauth/protected', { headers: bearer(accessToken) })
}

export function refreshSession(refreshToken) {
  return apiRequest('/tokenauth/refresh', {
    method: 'POST',
    headers: bearer(refreshToken),
  })
}

export function logoutCurrent(accessToken) {
  return apiRequest('/auth/logoutcurrent', {
    method: 'POST',
    headers: bearer(accessToken),
  })
}

export function logoutRefresh(refreshToken) {
  return apiRequest('/auth/logoutrefresh', {
    method: 'POST',
    headers: bearer(refreshToken),
  })
}
