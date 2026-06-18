import { useMemo, useState } from 'react'
import { coverCandidates } from '../lib/coverUtils'

type BookCoverProps = {
  coverUrl?: string | null
  isbn?: string | null
  openLibraryId?: string | null
  title: string
  size?: 'sm' | 'md'
  className?: string
}

const sizeClasses = {
  sm: 'w-10 h-[60px]',
  md: 'w-full h-40',
} as const

function Placeholder({ title, size }: { title: string; size: 'sm' | 'md' }) {
  const initial = (title.trim()[0] ?? '?').toUpperCase()
  return (
    <div
      className={`flex items-center justify-center rounded-md bg-surface-alt border border-border text-text-muted font-medium ${
        size === 'sm' ? 'text-xs' : 'text-2xl'
      } ${sizeClasses[size]}`}
      aria-hidden
    >
      {initial}
    </div>
  )
}

export default function BookCover({
  coverUrl,
  isbn,
  openLibraryId,
  title,
  size = 'md',
  className = '',
}: BookCoverProps) {
  const candidates = useMemo(
    () => coverCandidates({ cover_url: coverUrl, isbn, open_library_id: openLibraryId }, size),
    [coverUrl, isbn, openLibraryId, size],
  )

  const [candidateIndex, setCandidateIndex] = useState(0)
  const src = candidates[candidateIndex]

  if (!src) {
    return <Placeholder title={title} size={size} />
  }

  return (
    <img
      src={src}
      alt={`Cover of ${title}`}
      loading="lazy"
      className={`rounded-md object-cover bg-surface-alt border border-border ${sizeClasses[size]} ${className}`}
      onError={() => {
        setCandidateIndex((index) => {
          const next = index + 1
          return next < candidates.length ? next : candidates.length
        })
      }}
    />
  )
}
