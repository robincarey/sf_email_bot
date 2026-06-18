export type CoverSize = 'S' | 'M'

export type CoverSourceFields = {
  cover_url?: string | null
  isbn?: string | null
  open_library_id?: string | null
}

export function normalizeOpenLibraryId(value: string | null | undefined): string | null {
  const trimmed = value?.trim()
  if (!trimmed) return null
  const withoutPrefix = trimmed.replace(/^\/works\//, '')
  return withoutPrefix || null
}

export function olCoverByIsbn(isbn: string, size: CoverSize = 'M'): string {
  const cleaned = isbn.replace(/[^0-9Xx]/g, '')
  return `https://covers.openlibrary.org/b/isbn/${encodeURIComponent(cleaned)}-${size}.jpg`
}

export function olCoverByOlid(olid: string, size: CoverSize = 'M'): string {
  const normalized = normalizeOpenLibraryId(olid)
  if (!normalized) return ''
  return `https://covers.openlibrary.org/b/olid/${encodeURIComponent(normalized)}-${size}.jpg`
}

export function coverSizeParam(uiSize: 'sm' | 'md'): CoverSize {
  return uiSize === 'sm' ? 'S' : 'M'
}

export function coverCandidates(
  item: CoverSourceFields,
  uiSize: 'sm' | 'md' = 'md',
): string[] {
  const size = coverSizeParam(uiSize)
  const candidates: string[] = []

  const coverUrl = item.cover_url?.trim()
  if (coverUrl) candidates.push(coverUrl)

  const isbn = item.isbn?.trim()
  if (isbn) candidates.push(olCoverByIsbn(isbn, size))

  const olid = normalizeOpenLibraryId(item.open_library_id)
  if (olid) candidates.push(olCoverByOlid(olid, size))

  return candidates
}
