import { useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { apiRequest } from '../api.js'

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') || ''
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    if (password !== confirm) {
      setError("The passwords don't match.")
      return
    }
    setBusy(true)
    setError('')
    try {
      await apiRequest('/auth/reset-password', { method: 'POST', body: { token, password }, auth: false })
      setDone(true)
    } catch (err) {
      setError(err.fieldErrors?.password || err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-card">
        <Link to="/" className="brand">
          Job Tracker
        </Link>
        <h1>Choose a new password</h1>

        {!token ? (
          <p className="notice">
            This link is missing its reset code. <Link to="/forgot-password">Request a new link</Link>.
          </p>
        ) : done ? (
          <>
            <p className="notice notice-success">Your password has been reset, and you've been logged out everywhere else.</p>
            <Link to="/login" className="button button-wide auth-cta">
              Log in
            </Link>
          </>
        ) : (
          <form onSubmit={handleSubmit} noValidate>
            <div className="field">
              <label htmlFor="new-password">New password</label>
              <input
                id="new-password"
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <p className="field-hint">At least 8 characters.</p>
            </div>
            <div className="field">
              <label htmlFor="confirm-password">Confirm new password</label>
              <input
                id="confirm-password"
                type="password"
                autoComplete="new-password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
              />
            </div>
            {error && (
              <p className="form-error" role="alert">
                {error}{' '}
                {error.includes('expired') && <Link to="/forgot-password">Request a new link</Link>}
              </p>
            )}
            <button type="submit" className="button button-wide" disabled={busy || !password || !confirm}>
              {busy ? 'Saving…' : 'Reset password'}
            </button>
          </form>
        )}
      </div>
    </main>
  )
}
