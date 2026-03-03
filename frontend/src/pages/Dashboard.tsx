import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { useAuth } from '../context/AuthContext'
import RecentAlerts from '../components/RecentAlerts'

interface WatchlistItem {
  id: string
  item_id: number
  items_seen: {
    name: string
    link: string
    store: string | null
    price: string | null
    in_stock: boolean
    last_in_stock: string | null
  }
}

const EXPIRY_MS = 30 * 24 * 60 * 60 * 1000

function isExpired(lastInStock: string | null): boolean {
  if (!lastInStock) return true
  return Date.now() - new Date(lastInStock).getTime() > EXPIRY_MS
}

export default function Dashboard() {
  const { user } = useAuth()
  const [pauseAll, setPauseAll] = useState(false)
  const [loadingPause, setLoadingPause] = useState(true)
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([])
  const [loadingWatchlist, setLoadingWatchlist] = useState(true)

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

    fetchWatchlist()
  }, [user])

  async function fetchWatchlist() {
    if (!user) return
    const { data, error } = await supabase
      .from('watchlist')
      .select('id, item_id, items_seen!inner(name, link, store, price, in_stock, last_in_stock)')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false })

    if (error) {
      console.error('Error fetching watchlist:', error)
    } else {
      const normalized = (data ?? []).map((row) => {
        const item = Array.isArray(row.items_seen) ? row.items_seen[0] : row.items_seen
        return { ...row, items_seen: item } as unknown as WatchlistItem
      })
      setWatchlist(normalized)
    }
    setLoadingWatchlist(false)
  }

  const togglePause = async () => {
    const next = !pauseAll
    setPauseAll(next)
    await supabase
      .from('profiles')
      .update({ pause_all_alerts: next })
      .eq('id', user!.id)
  }

  const removeFromWatchlist = async (watchlistId: string) => {
    setWatchlist((prev) => prev.filter((w) => w.id !== watchlistId))
    await supabase.from('watchlist').delete().eq('id', watchlistId)
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

      {/* Watchlist */}
      <div className="rounded-xl bg-surface border border-border p-6 shadow-sm">
        <h2 className="text-base font-semibold text-text">Your Watchlist</h2>
        <p className="text-sm text-text-muted mt-0.5 mb-4">
          Track specific items you're interested in. You'll always be notified about changes to watched items, even from stores you've disabled.
        </p>

        {loadingWatchlist ? (
          <div className="animate-pulse space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-10 bg-gray-100 dark:bg-gray-800 rounded" />
            ))}
          </div>
        ) : watchlist.length === 0 ? (
          <p className="text-sm text-text-muted py-4 text-center">
            You haven't watched any items yet. Use the &#9733; icon in Recent Alerts to start.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-text-muted">
                  <th className="pb-2 pr-4 font-medium">Item</th>
                  <th className="pb-2 pr-4 font-medium">Store</th>
                  <th className="pb-2 pr-4 font-medium">Price</th>
                  <th className="pb-2 pr-4 font-medium">Status</th>
                  <th className="pb-2 font-medium w-8"></th>
                </tr>
              </thead>
              <tbody>
                {watchlist.map((w) => {
                  const item = w.items_seen
                  const expired = isExpired(item.last_in_stock)
                  return (
                    <tr key={w.id} className={`border-b border-border last:border-0 ${expired ? 'opacity-50' : ''}`}>
                      <td className="py-3 pr-4">
                        <a
                          href={item.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-brand hover:text-brand-dark font-medium hover:underline"
                        >
                          {item.name}
                        </a>
                      </td>
                      <td className="py-3 pr-4 text-text-muted">{item.store || '\u2014'}</td>
                      <td className="py-3 pr-4 text-text-muted">{item.price || '\u2014'}</td>
                      <td className="py-3 pr-4">
                        {expired ? (
                          <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400">
                            Unavailable
                          </span>
                        ) : item.in_stock ? (
                          <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300">
                            In Stock
                          </span>
                        ) : (
                          <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300">
                            Out of Stock
                          </span>
                        )}
                      </td>
                      <td className="py-3">
                        <button
                          onClick={() => removeFromWatchlist(w.id)}
                          className="text-text-muted hover:text-red-600 dark:hover:text-red-400 transition-colors cursor-pointer"
                          title="Remove from watchlist"
                        >
                          &#10005;
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent alerts */}
      <div className="rounded-xl bg-surface border border-border p-6 shadow-sm">
        <h2 className="text-base font-semibold text-text mb-4">Recent Alerts</h2>
        <RecentAlerts onWatchlistChange={fetchWatchlist} />
      </div>
    </div>
  )
}
