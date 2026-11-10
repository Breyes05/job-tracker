// The one place the frontend talks to the API: it adds the base URL and the
// token, turns error responses into readable messages, and reports slow
// requests (Render's free tier can take up to a minute to wake up).

const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')
const TOKEN_KEY = 'jobtracker.token'
const SLOW_REQUEST_MS = 3000

// localStorage can throw (private windows, blocked storage), so every access is guarded.
export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token) {
  try {
    localStorage.setItem(TOKEN_KEY, token)
  } catch {
    // Storage unavailable: the user stays logged in until the page reloads.
  }
}

export function clearToken() {
  try {
    localStorage.removeItem(TOKEN_KEY)
  } catch {
    // Nothing stored, nothing to clear.
  }
}

export class ApiError extends Error {
  constructor(status, message, fieldErrors = {}) {
    super(message)
    this.status = status
    this.fieldErrors = fieldErrors
  }
}

// Called when a logged-in request comes back 401 (expired or invalid token).
let handleUnauthorized = () => {}
export function onUnauthorized(handler) {
  handleUnauthorized = handler
}

// Lets the UI show a "waking up the server" notice while any request is slow.
let slowCount = 0
const slowListeners = new Set()
export function subscribeToSlowRequests(listener) {
  slowListeners.add(listener)
  return () => slowListeners.delete(listener)
}
function changeSlowCount(delta) {
  slowCount += delta
  slowListeners.forEach((listener) => listener(slowCount > 0))
}

// FastAPI returns `detail` as a string for most errors, and as a list of
// field problems for validation errors (422).
function readError(status, data) {
  const fieldErrors = {}
  let message = 'Something went wrong. Please try again.'

  if (Array.isArray(data?.detail)) {
    for (const problem of data.detail) {
      const field = problem.loc?.[problem.loc.length - 1]
      if (field && !fieldErrors[field]) fieldErrors[field] = problem.msg
    }
    message = 'Please fix the highlighted fields.'
  } else if (typeof data?.detail === 'string') {
    message = data.detail
  } else if (status >= 500) {
    message = 'The server had a problem. Please try again in a moment.'
  }
  return new ApiError(status, message, fieldErrors)
}

/**
 * Send a request to the API.
 * - `body` is sent as JSON; `form` is sent as form data (used by login).
 * - `auth: false` skips the token and the 401 handling (login and register).
 */
export async function apiRequest(path, { method = 'GET', body, form, auth = true } = {}) {
  const headers = {}
  let payload

  // form data
  if (form) {
    payload = new URLSearchParams(form)
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }

  // Every protected request proves who user is, if auth: false skip this for logins and registers
  const token = getToken()
  if (auth && token) headers.Authorization = `Bearer ${token}`

  // slow request timer, to show app is still running
  let isSlow = false
  const slowTimer = setTimeout(() => {
    isSlow = true
    changeSlowCount(1)
  }, SLOW_REQUEST_MS)

  // 
  let response
  try {
    response = await fetch(`${API_URL}${path}`, { method, headers, body: payload })
  } catch {
    throw new ApiError(0, "Couldn't reach the server. Check your connection and try again.")
  } finally {
    clearTimeout(slowTimer)
    if (isSlow) changeSlowCount(-1)
  }

  if (response.status === 401 && auth) {
    clearToken()
    handleUnauthorized()
  }

  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw readError(response.status, data)
  }

  if (response.status === 204) return null
  return response.json()
}
