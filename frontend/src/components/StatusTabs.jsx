import { STATUSES } from '../statuses.js'

// "All · Applied · Interviewing · Offer · Rejected", each with a count.
export default function StatusTabs({ applications, selected, onSelect }) {
  const counts = { all: applications.length }
  for (const { value } of STATUSES) counts[value] = 0
  for (const application of applications) counts[application.status] += 1

  const tabs = [{ value: 'all', label: 'All' }, ...STATUSES]

  return (
    <div className="status-tabs" role="group" aria-label="Filter by status">
      {tabs.map(({ value, label }) => (
        <button
          key={value}
          type="button"
          className={`status-tab${selected === value ? ' is-selected' : ''}`}
          aria-pressed={selected === value}
          onClick={() => onSelect(value)}
        >
          {label} <span className="status-tab-count">{counts[value]}</span>
        </button>
      ))}
    </div>
  )
}
