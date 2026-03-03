import { useEffect, useState, useMemo, useCallback } from 'react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../context/AuthContext'

interface Item {
  id: number
  name: string
  price: string | null
  store: string | null
  link: string
  in_stock: boolean
}

type StockFilter = 'all' | 'in_stock'

function usePageSize() {
  const [pageSize, setPageSize] = useState(() =>
    window.innerWidth >= 768 ? 50 : 25,
  )

  useEffect(() => {
    const onResize = () => setPageSize(window.innerWidth >= 768 ? 50 : 25)
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  return pageSize
}

export default function Items() {
  const { user } = useAuth()
  const pageSize = usePageSize()

  const [items, setItems] = useState<Item[]>([])
  const [loading, setLoading] = useState(true)
  const [watchedIds, setWatchedIds] = useState<Set<number>>(new Set())
  const [togglingId, setTogglingId] = useState<number | null>(null)

  const [stockFilter, setStockFilter] = useState<StockFilter>('all')
  const [storeFilter, setStoreFilter] = useState<string>('all')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  useEffect(() => {
    async function fetchItems() {
      const { data, error } = await supabase
        .from('items_seen')
        .select('id, name, price, store, link, in_stock')
        .order('name', { ascending: true })

      if (error) {
        console.error('Error fetching items:', error)
      } else {
        setItems(data ?? [])
      }
      setLoading(false)
    }
    fetchItems()
  }, [])

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
    fetchWatchlist()
  }, [fetchWatchlist])

  const stores = useMemo(() => {
    const set = new Set<string>()
    for (const item of items) {
      if (item.store) set.add(item.store)
    }
    return Array.from(set).sort()
  }, [items])

  const filtered = useMemo(() => {
    let result = items

    if (stockFilter === 'in_stock') {
      result = result.filter((i) => i.in_stock)
    }

    if (storeFilter !== 'all') {
      result = result.filter((i) => i.store === storeFilter)
    }

    const q = search.toLowerCase().trim()
    if (q) {
      result = result.filter((i) => i.name.toLowerCase().includes(q))
    }

    return result
  }, [items, stockFilter, storeFilter, search])

  useEffect(() => {
    setPage(1)
  }, [stockFilter, storeFilter, search])

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))
  const safePageNum = Math.min(page, totalPages)
  const pageItems = filtered.slice(
    (safePageNum - 1) * pageSize,
    safePageNum * pageSize,
  )

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
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div><h2 className="text-lg font-semibold text-text">Items</h2></div>
        <div className="animate-pulse space-y-3">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-10 bg-gray-100 dark:bg-gray-800 rounded" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-text">Items</h2>
        <p className="text-sm text-text-muted mt-1">
          Browse all tracked items. Use the star to add items to your watchlist.
        </p>
      </div>

      {/* Filter bar */}
      <div className="rounded-xl bg-surface border border-border p-4 shadow-sm">
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Stock filter */}
          <div className="flex rounded-lg border border-border overflow-hidden text-sm shrink-0">
            <button
              onClick={() => setStockFilter('all')}
              className={`px-3 py-1.5 cursor-pointer transition-colors ${
                stockFilter === 'all'
                  ? 'bg-brand text-white'
                  : 'bg-surface text-text hover:bg-surface-alt'
              }`}
            >
              All Items
            </button>
            <button
              onClick={() => setStockFilter('in_stock')}
              className={`px-3 py-1.5 cursor-pointer transition-colors ${
                stockFilter === 'in_stock'
                  ? 'bg-brand text-white'
                  : 'bg-surface text-text hover:bg-surface-alt'
              }`}
            >
              In Stock
            </button>
          </div>

          {/* Store filter */}
          <select
            value={storeFilter}
            onChange={(e) => setStoreFilter(e.target.value)}
            className="rounded-lg border border-border bg-surface text-text text-sm px-3 py-1.5 cursor-pointer focus:outline-2 focus:outline-brand"
          >
            <option value="all">All Stores</option>
            {stores.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          {/* Search */}
          <input
            type="text"
            placeholder="Search items..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 rounded-lg border border-border bg-surface text-text text-sm px-3 py-1.5 placeholder:text-text-muted focus:outline-2 focus:outline-brand"
          />
        </div>
      </div>

      {/* Results info */}
      <p className="text-xs text-text-muted">
        Showing {pageItems.length} of {filtered.length} item{filtered.length !== 1 ? 's' : ''}
        {filtered.length !== items.length && ` (${items.length} total)`}
      </p>

      {/* Table */}
      {pageItems.length === 0 ? (
        <div className="rounded-xl bg-surface border border-border p-8 shadow-sm text-center">
          <p className="text-sm text-text-muted">No items match your filters.</p>
        </div>
      ) : (
        <div className="rounded-xl bg-surface border border-border shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-text-muted bg-surface-alt">
                  <th className="py-2 px-3 font-medium w-8"></th>
                  <th className="py-2 px-3 font-medium">Name</th>
                  <th className="py-2 px-3 font-medium">Store</th>
                  <th className="py-2 px-3 font-medium">Price</th>
                  <th className="py-2 px-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {pageItems.map((item) => {
                  const watched = watchedIds.has(item.id)
                  return (
                    <tr key={item.id} className="border-b border-border last:border-0">
                      <td className="py-2.5 px-3">
                        <button
                          onClick={() => toggleWatch(item.id)}
                          disabled={togglingId === item.id}
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
                      <td className="py-2.5 px-3">
                        <a
                          href={item.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-brand hover:text-brand-dark font-medium hover:underline"
                        >
                          {item.name}
                        </a>
                      </td>
                      <td className="py-2.5 px-3 text-text-muted">{item.store || '\u2014'}</td>
                      <td className="py-2.5 px-3 text-text-muted">{item.price || '\u2014'}</td>
                      <td className="py-2.5 px-3">
                        {item.in_stock ? (
                          <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300">
                            In Stock
                          </span>
                        ) : (
                          <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300">
                            Out of Stock
                          </span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-border px-4 py-3">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={safePageNum <= 1}
                className="text-sm text-brand hover:text-brand-dark font-medium disabled:text-text-muted disabled:cursor-not-allowed cursor-pointer"
              >
                &larr; Previous
              </button>
              <span className="text-xs text-text-muted">
                Page {safePageNum} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={safePageNum >= totalPages}
                className="text-sm text-brand hover:text-brand-dark font-medium disabled:text-text-muted disabled:cursor-not-allowed cursor-pointer"
              >
                Next &rarr;
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
