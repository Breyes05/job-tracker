import { Navigate } from 'react-router'
import { useAuth } from '../auth/AuthContext.js'

function CheckingSession() {
  return <p className="page-message">Loading…</p>
}

function ConnectionProblem() {
  const { retry, logout } = useAuth()
  return (
    <div className="page-message">
      <p>Couldn't reach the server. Check your connection and try again.</p>
      <div className="button-row">
        <button type="button" className="button" onClick={retry}>
          Retry
        </button>
        <button type="button" className="button button-quiet" onClick={logout}>
          Log out
        </button>
      </div>
    </div>
  )
}

// Pages that need a logged-in user; everyone else goes to /login.
export function RequireAuth({ children }) {
  const { status } = useAuth()
  if (status === 'checking') return <CheckingSession />
  if (status === 'error') return <ConnectionProblem />
  if (status === 'signed-out') return <Navigate to="/login" replace />
  return children
}

// Login and register pages; logged-in users go straight to their applications.
export function RedirectIfSignedIn({ children }) {
  const { status } = useAuth()
  if (status === 'checking') return <CheckingSession />
  if (status === 'signed-in') return <Navigate to="/" replace />
  return children
}
