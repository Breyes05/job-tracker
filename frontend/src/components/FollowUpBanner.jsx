import { useEffect, useState } from 'react'
import { apiRequest } from '../api.js'

const DAY_MS = 24 * 60 * 60 * 1000

function daysSince(isoDate) {
  const applied = new Date(`${isoDate}T00:00:00`)
  return Math.max(0, Math.floor((Date.now() - applied.getTime()) / DAY_MS))
}

// "3 applications haven't heard back in two weeks", with a way to mark each one
// as followed up (which hides it for another two weeks) or open it.
export default function FollowUpBanner({ refreshKey, onOpen, onFollowedUp }) {
  const [items, setItems] = useState([])
  const [expanded, setExpanded] = useState(false)
  const [busyId, setBusyId] = useState(null)

  useEffect(() => {
    let ignore = false
    apiRequest('/applications/follow-ups').then(
      (data) => {
        if (!ignore) setItems(data)
      },
      () => {
        // Reminders are extra; if they fail to load, the board still works.
      },
    )
    return () => {
      ignore = true
    }
  }, [refreshKey])

  async function markFollowedUp(application) {
    setBusyId(application.id)
    try {
      await apiRequest(`/applications/${application.id}/follow-up`, { method: 'POST' })
      setItems((current) => current.filter((a) => a.id !== application.id))
      onFollowedUp(application)
    } catch {
      // Leave it in the list so the user can try again.
    } finally {
      setBusyId(null)
    }
  }

  if (items.length === 0) return null

  return (
    <section className="follow-ups" aria-label="Applications that may need a follow-up">
      <div className="follow-ups-summary">
        <span className="follow-ups-dot" aria-hidden="true" />
        <p>
          <strong>
            {items.length} application{items.length === 1 ? '' : 's'}
          </strong>{' '}
          {items.length === 1 ? "hasn't" : "haven't"} heard back in over two weeks. A short follow-up email can help.
        </p>
        <button type="button" className="text-button" aria-expanded={expanded} onClick={() => setExpanded((e) => !e)}>
          {expanded ? 'Hide' : 'Show'}
        </button>
      </div>

      {expanded && (
        <ul className="follow-ups-list">
          {items.map((application) => (
            <li key={application.id} className="follow-ups-item">
              <div className="follow-ups-info">
                <span className="follow-ups-company">{application.company}</span>
                <span className="follow-ups-meta">
                  {application.role} · applied {daysSince(application.date_applied)} days ago
                </span>
              </div>
              <div className="follow-ups-actions">
                <button type="button" className="text-button" onClick={() => onOpen(application)}>
                  Open
                </button>
                <button
                  type="button"
                  className="button button-quiet"
                  onClick={() => markFollowedUp(application)}
                  disabled={busyId === application.id}
                >
                  {busyId === application.id ? 'Saving…' : 'I followed up'}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
