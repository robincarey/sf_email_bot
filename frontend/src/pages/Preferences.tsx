import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
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
  const [searchParams] = useSearchParams()
  const [pauseAll, setPauseAll] = useState(false)
  const [receiveAnnouncements, setReceiveAnnouncements] = useState(true)
  const [stores, setStores] = useState<StorePreference[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showUnsubscribeBanner, setShowUnsubscribeBanner] = useState(false)
  const pauseAllRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!user) return

    async function load() {
      const [profileResp, storeResp] = await Promise.all([
        supabase
          .from('profiles')
          .select('pause_all_alerts, receive_announcements')
          .eq('id', user!.id)
          .single(),
        supabase
          .from('user_store_preferences')
          .select('id, store_name, enabled')
          .eq('user_id', user!.id),
      ])

      if (profileResp.data) {
        setPauseAll(profileResp.data.pause_all_alerts)
        setReceiveAnnouncements(profileResp.data.receive_announcements)
      }
      if (storeResp.data) {
        setStores(storeResp.data)
      }
      setLoading(false)
    }

    load()
  }, [user])

  useEffect(() => {
    if (searchParams.get('unsubscribe') !== 'true') return

    setShowUnsubscribeBanner(true)
    const timerId = window.setTimeout(() => {
      pauseAllRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      })
    }, 100)

    return () => window.clearTimeout(timerId)
  }, [searchParams])

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

  const toggleAnnouncements = async () => {
    const next = !receiveAnnouncements
    setReceiveAnnouncements(next)
    setSaving(true)
    await supabase
      .from('profiles')
      .update({ receive_announcements: next })
      .eq('id', user!.id)
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
      {showUnsubscribeBanner && (
        <div className="rounded-xl border border-brand bg-brand/10 p-4 text-sm text-text">
          <div className="flex items-start justify-between gap-3">
            <p>
              You can manage your notification preferences below, or pause all alerts using the toggle at the bottom.
            </p>
            <button
              type="button"
              onClick={() => setShowUnsubscribeBanner(false)}
              className="text-text-muted transition-colors hover:text-text"
              aria-label="Dismiss notification preferences banner"
            >
              ×
            </button>
          </div>
        </div>
      )}
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
      <div
        ref={pauseAllRef}
        className="rounded-xl bg-surface border border-border p-6 shadow-sm"
      >
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

      {/* Announcement emails */}
      <div className="rounded-xl bg-surface border border-border p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-text">Product announcements</h3>
            <p className="text-sm text-text-muted mt-0.5">
              Receive occasional service updates and feature announcements
            </p>
          </div>
          <button
            onClick={toggleAnnouncements}
            className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand ${
              receiveAnnouncements ? 'bg-brand' : 'bg-gray-200 dark:bg-gray-600'
            }`}
            role="switch"
            aria-checked={receiveAnnouncements}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow ring-0 transition-transform duration-200 ${
                receiveAnnouncements ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Per-store toggles */}
      <div className="rounded-xl bg-surface border border-border p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-text mb-2">Store Alerts</h3>
        <p className="text-sm text-text-muted mb-1">
          Choose which stores you want to receive alerts for.
        </p>
        <p className="text-xs text-text-muted mb-4">
          Tip: You can watch individual items from the Dashboard to get alerts for them regardless of store settings.
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
