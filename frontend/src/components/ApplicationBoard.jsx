import { useState } from 'react'
import { STATUSES } from '../statuses.js'
import StatusSelect from './StatusSelect.jsx'

const shortDate = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' })

function formatDate(isoDate) {
  return shortDate.format(new Date(`${isoDate}T00:00:00Z`))
}

// One column per status. Drag a card to another column to change its status
// (mouse only; the browser's drag and drop doesn't work with touch), or use the
// dropdown on the card, which works everywhere.
export default function ApplicationBoard({ applications, onStatusChange, onEdit }) {
  const [draggingId, setDraggingId] = useState(null)
  const [dropTarget, setDropTarget] = useState(null)

  function handleDrop(event, status) {
    event.preventDefault()
    setDropTarget(null)
    const id = Number(event.dataTransfer.getData('text/plain'))
    const application = applications.find((a) => a.id === id)
    if (application && application.status !== status) onStatusChange(application, status)
  }

  return (
    <div className="board">
      {STATUSES.map(({ value, label }) => {
        const cards = applications.filter((a) => a.status === value)
        return (
          <section
            key={value}
            className={`board-column${dropTarget === value ? ' is-drop-target' : ''}`}
            aria-label={`${label} applications`}
            onDragOver={(event) => {
              event.preventDefault()
              if (dropTarget !== value) setDropTarget(value)
            }}
            onDragLeave={(event) => {
              // Ignore moves between elements inside the same column.
              if (!event.currentTarget.contains(event.relatedTarget)) setDropTarget(null)
            }}
            onDrop={(event) => handleDrop(event, value)}
          >
            <header className="board-column-header">
              <span className={`board-dot status-${value}`} aria-hidden="true" />
              <h2>{label}</h2>
              <span className="board-count">{cards.length}</span>
            </header>

            <div className="board-cards">
              {cards.length === 0 && <p className="board-empty">Drop applications here</p>}
              {cards.map((application) => (
                <article
                  key={application.id}
                  className={`board-card${draggingId === application.id ? ' is-dragging' : ''}`}
                  draggable
                  onDragStart={(event) => {
                    event.dataTransfer.setData('text/plain', String(application.id))
                    event.dataTransfer.effectAllowed = 'move'
                    setDraggingId(application.id)
                  }}
                  onDragEnd={() => {
                    setDraggingId(null)
                    setDropTarget(null)
                  }}
                >
                  {/* The company name is a button that covers the whole card,
                      so clicking anywhere on the card opens it for editing. */}
                  <button type="button" className="board-card-open" onClick={() => onEdit(application)}>
                    {application.company}
                  </button>
                  <p className="board-card-role">{application.role}</p>
                  {application.notes && <p className="board-card-notes">{application.notes}</p>}
                  <div className="board-card-footer">
                    <span className="board-card-date">{formatDate(application.date_applied)}</span>
                    {application.job_url && (
                      <a
                        className="board-card-link"
                        href={application.job_url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Posting
                      </a>
                    )}
                    <span className="board-card-status">
                      <StatusSelect application={application} onChange={onStatusChange} />
                    </span>
                  </div>
                </article>
              ))}
            </div>
          </section>
        )
      })}
    </div>
  )
}
