import { useEffect, useState } from 'react'
import { apiRequest } from '../api.js'
import AppHeader from '../components/AppHeader.jsx'
import ApplicationTable from '../components/ApplicationTable.jsx'
import StatusTabs from '../components/StatusTabs.jsx'
import { STATUS_LABELS } from '../statuses.js'

const SEARCH_DELAY_MS = 300

export default function ApplicationsPage() {
  // What's typed in the search box, and the value actually sent to the API
  // (updated after the user pauses typing, so we don't send a request per key).
  const [searchText, setSearchText] = useState('')
  const [company, setCompany] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [reloadCount, setReloadCount] = useState(0)

  // The latest response, tagged with the request it answers.
  const requestKey = `${company}|${reloadCount}`
  const [result, setResult] = useState({ key: null, applications: [], error: null })

  useEffect(() => {
    const timer = setTimeout(() => setCompany(searchText.trim()), SEARCH_DELAY_MS)
    return () => clearTimeout(timer)
  }, [searchText])

  // Load the list whenever the search changes or the user clicks Retry. Status
  // filtering happens in the browser so every tab can show its count.
  useEffect(() => {
    let ignore = false
    const params = new URLSearchParams({ limit: '200' })
    if (company) params.set('company', company)

    apiRequest(`/applications?${params}`).then(
      (applications) => {
        if (!ignore) setResult({ key: requestKey, applications, error: null })
      },
      (error) => {
        if (!ignore) setResult({ key: requestKey, applications: [], error })
      },
    )
    // If the search changes before this response arrives, drop the old response.
    return () => {
      ignore = true
    }
  }, [company, requestKey])

  const { applications, error } = result
  const isFirstLoad = result.key === null
  const isRefreshing = !isFirstLoad && result.key !== requestKey
  const visible =
    statusFilter === 'all' ? applications : applications.filter((a) => a.status === statusFilter)

  let content
  if (isFirstLoad) {
    content = <p className="page-message">Loading your applications…</p>
  } else if (error) {
    content = (
      <div className="page-message">
        <p>{error.message}</p>
        <button type="button" className="button" onClick={() => setReloadCount((n) => n + 1)}>
          Retry
        </button>
      </div>
    )
  } else if (applications.length === 0 && !company) {
    content = <p className="page-message">No applications yet. Add the first one you've applied to.</p>
  } else if (visible.length === 0) {
    content = (
      <p className="page-message">
        No {statusFilter === 'all' ? '' : `${STATUS_LABELS[statusFilter].toLowerCase()} `}
        applications{company ? ` matching “${company}”` : ''}.
      </p>
    )
  } else {
    content = <ApplicationTable applications={visible} />
  }

  return (
    <>
      <AppHeader />
      <main className="app-main">
        <div className="page-title-row">
          <h1>Applications</h1>
        </div>

        <div className="toolbar">
          <StatusTabs applications={applications} selected={statusFilter} onSelect={setStatusFilter} />
          <div className="search">
            <label htmlFor="company-search" className="visually-hidden">
              Search by company
            </label>
            <input
              id="company-search"
              type="search"
              placeholder="Search by company"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
          </div>
        </div>

        <div className={isRefreshing ? 'is-refreshing' : undefined}>{content}</div>
      </main>
    </>
  )
}
