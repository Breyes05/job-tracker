import { useState } from 'react'
import Dialog from './Dialog.jsx'

export default function ConfirmDelete({ application, onConfirm, onClose }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function handleDelete() {
    setBusy(true)
    setError('')
    try {
      await onConfirm()
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <Dialog title="Delete application?" onClose={onClose} size="sm">
      <p className="dialog-text">
        <strong>
          {application.company} · {application.role}
        </strong>{' '}
        will be permanently deleted.
      </p>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      <div className="dialog-actions">
        <button type="button" className="button button-quiet" onClick={onClose}>
          Cancel
        </button>
        <button type="button" className="button button-danger" onClick={handleDelete} disabled={busy}>
          {busy ? 'Deleting…' : 'Delete'}
        </button>
      </div>
    </Dialog>
  )
}
