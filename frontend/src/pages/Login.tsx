import { useState } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { useAuth } from '../context/AuthContext'

/** Only allow in-app paths so magic-link ?next= is not an open redirect. */
function safeNextParam(raw: string | null): string {
  if (!raw || !raw.startsWith('/') || raw.startsWith('//')) return '/app'
  return raw
}

export default function Login() {
  const { user, loading } = useAuth()
  const location = useLocation()
  const next = safeNextParam(new URLSearchParams(location.search).get('next'))
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin h-8 w-8 rounded-full border-4 border-brand border-t-transparent" />
      </div>
    )
  }

  if (user) {
    return <Navigate to={next} replace />
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)

    // Redirect to /login (not /app) so tokens (?code= or #access_token) are not
    // stripped by ProtectedRoute navigating away before getSession() finishes.
    const redirectUrl = new URL('/login', window.location.origin)
    redirectUrl.searchParams.set('next', next)

    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: redirectUrl.toString() },
    })

    setSubmitting(false)

    if (error) {
      setError(error.message)
    } else {
      setSent(true)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-alt px-4">
      <div className="w-full max-w-sm">
        <div className="rounded-xl bg-surface border border-border shadow-sm p-8">
          <div className="flex flex-col items-center gap-2.5 mb-1">
            <img src="/logo.png" alt="" className="h-32 w-auto" />
            <h1 className="text-xl font-semibold text-text">
              SFF Stock Alerts
            </h1>
          </div>
          <p className="text-sm text-text-muted text-center mb-8">
            Sign in to manage your alert preferences
          </p>

          {sent ? (
            <div className="rounded-lg bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 p-4 text-center">
              <p className="text-sm font-medium text-green-800 dark:text-green-300">
                Check your email
              </p>
              <p className="text-sm text-green-700 dark:text-green-400 mt-1">
                We sent a magic link to <strong>{email}</strong>
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-text mb-1">
                  Email address
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="block w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-muted focus:outline-2 focus:outline-brand"
                />
              </div>

              {error && (
                <p className="text-sm text-red-600">{error}</p>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="w-full rounded-lg bg-brand px-4 py-2.5 text-sm font-medium text-white hover:bg-brand-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                {submitting ? 'Sending...' : 'Send magic link'}
              </button>
            </form>
          )}

          <p className="mt-6 text-center text-xs text-text-muted">
            By continuing, you agree to our{' '}
            <Link to="/terms" className="underline hover:text-text transition-colors">
              Terms of Service
            </Link>
            {' '}
            and{' '}
            <Link to="/privacy" className="underline hover:text-text transition-colors">
              Privacy Policy
            </Link>
            .
          </p>
        </div>
      </div>
    </div>
  )
}
