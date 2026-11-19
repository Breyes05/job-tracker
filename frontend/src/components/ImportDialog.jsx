import { useState } from 'react'
import { apiRequest } from '../api.js'
import Dialog from './Dialog.jsx'

const TEMPLATE = 'company,role,status,date_applied,job_url,notes\nAcme Corp,Software Engineering Intern,applied,2026-11-03,https://example.com/jobs/1,Referral from Sam\n'

function downloadTemplate() {
  const url = URL.createObjectURL(new Blob([TEMPLATE], { type: 'text/csv' }))
  const link = document.createElement('a')
  link.href = url
  link.download = 'job-tracker-template.csv'
  link.click()
  URL.revokeObjectURL(url)
}

// Upload a CSV exported from Google Sheets or Excel.
export default function ImportDialog({ onImported, onClose }) {
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  async function handleSubmit(event) {
    event.preventDefault()
    if (!file) return
    setBusy(true)
    setError('')
    try {
      const data = await apiRequest('/applications/import', { method: 'POST', file })
      setResult(data)
      if (data.imported > 0) onImported(data.imported)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const problems = result ? [...result.skipped.map((p) => ({ ...p, kind: 'Skipped' })), ...result.warnings.map((p) => ({ ...p, kind: 'Note' }))].sort((a, b) => a.row - b.row) : []

  return (
    <Dialog title="Import from a spreadsheet" onClose={onClose}>
      {!result ? (
        <form onSubmit={handleSubmit} noValidate>
          <p className="dialog-text">
            Upload a CSV with a header row. <strong>Company</strong> and <strong>Role</strong> are required; Status, Date
            applied, Job URL, and Notes are optional. Common column names like "Position" or "Link" work too. In Google
            Sheets, use File → Download → CSV.
          </p>
          <div className="field">
            <label htmlFor="import-file">CSV file</label>
            <input
              id="import-file"
              type="file"
              accept=".csv,text/csv"
              onChange={(e) => {
                setFile(e.target.files[0] || null)
                setError('')
              }}
            />
          </div>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <div className="dialog-actions">
            <button type="button" className="text-button dialog-delete" onClick={downloadTemplate}>
              Download a template
            </button>
            <button type="button" className="button button-quiet" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="button" disabled={!file || busy}>
              {busy ? 'Importing…' : 'Import'}
            </button>
          </div>
        </form>
      ) : (
        <div>
          <p className="import-summary">
            {result.imported === 0
              ? 'No applications were imported.'
              : `Imported ${result.imported} application${result.imported === 1 ? '' : 's'}.`}
          </p>
          {problems.length > 0 && (
            <ul className="import-problems">
              {problems.map((p) => (
                <li key={`${p.kind}-${p.row}-${p.message}`}>
                  <span className={`import-kind${p.kind === 'Skipped' ? ' is-skipped' : ''}`}>{p.kind}</span> Row {p.row}:{' '}
                  {p.message}
                </li>
              ))}
            </ul>
          )}
          <div className="dialog-actions">
            <button type="button" className="button" onClick={onClose}>
              Done
            </button>
          </div>
        </div>
      )}
    </Dialog>
  )
}
