import { useEffect, useState, useCallback } from 'react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../context/AuthContext'

interface ItemInfo {
  name: string
  link: string
  store: string | null
}

interface AlertEvent {
  id: number
  item_id: number
  event_type: string
  store: string
  event_time: string
  in_stock: boolean
  old_value: string | null
  new_value: string | null
  items_seen: ItemInfo | ItemInfo[] | null
}

const eventBadgeColors: Record<string, string> = {
  'New Item': 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
  'Restocked': 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
  'Price Change': 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
  'Store Change': 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300',
  'Out of Stock': 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300',
  'New Item - Out of Stock': 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
}

interface RecentAlertsProps {
  onWatchlistChange?: () => void
}

export default function RecentAlerts({ onWatchlistChange }: RecentAlertsProps) {
  const { user } = useAuth()
  const [events, setEvents] = useState<AlertEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [watchedIds, setWatchedIds] = useState<Set<number>>(new Set())
  const [togglingId, setTogglingId] = useState<number | null>(null)

  const fetchWatchlist = useCallback(async () => {
    if (!user) return
    const { data } = await supabase
      .from('watchlist')
      .select('item_id')
      .eq('user_id', user.id)
    if (data) {
      setWatchedIds(new Set(data.map((r) => r.item_id)))
    }
  }, [user])

  useEffect(() => {
    async function fetchEvents() {
      const { data, error } = await supabase
        .from('item_events')
        .select('id, item_id, event_type, store, event_time, in_stock, old_value, new_value, items_seen!inner(name, link, store)')
        .order('event_time', { ascending: false })
        .limit(20)

      if (error) {
        console.error('Error fetching events:', error)
      } else {
        const normalized = (data ?? []).map((row) => {
          const item = Array.isArray(row.items_seen)
            ? row.items_seen[0] ?? null
            : row.items_seen
          return { ...row, items_seen: item } as AlertEvent
        })
        setEvents(normalized)
      }
      setLoading(false)
    }
    fetchEvents()
    fetchWatchlist()
  }, [fetchWatchlist])

  const toggleWatch = async (itemId: number) => {
    if (!user) return
    setTogglingId(itemId)

    if (watchedIds.has(itemId)) {
      await supabase
        .from('watchlist')
        .delete()
        .eq('user_id', user.id)
        .eq('item_id', itemId)
      setWatchedIds((prev) => {
        const next = new Set(prev)
        next.delete(itemId)
        return next
      })
    } else {
      await supabase
        .from('watchlist')
        .insert({ user_id: user.id, item_id: itemId })
      setWatchedIds((prev) => new Set(prev).add(itemId))
    }

    setTogglingId(null)
    onWatchlistChange?.()
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-12 bg-gray-100 dark:bg-gray-800 rounded" />
        ))}
      </div>
    )
  }

  if (events.length === 0) {
    return (
      <p className="text-sm text-text-muted py-6 text-center">
        No recent alerts yet. Events will appear here when items change.
      </p>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-text-muted">
            <th className="pb-2 pr-2 font-medium w-8"></th>
            <th className="pb-2 pr-4 font-medium">Item</th>
            <th className="pb-2 pr-4 font-medium">Event</th>
            <th className="pb-2 pr-4 font-medium">Store</th>
            <th className="pb-2 font-medium">When</th>
          </tr>
        </thead>
        <tbody>
          {events.map((evt) => {
            const item = Array.isArray(evt.items_seen) ? evt.items_seen[0] : evt.items_seen
            const watched = watchedIds.has(evt.item_id)
            return (
            <tr key={evt.id} className="border-b border-border last:border-0">
              <td className="py-3 pr-2">
                <button
                  onClick={() => toggleWatch(evt.item_id)}
                  disabled={togglingId === evt.item_id}
                  className="text-lg leading-none cursor-pointer disabled:opacity-50 hover:scale-110 transition-transform"
                  title={watched ? 'Remove from watchlist' : 'Add to watchlist'}
                >
                  {watched ? (
                    <span className="text-brand">&#9733;</span>
                  ) : (
                    <span className="text-text-muted">&#9734;</span>
                  )}
                </button>
              </td>
              <td className="py-3 pr-4">
                {item ? (
                  <a
                    href={item.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-brand hover:text-brand-dark font-medium hover:underline"
                  >
                    {item.name}
                  </a>
                ) : (
                  <span className="text-text-muted italic">Unknown item</span>
                )}
              </td>
              <td className="py-3 pr-4">
                <span
                  className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                    eventBadgeColors[evt.event_type] ?? 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {evt.event_type}
                </span>
              </td>
              <td className="py-3 pr-4 text-text-muted">{evt.store || item?.store || '\u2014'}</td>
              <td className="py-3 text-text-muted whitespace-nowrap">
                {formatRelativeTime(evt.event_time)}
              </td>
            </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const minutes = Math.floor(diff / 60_000)
  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days}d ago`
  return new Date(iso).toLocaleDateString()
}
