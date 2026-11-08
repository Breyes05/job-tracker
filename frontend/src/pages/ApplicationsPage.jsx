import { useCallback, useEffect, useState } from 'react'
import { apiRequest } from '../api.js'
import AppHeader from '../components/AppHeader.jsx'
import ApplicationForm from '../components/ApplicationForm.jsx'
import ApplicationTable from '../components/ApplicationTable.jsx'
import ConfirmDelete from '../components/ConfirmDelete.jsx'
import StatusTabs from '../components/StatusTabs.jsx'
import Toast from '../components/Toast.jsx'
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

  // Which dialog is open: the form (null application = adding) or delete confirmation.
  const [formTarget, setFormTarget] = useState(undefined)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [toast, setToast] = useState(null)
  const clearToast = useCallback(() => setToast(null), [])

  useEffect(() => {
    const timer = setTimeout(() => setCompany(searchText.trim()), SEARCH_DELAY_MS)
    return () => clearTimeout(timer)
  }, [searchText])

  // Load the list whenever the search changes or a reload is requested. Status
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

  function reload() {
    setReloadCount((n) => n + 1)
  }

  function updateLocal(id, changes) {
    setResult((current) => ({
      ...current,
      applications: current.applications.map((a) => (a.id === id ? { ...a, ...changes } : a)),
    }))
  }

  // Change the badge right away, then save. If saving fails, put it back.
  async function handleStatusChange(application, status) {
    updateLocal(application.id, { status })
    try {
      const saved = await apiRequest(`/applications/${application.id}`, {
        method: 'PATCH',
        body: { status },
      })
      updateLocal(application.id, saved)
      setToast({ text: `${application.company} moved to ${STATUS_LABELS[status]}.` })
    } catch (error) {
      updateLocal(application.id, { status: application.status })
      setToast({ text: `Couldn't update the status. ${error.message}`, isError: true })
    }
  }

  function handleSaved(saved, isNew) {
    setFormTarget(undefined)
    if (isNew) {
      // Reload so the new application lands in the right place and counts.
      reload()
      setToast({ text: `Added ${saved.company}.` })
    } else {
      updateLocal(saved.id, saved)
      setToast({ text: 'Changes saved.' })
    }
  }

  async function handleDelete() {
    const { id, company: name } = deleteTarget
    await apiRequest(`/applications/${id}`, { method: 'DELETE' })
    setResult((current) => ({
      ...current,
      applications: current.applications.filter((a) => a.id !== id),
    }))
    setDeleteTarget(null)
    setToast({ text: `Deleted ${name}.` })
  }

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
        <button type="button" className="button" onClick={reload}>
          Retry
        </button>
      </div>
    )
  } else if (applications.length === 0 && !company) {
    content = (
      <div className="page-message">
        <p>No applications yet. Add the first one you've applied to.</p>
        <button type="button" className="button" onClick={() => setFormTarget(null)}>
          Add application
        </button>
      </div>
    )
  } else if (visible.length === 0) {
    content = (
      <p className="page-message">
        No {statusFilter === 'all' ? '' : `${STATUS_LABELS[statusFilter].toLowerCase()} `}
        applications{company ? ` matching “${company}”` : ''}.
      </p>
    )
  } else {
    content = (
      <ApplicationTable
        applications={visible}
        onStatusChange={handleStatusChange}
        onEdit={setFormTarget}
        onDelete={setDeleteTarget}
      />
    )
  }

  return (
    <>
      <AppHeader />
      <main className="app-main">
        <div className="page-title-row">
          <h1>Applications</h1>
          <button type="button" className="button" onClick={() => setFormTarget(null)}>
            + Add application
          </button>
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

      {formTarget !== undefined && (
        <ApplicationForm
          application={formTarget}
          onSaved={handleSaved}
          onClose={() => setFormTarget(undefined)}
        />
      )}
      {deleteTarget && (
        <ConfirmDelete
          application={deleteTarget}
          onConfirm={handleDelete}
          onClose={() => setDeleteTarget(null)}
        />
      )}
      <Toast message={toast} onDone={clearToast} />
    </>
  )
}
