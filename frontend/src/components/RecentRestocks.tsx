import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import { eventBadgeColors, formatRelativeTime } from '../lib/eventUtils'

type ItemInfo = {
  name: string
  link: string
  store: string | null
  price: string | null
}

type RestockEvent = {
  id: number
  event_type: string
  event_time: string
  items_seen: ItemInfo | ItemInfo[] | null
}

export default function RecentRestocks() {
  const [events, setEvents] = useState<
    Array<
      Omit<RestockEvent, 'items_seen'> & {
        item: ItemInfo | null
      }
    >
  >([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    async function fetchEvents() {
      const { data, error } = await supabase
        .from('item_events')
        .select(
          'id, event_type, event_time, items_seen!inner(name, link, store, price)',
        )
        .in('event_type', ['Restocked', 'New Item'])
        .order('event_time', { ascending: false })
        .limit(20)

      if (cancelled) return

      if (error) {
        console.error('Error fetching recent restocks:', error)
        setEvents([])
        setLoading(false)
        return
      }

      const normalized = (data ?? []).map((row: RestockEvent) => {
        const item = Array.isArray(row.items_seen) ? row.items_seen[0] ?? null : row.items_seen
        return { id: row.id, event_type: row.event_type, event_time: row.event_time, item }
      })

      setEvents(normalized)
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
        return (
          <a
            key={evt.id}
            href={evt.item?.link ?? '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="block rounded-xl bg-surface border border-border shadow-sm p-4 hover:bg-surface-alt transition-colors"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <div className="font-medium text-text truncate">
                    {evt.item?.name ?? 'Unknown item'}
                  </div>
                  <span
                    className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${badgeClass}`}
                  >
                    {evt.event_type}
                  </span>
                </div>
                <div className="mt-2 text-sm text-text-muted">
                  <div className="truncate">
                    <span className="font-medium text-text-muted">Store: </span>
                    {evt.item?.store ?? '\u2014'}
                  </div>
                  <div className="truncate">
                    <span className="font-medium text-text-muted">Price: </span>
                    {evt.item?.price ?? '\u2014'}
                  </div>
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

