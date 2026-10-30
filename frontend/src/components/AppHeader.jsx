import { useAuth } from '../auth/AuthContext.js'

export default function AppHeader() {
  const { user, logout } = useAuth()

  return (
    <header className="app-header">
      <span className="brand">Job Tracker</span>
      <div className="app-header-user">
        <span className="user-email">{user.email}</span>
        <button type="button" className="button button-quiet" onClick={logout}>
          Log out
        </button>
      </div>
    </header>
  )
}
