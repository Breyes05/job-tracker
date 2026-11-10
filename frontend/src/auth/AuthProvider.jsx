import { useCallback, useEffect, useMemo, useState } from 'react'
import { apiRequest, clearToken, getToken, onUnauthorized, setToken } from '../api.js'
import { AuthContext } from './AuthContext.js'

// status: 'checking' (looking up a saved token), 'error' (couldn't reach the API),
// 'signed-in', or 'signed-out'.
export default function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState(() => (getToken() ? 'checking' : 'signed-out'))
  const [notice, setNotice] = useState('')

  // Ask the API who the saved token belongs to. A 401 means the token is no
  // longer valid; anything else means the server couldn't be reached, so keep
  // the token and offer a retry.
  const loadUser = useCallback(
    () =>
      apiRequest('/auth/me').then(
        (me) => {
          setUser(me)
          setStatus('signed-in')
        },
        (error) => setStatus(error.status === 401 ? 'signed-out' : 'error'),
      ),
    [],
  )

  // On first load, check whether a saved token still works.
  useEffect(() => {
    if (!getToken()) return
    apiRequest('/auth/me').then(
      (me) => {
        setUser(me)
        setStatus('signed-in')
      },
      (error) => setStatus(error.status === 401 ? 'signed-out' : 'error'),
    )
  }, [])

  // Any request that comes back 401 signs the user out.
  useEffect(() => {
    onUnauthorized(() => {
      setUser(null)
      setStatus('signed-out')
      setNotice('Your session expired. Log in again.')
    })
  }, [])

  const login = useCallback(async (email, password) => {
    const { access_token } = await apiRequest('/auth/login', {
      method: 'POST',
      form: { username: email, password },
      auth: false,
    })
    setToken(access_token)
    setNotice('')
    setUser(await apiRequest('/auth/me'))
    setStatus('signed-in')
  }, [])

  const register = useCallback(
    async (email, password) => {
      await apiRequest('/auth/register', {
        method: 'POST',
        body: { email, password },
        auth: false,
      })
      await login(email, password)
    },
    [login],
  )

  const logout = useCallback(() => {
    clearToken()
    setUser(null)
    setStatus('signed-out')
    setNotice('')
  }, [])

  const retry = useCallback(() => {
    setStatus('checking')
    loadUser()
  }, [loadUser])

  const value = useMemo(
    () => ({ user, status, notice, login, register, logout, retry }),
    [user, status, notice, login, register, logout, retry],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
