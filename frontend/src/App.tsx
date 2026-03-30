import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { Analytics } from '@vercel/analytics/react'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Preferences from './pages/Preferences'
import Account from './pages/Account'
import Contact from './pages/Contact'
import Items from './pages/Items'
import Privacy from './pages/Privacy'
import Terms from './pages/Terms'

function RedirectWithSearch({ to }: { to: string }) {
  const { search } = useLocation()
  return <Navigate to={`${to}${search}`} replace />
}

/** Preserves hash/query so Supabase magic-link tokens on `/` are not stripped when sending users to `/app`. */
function RootToApp() {
  const { search, hash } = useLocation()
  return (
    <Navigate
      to={{ pathname: '/app', search, hash }}
      replace
    />
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route path="/terms" element={<Terms />} />
            <Route path="/items" element={<RedirectWithSearch to="/app/items" />} />
            <Route path="/preferences" element={<RedirectWithSearch to="/app/preferences" />} />
            <Route path="/contact" element={<RedirectWithSearch to="/app/contact" />} />
            <Route path="/account" element={<RedirectWithSearch to="/app/account" />} />
            <Route
              path="/app"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="items" element={<Items />} />
              <Route path="preferences" element={<Preferences />} />
              <Route path="contact" element={<Contact />} />
              <Route path="account" element={<Account />} />
            </Route>
            <Route path="/" element={<RootToApp />} />
          </Routes>
          <Analytics />
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  )
}
