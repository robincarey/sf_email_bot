import { useEffect, useState, useCallback } from 'react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../context/AuthContext'
import { eventBadgeColors, formatRelativeTime } from '../lib/eventUtils'
import {
  addToWatchlist,
  fetchWatchlistTargets,
  isItemWatched,
  removeFromWatchlist,
  type WatchlistTargets,
} from '../lib/watchlist'
import type { CatalogEvent } from '../lib/catalog'

interface RecentAlertsProps {
  onWatchlistChange?: () => void
}

export default function RecentAlerts({ onWatchlistChange }: RecentAlertsProps) {
  const { user } = useAuth()
  const [events, setEvents] = useState<CatalogEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [watchlistTargets, setWatchlistTargets] = useState<WatchlistTargets>({
    editionIds: new Set(),
  })
  const [togglingId, setTogglingId] = useState<number | null>(null)

  const fetchWatchlist = useCallback(async () => {
    if (!user) return
    setWatchlistTargets(await fetchWatchlistTargets(user.id))
  }, [user])

  useEffect(() => {
    async function fetchEvents() {
      const { data, error } = await supabase
        .from('catalog_events')
        .select('id, item_id, edition_id, event_type, store, event_time, in_stock, old_value, new_value, name, link')
        .order('event_time', { ascending: false })
        .limit(20)

      if (error) {
        console.error('Error fetching events:', error)
        setEvents([])
      } else {
        setEvents((data ?? []) as CatalogEvent[])
      }
      setLoading(false)
    }
    fetchEvents()
    fetchWatchlist()
  }, [fetchWatchlist])

  const toggleWatch = async (editionId: number) => {
    if (!user) return
    setTogglingId(editionId)
    const watched = isItemWatched(editionId, watchlistTargets)

    try {
      if (watched) {
        await removeFromWatchlist(user.id, editionId)
        setWatchlistTargets((prev) => {
          const editionIds = new Set(prev.editionIds)
          editionIds.delete(editionId)
          return { editionIds }
        })
      } else {
        await addToWatchlist(user.id, editionId)
        setWatchlistTargets((prev) => ({
          editionIds: new Set(prev.editionIds).add(editionId),
        }))
      }
    } catch (err) {
      console.error('Error toggling watchlist:', err)
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
            const watched = isItemWatched(evt.edition_id, watchlistTargets)
            return (
            <tr key={evt.id} className="border-b border-border last:border-0">
              <td className="py-3 pr-2">
                <button
                  onClick={() => toggleWatch(evt.edition_id)}
                  disabled={togglingId === evt.edition_id}
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
                {evt.link ? (
                  <a
                    href={evt.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-brand hover:text-brand-dark font-medium hover:underline"
                  >
                    {evt.name ?? 'Unknown item'}
                  </a>
                ) : (
                  <span className="text-text-muted italic">{evt.name ?? 'Unknown item'}</span>
                )}
              </td>
              <td className="py-3 pr-4">
                <span
                  className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${
                    eventBadgeColors[evt.event_type] ?? 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {evt.event_type}
                </span>
                {evt.event_type === 'Price Change' && evt.old_value && evt.new_value && (
                  <span className="block text-xs text-text-muted mt-0.5">
                    <span className="line-through">{evt.old_value}</span>
                    {' \u2192 '}
                    <span className="font-medium text-amber-700 dark:text-amber-400">{evt.new_value}</span>
                  </span>
                )}
              </td>
              <td className="py-3 pr-4 text-text-muted">{evt.store || '\u2014'}</td>
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
