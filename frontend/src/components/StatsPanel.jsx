import { useEffect, useState } from 'react'
import { apiRequest } from '../api.js'

const weekFormat = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' })

function percent(value) {
  return value === null ? '—' : `${Math.round(value * 100)}%`
}

function days(value) {
  if (value === null) return '—'
  const rounded = Math.round(value)
  return rounded === 1 ? '1 day' : `${rounded} days`
}

// Summary cards and a weekly activity chart above the board. `refreshKey`
// changes whenever applications are added, edited, moved, or deleted.
export default function StatsPanel({ refreshKey }) {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    let ignore = false
    apiRequest('/stats').then(
      (data) => {
        if (!ignore) setStats(data)
      },
      () => {
        // Stats are extra; if they fail to load, the board still works.
      },
    )
    return () => {
      ignore = true
    }
  }, [refreshKey])

  if (!stats || stats.total === 0) return null

  const busiestWeek = Math.max(1, ...stats.weekly.map((week) => week.count))
  const cards = [
    { label: 'Applications', value: stats.total, detail: null },
    { label: 'Response rate', value: percent(stats.response_rate), detail: `${stats.responded} heard back` },
    { label: 'Interview rate', value: percent(stats.interview_rate), detail: `${stats.interviewed} interviews` },
    { label: 'Offers', value: stats.offers, detail: stats.offers ? percent(stats.offer_rate) : null },
    {
      label: 'Typical response time',
      value: days(stats.median_days_to_response),
      detail: stats.median_days_to_response === null ? 'Shows up after replies' : 'median',
    },
  ]

  return (
    <section className="stats" aria-label="Your job search at a glance">
      <div className="stats-cards">
        {cards.map(({ label, value, detail }) => (
          <div key={label} className="stats-card">
            <span className="stats-label">{label}</span>
            <span className="stats-value">{value}</span>
            {detail && <span className="stats-detail">{detail}</span>}
          </div>
        ))}
      </div>

      <div className="stats-chart">
        <span className="stats-label">Applications per week</span>
        <ol className="stats-bars">
          {stats.weekly.map((week) => (
            <li key={week.week_start} className="stats-bar-item">
              <span className="stats-bar-count">{week.count || ''}</span>
              <span
                className="stats-bar"
                style={{ height: `${(week.count / busiestWeek) * 100}%` }}
                aria-label={`${week.count} applications the week of ${weekFormat.format(new Date(week.week_start))}`}
              />
              <span className="stats-bar-label">{weekFormat.format(new Date(week.week_start))}</span>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}
