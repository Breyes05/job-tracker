import { useAuth } from '../auth/AuthContext.js'

// Placeholder for step 1: the list, filters, and form arrive in steps 2 and 3.
export default function ApplicationsPage() {
  const { user, logout } = useAuth()

  return (
    <>
      <header className="app-header">
        <span className="brand">Job Tracker</span>
        <div className="app-header-user">
          <span className="user-email">{user.email}</span>
          <button type="button" className="button button-quiet" onClick={logout}>
            Log out
          </button>
        </div>
      </header>
      <main className="app-main">
        <p className="page-message">You're logged in. Your applications will show up here.</p>
      </main>
    </>
  )
}
