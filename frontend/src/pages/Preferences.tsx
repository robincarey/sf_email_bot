import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../context/AuthContext'
import StoreToggle from '../components/StoreToggle'

interface StorePreference {
  id: string
  store_name: string
  enabled: boolean
}

export default function Preferences() {
  const { user } = useAuth()
  const [pauseAll, setPauseAll] = useState(false)
  const [stores, setStores] = useState<StorePreference[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!user) return

    async function load() {
      const [profileResp, storeResp] = await Promise.all([
        supabase
          .from('profiles')
          .select('pause_all_alerts')
          .eq('id', user!.id)
          .single(),
        supabase
          .from('user_store_preferences')
          .select('id, store_name, enabled')
          .eq('user_id', user!.id),
      ])

      if (profileResp.data) {
        setPauseAll(profileResp.data.pause_all_alerts)
      }
      if (storeResp.data) {
        setStores(storeResp.data)
      }
      setLoading(false)
    }

    load()
  }, [user])

  const togglePauseAll = async () => {
    const next = !pauseAll
    setPauseAll(next)
    setSaving(true)
    await supabase
      .from('profiles')
      .update({ pause_all_alerts: next })
      .eq('id', user!.id)
    setSaving(false)
  }

  const toggleStore = async (id: string, enabled: boolean) => {
    setStores((prev) =>
      prev.map((s) => (s.id === id ? { ...s, enabled } : s)),
    )
    setSaving(true)
    await supabase
      .from('user_store_preferences')
      .update({ enabled })
      .eq('id', id)
    setSaving(false)
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-20 bg-gray-100 dark:bg-gray-800 rounded-xl" />
        <div className="h-40 bg-gray-100 dark:bg-gray-800 rounded-xl" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-text">Preferences</h2>
        <p className="text-sm text-text-muted mt-1">
          Control which alerts you receive.
          {saving && (
            <span className="ml-2 text-brand">Saving...</span>
          )}
        </p>
      </div>

      {/* Pause all */}
      <div className="rounded-xl bg-surface border border-border p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-text">Pause all alerts</h3>
            <p className="text-sm text-text-muted mt-0.5">
              Temporarily stop all email notifications
            </p>
          </div>
          <button
            onClick={togglePauseAll}
            className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand ${
              pauseAll ? 'bg-brand' : 'bg-gray-200 dark:bg-gray-600'
            }`}
            role="switch"
            aria-checked={pauseAll}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow ring-0 transition-transform duration-200 ${
                pauseAll ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Per-store toggles */}
      <div className="rounded-xl bg-surface border border-border p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-text mb-2">Store Alerts</h3>
        <p className="text-sm text-text-muted mb-4">
          Choose which stores you want to receive alerts for.
        </p>
        <div className="divide-y divide-border">
          {stores.map((s) => (
            <StoreToggle
              key={s.id}
              storeName={s.store_name}
              enabled={s.enabled}
              onToggle={(enabled) => toggleStore(s.id, enabled)}
              disabled={pauseAll}
            />
          ))}
        </div>
        {pauseAll && (
          <p className="text-xs text-text-muted mt-3">
            Store toggles are disabled while all alerts are paused.
          </p>
        )}
      </div>
    </div>
  )
}
