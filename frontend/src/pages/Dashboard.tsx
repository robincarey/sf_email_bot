import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { useAuth } from '../context/AuthContext'
import RecentAlerts from '../components/RecentAlerts'

export default function Dashboard() {
  const { user } = useAuth()
  const [pauseAll, setPauseAll] = useState(false)
  const [loadingPause, setLoadingPause] = useState(true)

  useEffect(() => {
    if (!user) return
    supabase
      .from('profiles')
      .select('pause_all_alerts')
      .eq('id', user.id)
      .single()
      .then(({ data }) => {
        if (data) setPauseAll(data.pause_all_alerts)
        setLoadingPause(false)
      })
  }, [user])

  const togglePause = async () => {
    const next = !pauseAll
    setPauseAll(next)
    await supabase
      .from('profiles')
      .update({ pause_all_alerts: next })
      .eq('id', user!.id)
  }

  return (
    <div className="space-y-8">
      {/* Quick controls */}
      <div className="rounded-xl bg-surface border border-border p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-text">Alert Status</h2>
            <p className="text-sm text-text-muted mt-0.5">
              {pauseAll
                ? 'All alerts are paused. You won\u2019t receive emails.'
                : 'Alerts are active. You\u2019ll be notified of changes.'}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={togglePause}
              disabled={loadingPause}
              className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand disabled:opacity-50 ${
                !pauseAll ? 'bg-brand' : 'bg-gray-200 dark:bg-gray-600'
              }`}
              role="switch"
              aria-checked={!pauseAll}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow ring-0 transition-transform duration-200 ${
                  !pauseAll ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
            <Link
              to="/preferences"
              className="text-sm text-brand hover:text-brand-dark font-medium"
            >
              All preferences &rarr;
            </Link>
          </div>
        </div>
      </div>

      {/* Recent alerts */}
      <div className="rounded-xl bg-surface border border-border p-6 shadow-sm">
        <h2 className="text-base font-semibold text-text mb-4">Recent Alerts</h2>
        <RecentAlerts />
      </div>
    </div>
  )
}
