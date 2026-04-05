import { useEffect, useMemo, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { supabase } from '../lib/supabase'
import { useTheme } from '../context/ThemeContext'
import { formatRelativeTime } from '../lib/eventUtils'

type LeaderboardRow = {
  item_id: number
  restock_count: number
  name: string | null
  store: string | null
  link: string | null
}

type VolumeRow = {
  day: string
  event_type: string
  event_count: number
}

type StoreRow = {
  store: string
  event_count: number
}

type PriceDropRow = {
  event_id: number
  item_id: number
  old_value: string | null
  new_value: string | null
  old_num: string | number | null
  new_num: string | number | null
  price_drop: string | number | null
  name: string | null
  store: string | null
  link: string | null
}

type RecentRestockRow = {
  id: number
  event_time: string
  items_seen: { name: string; link: string; store: string | null } | { name: string; link: string; store: string | null }[] | null
}

/**
 * Days (UTC YYYY-MM-DD) omitted from the event-volume chart (e.g. initial DB load).
 * Set VITE_ANALYTICS_VOLUME_EXCLUDE_DAYS to a comma-separated list, or "" to exclude none.
 * When unset, defaults to 2026-03-03.
 */
function volumeChartExcludedDays(): Set<string> {
  const raw = import.meta.env.VITE_ANALYTICS_VOLUME_EXCLUDE_DAYS as string | undefined
  if (raw === '') return new Set()
  const csv = (raw?.trim() || '2026-03-03').split(',')
  return new Set(csv.map((s) => s.trim()).filter(Boolean))
}

const CHART_COLORS: Record<string, string> = {
  'New Item': '#16a34a',
  Restocked: '#2563eb',
  'Price Change': '#d97706',
  'Store Change': '#9333ea',
  'Out of Stock': '#dc2626',
  'New Item - Out of Stock': '#57534e',
  'Unknown Change': '#78716c',
}

function chartColor(eventType: string): string {
  return CHART_COLORS[eventType] ?? '#78716c'
}

function formatStoreLine(store: string | null) {
  if (!store) return '—'
  const parts = store.split(' - ')
  if (parts.length >= 2) {
    return `${parts[0]} · ${parts.slice(1).join(' - ')}`
  }
  return store
}

function formatDayLabel(isoDate: string): string {
  const d = new Date(isoDate.includes('T') ? isoDate : `${isoDate}T12:00:00Z`)
  if (!Number.isFinite(d.getTime())) return isoDate
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

function pivotVolumeForChart(rows: VolumeRow[]) {
  const types = new Set<string>()
  const byDay = new Map<string, Record<string, number>>()

  for (const r of rows) {
    types.add(r.event_type)
    const rawDay = typeof r.day === 'string' ? r.day.split('T')[0] : String(r.day)
    if (!byDay.has(rawDay)) byDay.set(rawDay, {})
    const bucket = byDay.get(rawDay)!
    bucket[r.event_type] = Number(r.event_count)
  }

  const sortedDays = [...byDay.keys()].sort()
  const typeList = [...types].sort()

  const data = sortedDays.map((rawDay) => {
    const row: Record<string, string | number> = {
      dayKey: rawDay,
      dayLabel: formatDayLabel(rawDay),
    }
    const counts = byDay.get(rawDay)!
    for (const t of typeList) {
      row[t] = counts[t] ?? 0
    }
    return row
  })

  return { data, typeList }
}

function SectionSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-10 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
      ))}
    </div>
  )
}

function EmptyBlock({ message }: { message: string }) {
  return <p className="text-sm text-text-muted py-6 text-center">{message}</p>
}

