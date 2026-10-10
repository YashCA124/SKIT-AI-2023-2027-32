const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '')

function apiErrorMessage(data, status) {
  const detail = data?.detail
  if (Array.isArray(detail)) return detail.map((issue) => issue.msg).filter(Boolean).join(' ')
  if (typeof detail === 'string') return detail
  return data?.message || `The request failed (HTTP ${status}).`
}

export async function apiRequest(path, options = {}) {
  const headers = { Accept: 'application/json', ...options.headers }
  if (options.body) headers['Content-Type'] = 'application/json'
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  let data
  try {
    data = await response.json()
  } catch {
    data = null
  }
  if (!response.ok) {
    const error = new Error(apiErrorMessage(data, response.status))
    error.status = response.status
    throw error
  }
  if (data === null && response.status !== 204) throw new Error('The API returned an unreadable response.')
  return data
}
