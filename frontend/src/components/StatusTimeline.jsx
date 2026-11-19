import { Fragment, useEffect, useState } from 'react'
import { apiRequest } from '../api.js'
import { STATUS_LABELS } from '../statuses.js'

const DAY_MS = 24 * 60 * 60 * 1000
const dateFormat = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' })

// The API stores times in UTC without a time-zone marker, so add one before parsing.
function parseUtc(timestamp) {
  return new Date(timestamp.endsWith('Z') ? timestamp : `${timestamp}Z`)
}

function daysBetween(earlier, later) {
  const days = Math.round((later - earlier) / DAY_MS)
  if (days <= 0) return 'same day'
  return days === 1 ? '1 day' : `${days} days`
}

// "Applied Oct 1 → 14 days → Interviewing Oct 15", from the application's status history.
export default function StatusTimeline({ applicationId }) {
  const [state, setState] = useState({ events: null, error: null })

  useEffect(() => {
    let ignore = false
    apiRequest(`/applications/${applicationId}/history`).then(
      (events) => {
        if (!ignore) setState({ events, error: null })
      },
      (error) => {
        if (!ignore) setState({ events: null, error })
      },
    )
    return () => {
      ignore = true
    }
  }, [applicationId])

  if (state.error) return null // The history is extra; don't block editing if it fails to load.

  return (
    <section className="timeline" aria-label="Status history">
      <h3 className="timeline-title">History</h3>
      {state.events === null ? (
        <p className="timeline-loading">Loading history…</p>
      ) : (
        <ol className="timeline-list">
          {state.events.map((event, index) => {
            const at = parseUtc(event.changed_at)
            const previous = index > 0 ? parseUtc(state.events[index - 1].changed_at) : null
            return (
              <Fragment key={`${event.changed_at}-${index}`}>
                {previous && (
                  <li className="timeline-gap" aria-label={`${daysBetween(previous, at)} later`}>
                    {daysBetween(previous, at)}
                  </li>
                )}
                <li className="timeline-step">
                  <span className={`status-badge status-${event.to_status}`}>{STATUS_LABELS[event.to_status]}</span>
                  <span className="timeline-date">{dateFormat.format(at)}</span>
                </li>
              </Fragment>
            )
          })}
        </ol>
      )}
    </section>
  )
}
