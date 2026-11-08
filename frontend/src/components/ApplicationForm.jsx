import { useState } from 'react'
import { apiRequest } from '../api.js'
import { STATUSES } from '../statuses.js'
import Dialog from './Dialog.jsx'

// Today's date as "YYYY-MM-DD" in the user's own time zone.
function todayLocal() {
  const now = new Date()
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

function initialValues(application) {
  return {
    company: application?.company ?? '',
    role: application?.role ?? '',
    status: application?.status ?? 'applied',
    date_applied: application?.date_applied ?? todayLocal(),
    job_url: application?.job_url ?? '',
    notes: application?.notes ?? '',
  }
}

// Add a new application, or edit an existing one when `application` is given.
export default function ApplicationForm({ application, onSaved, onClose, onDelete }) {
  const isNew = !application
  const [values, setValues] = useState(() => initialValues(application))
  const [fieldErrors, setFieldErrors] = useState({})
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  function update(field) {
    return (event) => setValues((current) => ({ ...current, [field]: event.target.value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setFieldErrors({})

    // Empty optional fields are sent as null so the API clears them.
    const body = {
      company: values.company.trim(),
      role: values.role.trim(),
      status: values.status,
      date_applied: values.date_applied,
      job_url: values.job_url.trim() || null,
      notes: values.notes.trim() || null,
    }

    try {
      const saved = await apiRequest(isNew ? '/applications' : `/applications/${application.id}`, {
        method: isNew ? 'POST' : 'PATCH',
        body,
      })
      onSaved(saved, isNew)
    } catch (err) {
      setError(err.message)
      setFieldErrors(err.fieldErrors || {})
      setBusy(false)
    }
  }

  function fieldProps(field) {
    return {
      id: `app-${field}`,
      value: values[field],
      onChange: update(field),
      'aria-invalid': Boolean(fieldErrors[field]),
    }
  }

  function fieldError(field) {
    return fieldErrors[field] ? <p className="field-error">{fieldErrors[field]}</p> : null
  }

  return (
    <Dialog title={isNew ? 'Add application' : 'Edit application'} onClose={onClose}>
      <form onSubmit={handleSubmit} noValidate>
        <div className="form-grid">
          <div className="field">
            <label htmlFor="app-company">Company</label>
            <input {...fieldProps('company')} autoFocus required placeholder="Google" />
            {fieldError('company')}
          </div>

          <div className="field">
            <label htmlFor="app-role">Role</label>
            <input {...fieldProps('role')} required placeholder="Software Engineering Intern" />
            {fieldError('role')}
          </div>

          <div className="field">
            <label htmlFor="app-status">Status</label>
            <select {...fieldProps('status')}>
              {STATUSES.map(({ value, label }) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
            {fieldError('status')}
          </div>

          <div className="field">
            <label htmlFor="app-date_applied">Date applied</label>
            <input {...fieldProps('date_applied')} type="date" required />
            {fieldError('date_applied')}
          </div>

          <div className="field field-full">
            <label htmlFor="app-job_url">
              Job posting URL <span className="optional">Optional</span>
            </label>
            <input {...fieldProps('job_url')} type="url" placeholder="https://careers.example.com/jobs/123" />
            {fieldError('job_url')}
          </div>

          <div className="field field-full">
            <label htmlFor="app-notes">
              Notes <span className="optional">Optional</span>
            </label>
            <textarea {...fieldProps('notes')} rows={3} placeholder="Referral from Sam, recruiter is Alex…" />
            {fieldError('notes')}
          </div>
        </div>

        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}

        <div className="dialog-actions">
          {!isNew && onDelete && (
            <button
              type="button"
              className="text-button text-button-danger dialog-delete"
              onClick={() => onDelete(application)}
            >
              Delete
            </button>
          )}
          <button type="button" className="button button-quiet" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="button" disabled={busy}>
            {busy ? 'Saving…' : isNew ? 'Add application' : 'Save changes'}
          </button>
        </div>
      </form>
    </Dialog>
  )
}
