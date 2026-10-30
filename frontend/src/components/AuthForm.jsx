import { useState } from 'react'
import { Link } from 'react-router'

// Shared layout for the login and register pages.
export default function AuthForm({ title, submitLabel, busyLabel, onSubmit, notice, footer, passwordHint }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setFieldErrors({})
    try {
      await onSubmit(email.trim(), password)
    } catch (err) {
      setError(err.message)
      setFieldErrors(err.fieldErrors || {})
      setBusy(false)
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-card">
        <Link to="/" className="brand">
          Job Tracker
        </Link>
        <h1>{title}</h1>

        {notice && <p className="notice">{notice}</p>}

        <form onSubmit={handleSubmit} noValidate>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              aria-invalid={Boolean(fieldErrors.email)}
              required
            />
            {fieldErrors.email && <p className="field-error">{fieldErrors.email}</p>}
          </div>

          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              autoComplete={passwordHint ? 'new-password' : 'current-password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              aria-invalid={Boolean(fieldErrors.password)}
              required
            />
            {passwordHint && !fieldErrors.password && <p className="field-hint">{passwordHint}</p>}
            {fieldErrors.password && <p className="field-error">{fieldErrors.password}</p>}
          </div>

          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}

          <button type="submit" className="button button-wide" disabled={busy}>
            {busy ? busyLabel : submitLabel}
          </button>
        </form>

        <p className="auth-footer">{footer}</p>
      </div>
    </main>
  )
}
