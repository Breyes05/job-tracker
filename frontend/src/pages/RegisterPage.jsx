import { Link } from 'react-router'
import { useAuth } from '../auth/AuthContext.js'
import AuthForm from '../components/AuthForm.jsx'

export default function RegisterPage() {
  const { register } = useAuth()

  async function handleRegister(email, password) {
    try {
      await register(email, password)
    } catch (error) {
      if (error.status === 409) error.message = 'An account with this email already exists.'
      throw error
    }
  }

  return (
    <AuthForm
      title="Create your account"
      submitLabel="Create account"
      busyLabel="Creating account…"
      onSubmit={handleRegister}
      passwordHint="At least 8 characters."
      footer={
        <>
          Already have an account? <Link to="/login">Log in</Link>
        </>
      }
    />
  )
}
