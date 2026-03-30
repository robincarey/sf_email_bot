import { Link } from 'react-router-dom'
import RecentRestocks from '../components/RecentRestocks'

export default function Landing() {
  return (
    <div className="min-h-screen bg-surface-alt flex flex-col">
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 sm:px-6">
        {/* Hero */}
        <section className="py-10 sm:py-14 text-center">
          <div className="flex items-center justify-center gap-3">
            <img src="/logo.png" alt="" className="h-20 w-auto" />
            <h1 className="text-2xl sm:text-3xl font-semibold text-text tracking-tight">
              SFF Stock Alerts
            </h1>
          </div>

          <p className="mt-5 text-base sm:text-lg text-text-muted">
            Get email alerts when special edition sci-fi and fantasy books restock
          </p>

          <div className="mt-7 flex justify-center">
            <Link
              to="/login"
              className="rounded-lg bg-brand px-6 py-3 text-sm font-medium text-white hover:bg-brand-dark transition-colors"
            >
              Sign up for free
            </Link>
          </div>

          <div className="mt-7 max-w-2xl mx-auto text-sm sm:text-base text-text">
            <p className="text-text-muted">
              We monitor The Broken Binding and Folio Society → You choose which stores to
              follow → We email you when something restocks or goes live
            </p>
          </div>
        </section>

        {/* Recent Restocks */}
        <section className="pb-12">
          <h2 className="text-lg sm:text-xl font-semibold text-text mb-4">Recent Restocks</h2>
          <RecentRestocks />
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-surface py-4">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 flex flex-wrap justify-center sm:justify-end gap-x-3 gap-y-1 text-xs text-text-muted">
          <Link to="/privacy" className="hover:text-text transition-colors">
            Privacy Policy
          </Link>
          <span className="hidden sm:inline" aria-hidden>
            ·
          </span>
          <Link to="/terms" className="hover:text-text transition-colors">
            Terms of Service
          </Link>
        </div>
      </footer>
    </div>
  )
}

