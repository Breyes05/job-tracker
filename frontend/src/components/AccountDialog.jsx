import { useState } from 'react'
import { apiRequest } from '../api.js'
import { useAuth } from '../auth/AuthContext.js'
import Dialog from './Dialog.jsx'

export default function AccountDialog({ onClose }) {
  const { user, logout } = useAuth()
  const [confirming, setConfirming] = useState(false)
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleDelete(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await apiRequest('/auth/me', { method: 'DELETE', body: { password } })
      logout()
    } catch (err) {
      setError(err.status === 403 ? 'That password is incorrect.' : err.message)
      setBusy(false)
    }
  }

  return (
    <Dialog title="Account" onClose={onClose} size="sm">
      <p className="dialog-text">
        Logged in as <strong>{user.email}</strong>
      </p>

      <section className="danger-zone">
        <h3>Delete account</h3>
        <p>This permanently deletes your account, every application, and its history. It can't be undone.</p>

        {!confirming ? (
          <button type="button" className="button button-danger-outline" onClick={() => setConfirming(true)}>
            Delete my account
          </button>
        ) : (
          <form onSubmit={handleDelete} noValidate>
            <div className="field">
              <label htmlFor="delete-password">Enter your password to confirm</label>
              <input
                id="delete-password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                aria-invalid={Boolean(error)}
                autoFocus
              />
            </div>
            {error && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}
            <div className="dialog-actions">
              <button type="button" className="button button-quiet" onClick={() => setConfirming(false)}>
                Cancel
              </button>
              <button type="submit" className="button button-danger" disabled={busy || !password}>
                {busy ? 'Deleting…' : 'Delete everything'}
              </button>
            </div>
          </form>
        )}
      </section>
    </Dialog>
  )
}