export default function Analytics() {
  const { resolved } = useTheme()
  const axisColor = resolved === 'dark' ? '#a8a29e' : '#78716c'
  const gridColor = resolved === 'dark' ? '#44403c' : '#d6d3d1'

  const [leaderboard, setLeaderboard] = useState<LeaderboardRow[]>([])
  const [leaderboardLoading, setLeaderboardLoading] = useState(true)
  const [leaderboardError, setLeaderboardError] = useState<string | null>(null)

  const [recent, setRecent] = useState<
    { id: number; event_time: string; name: string; link: string; store: string | null }[]
  >([])
  const [recentLoading, setRecentLoading] = useState(true)
  const [recentError, setRecentError] = useState<string | null>(null)

  const [priceDrops, setPriceDrops] = useState<PriceDropRow[]>([])
  const [priceLoading, setPriceLoading] = useState(true)
  const [priceError, setPriceError] = useState<string | null>(null)

  const [volume, setVolume] = useState<VolumeRow[]>([])
  const [volumeLoading, setVolumeLoading] = useState(true)
  const [volumeError, setVolumeError] = useState<string | null>(null)

  const [stores, setStores] = useState<StoreRow[]>([])
  const [storesLoading, setStoresLoading] = useState(true)
  const [storesError, setStoresError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    ;(async () => {
      const { data, error } = await supabase.from('analytics_restock_leaderboard').select('*')
      if (cancelled) return
      if (error) {
        console.error('analytics_restock_leaderboard', error)
        setLeaderboardError(error.message)
        setLeaderboard([])
      } else {
        setLeaderboard((data ?? []) as LeaderboardRow[])
      }
      setLeaderboardLoading(false)
    })()

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    ;(async () => {
      const { data, error } = await supabase
        .from('item_events')
        .select('id, event_time, items_seen!inner(name, link, store)')
        .eq('event_type', 'Restocked')
        .order('event_time', { ascending: false })
        .limit(10)

      if (cancelled) return
      if (error) {
        console.error('recent restocks', error)
        setRecentError(error.message)
        setRecent([])
      } else {
        const normalized = (data ?? []).map((row: RecentRestockRow) => {
          const item = Array.isArray(row.items_seen) ? row.items_seen[0] ?? null : row.items_seen
          return {
            id: row.id,
            event_time: row.event_time,
            name: item?.name ?? 'Unknown item',
            link: item?.link ?? '#',
            store: item?.store ?? null,
          }
        })
        setRecent(normalized)
      }
      setRecentLoading(false)
    })()

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    ;(async () => {
      const { data, error } = await supabase.from('analytics_top_price_drops').select('*')
      if (cancelled) return
      if (error) {
        console.error('analytics_top_price_drops', error)
        setPriceError(error.message)
        setPriceDrops([])
      } else {
        setPriceDrops((data ?? []) as PriceDropRow[])
      }
      setPriceLoading(false)
    })()

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    ;(async () => {
      const { data, error } = await supabase.from('analytics_event_volume_daily').select('*')
      if (cancelled) return
      if (error) {
        console.error('analytics_event_volume_daily', error)
        setVolumeError(error.message)
        setVolume([])
      } else {
        const rows = (data ?? []).map((r: { day: string; event_type: string; event_count: number }) => ({
          day: typeof r.day === 'string' ? r.day.split('T')[0] : String(r.day),
          event_type: r.event_type,
          event_count: Number(r.event_count),
        }))
        setVolume(rows)
      }
      setVolumeLoading(false)
    })()

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    ;(async () => {
      const { data, error } = await supabase.from('analytics_store_event_totals').select('*')
      if (cancelled) return
      if (error) {
        console.error('analytics_store_event_totals', error)
        setStoresError(error.message)
        setStores([])
      } else {
        setStores(
          (data ?? []).map((r: { store: string; event_count: number }) => ({
            store: r.store,
            event_count: Number(r.event_count),
          })),
        )
      }
      setStoresLoading(false)
    })()

    return () => {
      cancelled = true
    }
  }, [])

  const { data: chartData, typeList: eventTypes } = useMemo(() => {
    const skip = volumeChartExcludedDays()
    const rows = skip.size === 0 ? volume : volume.filter((r) => !skip.has(r.day))
    return pivotVolumeForChart(rows)
  }, [volume])

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-2xl font-semibold text-text tracking-tight">Analytics</h1>
        <p className="mt-1 text-sm text-text-muted">
          Aggregated activity from item events across the catalog.
        </p>
      </div>

      <section className="rounded-xl bg-surface border border-border shadow-sm p-5 sm:p-6">
        <h2 className="text-lg font-medium text-text mb-4">Most restocked items</h2>
        {leaderboardLoading ? (
          <SectionSkeleton rows={5} />
        ) : leaderboardError ? (
          <p className="text-sm text-red-600 dark:text-red-400 py-4">{leaderboardError}</p>
        ) : leaderboard.length === 0 ? (
          <EmptyBlock message="No restock data yet." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-text">
              <thead>
                <tr className="border-b border-border text-left text-text-muted">
                  <th className="pb-2 pr-4 font-medium">Item</th>
                  <th className="pb-2 pr-4 font-medium">Store</th>
                  <th className="pb-2 text-right font-medium w-24">Restocks</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((row) => (
                  <tr key={row.item_id} className="border-b border-border/60 last:border-0">
                    <td className="py-2.5 pr-4">
                      {row.link ? (
                        <a
                          href={row.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-brand-dark dark:text-brand hover:underline font-medium"
                        >
                          {row.name ?? 'Unknown'}
                        </a>
                      ) : (
                        <span className="font-medium">{row.name ?? 'Unknown'}</span>
                      )}
                    </td>
                    <td className="py-2.5 pr-4 text-text-muted">{formatStoreLine(row.store)}</td>
                    <td className="py-2.5 text-right tabular-nums font-medium text-text">
                      {row.restock_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="rounded-xl bg-surface border border-border shadow-sm p-5 sm:p-6">
        <h2 className="text-lg font-medium text-text mb-4">Most recent restocks</h2>
        {recentLoading ? (
          <SectionSkeleton rows={5} />
        ) : recentError ? (
          <p className="text-sm text-red-600 dark:text-red-400 py-4">{recentError}</p>
        ) : recent.length === 0 ? (
          <EmptyBlock message="No recent restocks." />
        ) : (
          <ul className="space-y-3">
            {recent.map((r) => (
              <li key={r.id}>
                <a
                  href={r.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-start justify-between gap-4 rounded-lg border border-border bg-surface-alt/50 hover:bg-surface-alt px-4 py-3 transition-colors group"
                >
                  <div className="min-w-0">
                    <div className="font-medium text-text group-hover:text-brand-dark truncate">
                      {r.name}
                      {r.link !== '#' ? (
                        <span className="ml-1 text-brand/80" aria-hidden>
                          ↗
                        </span>
                      ) : null}
                    </div>
                    <div className="text-sm text-text-muted mt-0.5">{formatStoreLine(r.store)}</div>
                  </div>
                  <span className="text-xs text-text-muted whitespace-nowrap shrink-0">
                    {formatRelativeTime(r.event_time)}
                  </span>
                </a>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded-xl bg-surface border border-border shadow-sm p-5 sm:p-6">
        <h2 className="text-lg font-medium text-text mb-4">Biggest price drops</h2>
        {priceLoading ? (
          <SectionSkeleton rows={5} />
        ) : priceError ? (
          <p className="text-sm text-red-600 dark:text-red-400 py-4">{priceError}</p>
        ) : priceDrops.length === 0 ? (
          <EmptyBlock message="No price decrease events found." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-text">
              <thead>
                <tr className="border-b border-border text-left text-text-muted">
                  <th className="pb-2 pr-4 font-medium">Item</th>
                  <th className="pb-2 pr-4 font-medium">Store</th>
                  <th className="pb-2 pr-4 font-medium">Was → Now</th>
                  <th className="pb-2 text-right font-medium">Drop</th>
                </tr>
              </thead>
              <tbody>
                {priceDrops.map((row) => {
                  const drop = Number(row.price_drop)
                  const dropLabel = Number.isFinite(drop) ? drop.toFixed(2) : '—'
                  return (
                    <tr key={row.event_id} className="border-b border-border/60 last:border-0">
                      <td className="py-2.5 pr-4">
                        {row.link ? (
                          <a
                            href={row.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-brand-dark dark:text-brand hover:underline font-medium"
                          >
                            {row.name ?? 'Unknown'}
                          </a>
                        ) : (
                          <span className="font-medium">{row.name ?? 'Unknown'}</span>
                        )}
                      </td>
                      <td className="py-2.5 pr-4 text-text-muted">{formatStoreLine(row.store)}</td>
                      <td className="py-2.5 pr-4 text-text-muted">
                        <span className="line-through opacity-70">{row.old_value ?? '—'}</span>
                        <span className="mx-1" aria-hidden>
                          →
                        </span>
                        <span className="text-text font-medium">{row.new_value ?? '—'}</span>
                      </td>
                      <td className="py-2.5 text-right tabular-nums font-medium text-amber-800 dark:text-amber-300">
                        {dropLabel}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="rounded-xl bg-surface border border-border shadow-sm p-5 sm:p-6">
        <h2 className="text-lg font-medium text-text mb-4">Event volume over time</h2>
        {volumeLoading ? (
          <div className="h-80 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
        ) : volumeError ? (
          <p className="text-sm text-red-600 dark:text-red-400 py-4">{volumeError}</p>
        ) : chartData.length === 0 ? (
          <EmptyBlock message="No events to chart yet." />
        ) : (
          <div className="h-80 w-full min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
                <XAxis dataKey="dayLabel" tick={{ fill: axisColor, fontSize: 11 }} tickMargin={8} />
                <YAxis
                  tick={{ fill: axisColor, fontSize: 11 }}
                  tickMargin={8}
                  allowDecimals={false}
                  width={40}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: resolved === 'dark' ? '#292524' : '#ffffff',
                    border: `1px solid ${gridColor}`,
                    borderRadius: 8,
                    color: resolved === 'dark' ? '#fafaf9' : '#1c1917',
                  }}
                  labelStyle={{ color: axisColor }}
                  itemStyle={{ color: resolved === 'dark' ? '#fafaf9' : '#1c1917' }}
                  formatter={(value: number | string, name: string) => [value, name]}
                  labelFormatter={(label) => String(label)}
                />
                <Legend wrapperStyle={{ fontSize: 12, color: axisColor }} />
                {eventTypes.map((t: string) => (
                  <Bar key={t} dataKey={t} stackId="vol" fill={chartColor(t)} name={t} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>

      <section className="rounded-xl bg-surface border border-border shadow-sm p-5 sm:p-6">
        <h2 className="text-lg font-medium text-text mb-4">Store breakdown</h2>
        {storesLoading ? (
          <SectionSkeleton rows={5} />
        ) : storesError ? (
          <p className="text-sm text-red-600 dark:text-red-400 py-4">{storesError}</p>
        ) : stores.length === 0 ? (
          <EmptyBlock message="No events by store." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-text">
              <thead>
                <tr className="border-b border-border text-left text-text-muted">
                  <th className="pb-2 pr-4 font-medium">Store</th>
                  <th className="pb-2 text-right font-medium">Events</th>
                </tr>
              </thead>
              <tbody>
                {stores.map((row) => (
                  <tr key={row.store} className="border-b border-border/60 last:border-0">
                    <td className="py-2.5 pr-4">{formatStoreLine(row.store)}</td>
                    <td className="py-2.5 text-right tabular-nums font-medium text-text">
                      {row.event_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
