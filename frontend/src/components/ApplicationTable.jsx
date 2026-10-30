import { STATUS_LABELS } from '../statuses.js'

// Dates come from the API as "2026-10-24". Formatting them in UTC keeps the
// day from shifting back by one in time zones west of UTC.
const dateFormat = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
  timeZone: 'UTC',
})

function formatDate(isoDate) {
  return dateFormat.format(new Date(`${isoDate}T00:00:00Z`))
}

// A table on wide screens; CSS turns each row into a card on phones.
export default function ApplicationTable({ applications }) {
  return (
    <table className="app-table">
      <thead>
        <tr>
          <th scope="col">Company</th>
          <th scope="col">Role</th>
          <th scope="col">Status</th>
          <th scope="col">Applied</th>
          <th scope="col">Link</th>
          <th scope="col">Notes</th>
        </tr>
      </thead>
      <tbody>
        {applications.map((application) => (
          <tr key={application.id}>
            <td className="cell-company" data-label="Company">
              {application.company}
            </td>
            <td data-label="Role">{application.role}</td>
            <td data-label="Status">
              <span className={`status-badge status-${application.status}`}>
                {STATUS_LABELS[application.status]}
              </span>
            </td>
            <td data-label="Applied" className="cell-date">
              {formatDate(application.date_applied)}
            </td>
            <td data-label="Link">
              {application.job_url ? (
                <a href={application.job_url} target="_blank" rel="noopener noreferrer">
                  Posting
                </a>
              ) : (
                <span className="muted">—</span>
              )}
            </td>
            <td data-label="Notes" className="cell-notes" title={application.notes || undefined}>
              {application.notes || <span className="muted">—</span>}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
