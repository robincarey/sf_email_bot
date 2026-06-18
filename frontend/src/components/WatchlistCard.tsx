import BookCover from './BookCover'
import { formatAuthor, type CatalogListing } from '../lib/catalog'

type WatchlistCardProps = {
  watchlistId: string
  catalog: CatalogListing | null
  expired: boolean
  onRemove: (watchlistId: string) => void
}

function StatusPill({ catalog, expired }: { catalog: CatalogListing | null; expired: boolean }) {
  if (!catalog) {
    return (
      <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400">
        Unknown
      </span>
    )
  }
  if (expired) {
    return (
      <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400">
        Unavailable
      </span>
    )
  }
  if (catalog.in_stock) {
    return (
      <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300">
        In Stock
      </span>
    )
  }
  return (
    <span className="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300">
      Out of Stock
    </span>
  )
}

export default function WatchlistCard({
  watchlistId,
  catalog,
  expired,
  onRemove,
}: WatchlistCardProps) {
  const title = catalog?.name ?? 'Unknown book'

  return (
    <article
      className={`rounded-xl bg-surface border border-border shadow-sm overflow-hidden flex flex-col ${
        expired ? 'opacity-50' : ''
      }`}
    >
      <div className="p-3 pb-0">
        <BookCover
          coverUrl={catalog?.cover_url}
          isbn={catalog?.isbn}
          openLibraryId={catalog?.open_library_id}
          title={title}
          size="md"
        />
      </div>

      <div className="p-4 flex flex-col flex-1 gap-2">
        <div>
          {catalog?.link ? (
            <a
              href={catalog.link}
              target="_blank"
              rel="noopener noreferrer"
              className="text-brand hover:text-brand-dark font-medium hover:underline line-clamp-2"
            >
              {title}
            </a>
          ) : (
            <h3 className="font-medium text-text line-clamp-2">{title}</h3>
          )}
          <p className="mt-1 text-sm text-text-muted truncate">{formatAuthor(catalog?.author)}</p>
          <p className="mt-1 text-sm text-text-muted truncate">
            {catalog?.store || '\u2014'}
            <span aria-hidden> &middot; </span>
            {catalog?.price || '\u2014'}
          </p>
        </div>

        <div className="mt-auto flex items-center justify-between gap-2 pt-1">
          <StatusPill catalog={catalog} expired={expired} />
          <button
            onClick={() => onRemove(watchlistId)}
            className="text-text-muted hover:text-red-600 dark:hover:text-red-400 transition-colors cursor-pointer shrink-0"
            title="Remove from watchlist"
          >
            &#10005;
          </button>
        </div>
      </div>
    </article>
  )
}
