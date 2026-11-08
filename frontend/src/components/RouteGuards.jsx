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

// The home page: the applications for a logged-in user, the landing page for
// visitors. If a session just expired, go to /login so the message is shown.
export function HomeRoute({ app, landing }) {
  const { status, notice } = useAuth()
  if (status === 'checking') return <CheckingSession />
  if (status === 'error') return <ConnectionProblem />
  if (status === 'signed-out') return notice ? <Navigate to="/login" replace /> : landing
  return app
}

// Login and register pages; logged-in users go straight to their applications.
export function RedirectIfSignedIn({ children }) {
  const { status } = useAuth()
  if (status === 'checking') return <CheckingSession />
  if (status === 'signed-in') return <Navigate to="/" replace />
  return children
}
