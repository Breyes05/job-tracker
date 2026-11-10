// Gray placeholders shaped like the real content, shown while the list loads.
// They make the wait (especially Render's cold start) feel shorter than a
// "Loading…" message.
import { STATUSES } from '../statuses.js'

const CARDS_PER_COLUMN = [3, 2, 1, 2]

export function BoardSkeleton() {
  return (
    <div className="board" aria-busy="true" aria-label="Loading applications">
      {STATUSES.map(({ value, label }, index) => (
        <section key={value} className="board-column">
          <header className="board-column-header">
            <span className={`board-dot status-${value}`} aria-hidden="true" />
            <h2>{label}</h2>
          </header>
          <div className="board-cards">
            {Array.from({ length: CARDS_PER_COLUMN[index] }, (_, i) => (
              <div key={i} className="board-card skeleton-card">
                <span className="skeleton skeleton-line" style={{ width: '60%' }} />
                <span className="skeleton skeleton-line skeleton-small" style={{ width: '85%' }} />
                <span className="skeleton skeleton-line skeleton-small" style={{ width: '35%' }} />
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}

export function TableSkeleton() {
  return (
    <div className="skeleton-table" aria-busy="true" aria-label="Loading applications">
      {Array.from({ length: 5 }, (_, i) => (
        <div key={i} className="skeleton-row">
          <span className="skeleton skeleton-line" style={{ width: '18%' }} />
          <span className="skeleton skeleton-line" style={{ width: '26%' }} />
          <span className="skeleton skeleton-pill" />
          <span className="skeleton skeleton-line" style={{ width: '12%' }} />
        </div>
      ))}
    </div>
  )
}
