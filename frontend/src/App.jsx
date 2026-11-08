import { BrowserRouter, Navigate, Route, Routes } from 'react-router'
import AuthProvider from './auth/AuthProvider.jsx'
import { HomeRoute, RedirectIfSignedIn } from './components/RouteGuards.jsx'
import SlowServerNotice from './components/SlowServerNotice.jsx'
import ApplicationsPage from './pages/ApplicationsPage.jsx'
import LandingPage from './pages/LandingPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <SlowServerNotice />
        <Routes>
          <Route path="/" element={<HomeRoute app={<ApplicationsPage />} landing={<LandingPage />} />} />
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
