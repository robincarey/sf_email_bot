import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { useAuth } from '../context/AuthContext'
import RecentAlerts from '../components/RecentAlerts'
import WatchlistCard from '../components/WatchlistCard'
import { type CatalogListing } from '../lib/catalog'

interface WatchlistItem {
  id: string
  edition_id: number
  catalog: CatalogListing | null
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
    const { data: rows, error } = await supabase
      .from('watchlist')
      .select('id, edition_id')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false })

    if (error) {
      console.error('Error fetching watchlist:', error)
      setLoadingWatchlist(false)
      return
    }

    const editionIds = (rows ?? []).map((r) => r.edition_id)
    let catalogByEdition = new Map<number, CatalogListing>()
    if (editionIds.length > 0) {
      const { data: catalog, error: catalogError } = await supabase
        .from('catalog_listings')
        .select('edition_id, name, author, link, store, price, in_stock, last_in_stock, isbn, cover_url, open_library_id')
        .in('edition_id', editionIds)

      if (catalogError) {
        console.error('Error fetching catalog listings:', catalogError)
      } else {
        for (const row of catalog ?? []) {
          const editionId = row.edition_id as number
          const existing = catalogByEdition.get(editionId)
          if (!existing || (row.in_stock && !existing.in_stock)) {
            catalogByEdition.set(editionId, row as CatalogListing)
          }
        }
      }
    }

    setWatchlist(
      (rows ?? []).map((row) => ({
        id: row.id,
        edition_id: row.edition_id,
        catalog: catalogByEdition.get(row.edition_id) ?? null,
      })),
    )
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
              to="/app/preferences"
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
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-64 bg-gray-100 dark:bg-gray-800 rounded-xl" />
            ))}
          </div>
        ) : watchlist.length === 0 ? (
          <p className="text-sm text-text-muted py-4 text-center">
            You haven't watched any items yet. Use the &#9733; icon in Recent Alerts to start.
          </p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {watchlist.map((w) => (
              <WatchlistCard
                key={w.id}
                watchlistId={w.id}
                catalog={w.catalog}
                expired={isExpired(w.catalog?.last_in_stock ?? null)}
                onRemove={removeFromWatchlist}
              />
            ))}
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
