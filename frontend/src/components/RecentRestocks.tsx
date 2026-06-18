import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import { eventBadgeColors, formatRelativeTime } from '../lib/eventUtils'
import type { CatalogRestockFeedItem } from '../lib/catalog'

const DEDUPE_WINDOW_MS = 6 * 60 * 60 * 1000 // 6 hours

type FeedEvent = CatalogRestockFeedItem

function dedupeEventsWithinWindow(rows: FeedEvent[]) {
  const kept: FeedEvent[] = []
  const lastKeptAtByKey = new Map<string, number>()

  for (const evt of rows) {
    const key =
      evt.edition_id != null
        ? `edition:${evt.edition_id}`
        : evt.link ?? evt.name ?? 'unknown'
    const t = new Date(evt.event_time).getTime()

    if (!Number.isFinite(t)) {
      kept.push(evt)
      continue
    }

    const lastKeptAt = lastKeptAtByKey.get(key)
    if (
      lastKeptAt !== undefined &&
      lastKeptAt >= t &&
      lastKeptAt - t <= DEDUPE_WINDOW_MS
    ) {
      continue
    }

    kept.push(evt)
    lastKeptAtByKey.set(key, t)
  }

  return kept
}

function formatStoreLine(store: string | null) {
  if (!store) return '—'

  const parts = store.split(' - ')
  if (parts.length >= 2) {
    return `${parts[0]} · ${parts.slice(1).join(' - ')}`
  }

  return store
}

export default function RecentRestocks() {
  const [events, setEvents] = useState<FeedEvent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function fetchEvents() {
      const { data, error } = await supabase
        .from('catalog_restock_feed')
        .select('id, event_type, event_time, item_id, edition_id, name, link, store, price')
        .order('event_time', { ascending: false })
        .limit(20)

      if (cancelled) return

      if (error) {
        console.error('Error fetching recent restocks:', error)
        setEvents([])
        setLoading(false)
        return
      }

      setEvents(dedupeEventsWithinWindow((data ?? []) as FeedEvent[]))
      setLoading(false)
    }

    fetchEvents()

    return () => {
      cancelled = true
    }
  }, [])

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-24 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
        ))}
      </div>
    )
  }

  if (events.length === 0) {
    return (
      <p className="text-sm text-text-muted py-6 text-center">
        No recent restocks yet. Check back soon.
      </p>
    )
  }

  return (
    <div className="space-y-3">
      {events.map((evt) => {
        const badgeClass = eventBadgeColors[evt.event_type] ?? 'bg-gray-100 text-gray-800'
        const storeLine = formatStoreLine(evt.store)
        return (
          <a
            key={evt.id}
            href={evt.link ?? '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="group block rounded-xl bg-surface border border-border shadow-sm p-4 hover:bg-surface-alt transition-colors hover:shadow-md"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <div className="min-w-0 font-medium text-text truncate transition-colors group-hover:text-brand-dark">
                    {evt.name ?? 'Unknown item'}
                  </div>
                  {evt.link ? (
                    <span
                      aria-hidden
                      className="text-brand/80 group-hover:text-brand-dark transition-colors"
                      title="Opens in new tab"
                    >
                      ↗
                    </span>
                  ) : null}
                  <span
                    className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${badgeClass}`}
                  >
                    {evt.event_type}
                  </span>
                </div>
                <div className="mt-2 text-sm text-text-muted">
                  <span className="truncate">
                    {storeLine} <span aria-hidden>&middot;</span>{' '}
                    {evt.price ?? '\u2014'}
                  </span>
                </div>
              </div>
              <div className="text-xs text-text-muted whitespace-nowrap">
                {formatRelativeTime(evt.event_time)}
              </div>
            </div>
          </a>
        )
      })}
    </div>
  )
}
