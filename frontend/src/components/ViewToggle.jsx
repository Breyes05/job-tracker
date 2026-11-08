const VIEWS = [
  { value: 'board', label: 'Board' },
  { value: 'list', label: 'List' },
]

export default function ViewToggle({ view, onChange }) {
  return (
    <div className="status-tabs view-toggle" role="group" aria-label="View">
      {VIEWS.map(({ value, label }) => (
        <button
          key={value}
          type="button"
          className={`status-tab${view === value ? ' is-selected' : ''}`}
          aria-pressed={view === value}
          onClick={() => onChange(value)}
        >
          {label}
        </button>
      ))}
    </div>
  )
}
