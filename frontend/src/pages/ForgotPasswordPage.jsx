import { useState } from 'react'
import { Link } from 'react-router'
import { apiRequest } from '../api.js'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [sent, setSent] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await apiRequest('/auth/forgot-password', { method: 'POST', body: { email: email.trim() }, auth: false })
      setSent(true)
    } catch (err) {
      setError(err.fieldErrors?.email || err.message)
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
        <h1>Reset your password</h1>

        {sent ? (
          <p className="notice notice-success">
            If an account exists for <strong>{email.trim()}</strong>, we've sent a link to reset the password. It expires in
            an hour. Check your spam folder if you don't see it.
          </p>
        ) : (
          <form onSubmit={handleSubmit} noValidate>
            <p className="auth-intro">Enter the email you signed up with and we'll send you a link to choose a new password.</p>
            <div className="field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                aria-invalid={Boolean(error)}
                required
              />
            </div>
            {error && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}
            <button type="submit" className="button button-wide" disabled={busy || !email.trim()}>
              {busy ? 'Sending…' : 'Send reset link'}
            </button>
          </form>
        )}

        <p className="auth-footer">
          Remembered it? <Link to="/login">Log in</Link>
        </p>
      </div>
    </main>
  )
}
