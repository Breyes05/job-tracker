import { createContext, useContext } from 'react'

export const AuthContext = createContext(null)

// Gives any component the current user and the login/register/logout actions.
export function useAuth() {
  const auth = useContext(AuthContext)
  if (!auth) throw new Error('useAuth must be used inside <AuthProvider>')
  return auth
}
