export const eventBadgeColors: Record<string, string> = {
  'New Item': 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
  'Restocked': 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
  'Price Change': 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
  'Store Change': 'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300',
  'Out of Stock': 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300',
  'New Item - Out of Stock': 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
}

export function formatRelativeTime(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime()
  const minutes = Math.floor(diffMs / 60_000)

  if (!Number.isFinite(minutes) || minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes} minute${minutes === 1 ? '' : 's'} ago`

  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} hour${hours === 1 ? '' : 's'} ago`

  const days = Math.floor(hours / 24)
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days} day${days === 1 ? '' : 's'} ago`

  return new Date(iso).toLocaleDateString()
}

