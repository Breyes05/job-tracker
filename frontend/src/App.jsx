import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import AuthProvider from './auth/AuthProvider.jsx'
import { RedirectIfSignedIn, RequireAuth } from './components/RouteGuards.jsx'
import SlowServerNotice from './components/SlowServerNotice.jsx'
import ApplicationsPage from './pages/ApplicationsPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <SlowServerNotice />
        <Routes>
          <Route
            path="/"
            element={
              <RequireAuth>
                <ApplicationsPage />
              </RequireAuth>
            }
          />
          <Route
            path="/login"
            element={
              <RedirectIfSignedIn>
                <LoginPage />
              </RedirectIfSignedIn>
            }
          />
          <Route
            path="/register"
            element={
              <RedirectIfSignedIn>
                <RegisterPage />
              </RedirectIfSignedIn>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
