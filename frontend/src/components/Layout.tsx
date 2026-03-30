import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

const navItems = [
  { to: '/app', label: 'Dashboard', end: true },
  { to: '/app/items', label: 'Items' },
  { to: '/app/preferences', label: 'Preferences' },
  { to: '/app/contact', label: 'Contact' },
  { to: '/app/account', label: 'Account' },
] as const

function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const next = theme === 'dark' ? 'light' : theme === 'light' ? 'system' : 'dark'
  const icon = theme === 'dark' ? '\u263E' : theme === 'light' ? '\u2600' : '\u25D1'
  const label = theme === 'dark' ? 'Dark' : theme === 'light' ? 'Light' : 'Auto'

  return (
    <button
      onClick={() => setTheme(next)}
      className="flex items-center gap-1 text-sm text-text-muted hover:text-text transition-colors cursor-pointer"
      title={`Theme: ${label}. Click to switch.`}
    >
      <span className="text-base leading-none">{icon}</span>
      <span className="hidden sm:inline">{label}</span>
    </button>
  )
}

export default function Layout({ children }: { children?: React.ReactNode }) {
  const { user, signOut } = useAuth()

  return (
    <div className="min-h-screen bg-surface-alt flex flex-col">
      <header className="bg-surface border-b border-border">
        <div className="mx-auto max-w-5xl px-4 sm:px-6">
          {/* Top row: branding + user controls */}
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-2.5">
              <img src="/logo.png" alt="" className="h-24 w-auto" />
              <span className="text-lg font-semibold text-text tracking-tight">
                SFF Stock Alerts
              </span>
            </div>
            <div className="flex items-center gap-4">
              <ThemeToggle />
              <span className="hidden sm:inline text-sm text-text-muted truncate max-w-48">
                {user?.email}
              </span>
              <button
                onClick={signOut}
                className="text-sm text-text-muted hover:text-text transition-colors cursor-pointer whitespace-nowrap"
              >
                Sign out
              </button>
            </div>
          </div>
          {/* Nav row */}
          <nav className="flex gap-1 pb-2 overflow-x-auto">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={'end' in item ? item.end : false}
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded-md text-sm font-medium whitespace-nowrap transition-colors ${
                    isActive
                      ? 'bg-brand/10 text-brand-dark'
                      : 'text-text-muted hover:text-text hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:px-6">
        {children ?? <Outlet />}
      </main>

      <footer className="border-t border-border bg-surface py-3">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 flex flex-wrap justify-center sm:justify-end gap-x-3 gap-y-1 text-xs text-text-muted">
          <Link to="/terms" className="hover:text-text transition-colors">
            Terms of Service
          </Link>
          <span className="hidden sm:inline" aria-hidden>
            ·
          </span>
          <Link to="/privacy" className="hover:text-text transition-colors">
            Privacy Policy
          </Link>
        </div>
      </footer>
    </div>
  )
}
