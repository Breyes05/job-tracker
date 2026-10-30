import { Link } from 'react-router'
import { useAuth } from '../auth/AuthContext.js'
import AuthForm from '../components/AuthForm.jsx'

export default function LoginPage() {
  const { login, notice } = useAuth()

  async function handleLogin(email, password) {
    try {
      await login(email, password)
    } catch (error) {
      // The API returns the same 401 for a wrong password and an unknown email.
      if (error.status === 401) error.message = 'Incorrect email or password.'
      throw error
    }
  }

  return (
    <AuthForm
      title="Log in"
      submitLabel="Log in"
      busyLabel="Logging in…"
      onSubmit={handleLogin}
      notice={notice}
      footer={
        <>
          New here? <Link to="/register">Create an account</Link>
        </>
      }
    />
  )
}
