import { useState } from 'react'
import { useAuth } from '../auth/AuthContext.js'
import AccountDialog from './AccountDialog.jsx'

export default function AppHeader() {
  const { user, logout } = useAuth()
  const [showAccount, setShowAccount] = useState(false)

  return (
    <header className="app-header">
      <span className="brand">Job Tracker</span>
      <div className="app-header-user">
        <span className="user-email">{user.email}</span>
        <button type="button" className="button button-quiet" onClick={() => setShowAccount(true)}>
          Account
        </button>
        <button type="button" className="button button-quiet" onClick={logout}>
          Log out
        </button>
      </div>
      {showAccount && <AccountDialog onClose={() => setShowAccount(false)} />}
    </header>
  )
}
