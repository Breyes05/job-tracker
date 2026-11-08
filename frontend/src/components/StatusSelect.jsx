import { STATUSES } from '../statuses.js'

// A status badge that's also a dropdown: pick a new status and it saves.
export default function StatusSelect({ application, onChange }) {
  return (
    <select
      className={`status-select status-${application.status}`}
      value={application.status}
      onChange={(e) => onChange(application, e.target.value)}
      aria-label={`Status for ${application.company}`}
    >
      {STATUSES.map(({ value, label }) => (
        <option key={value} value={value}>
          {label}
        </option>
      ))}
    </select>
  )
}
