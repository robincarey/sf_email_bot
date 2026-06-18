export type CatalogListing = {
  id: number
  listing_id: number
  edition_id: number
  work_id: number
  name: string
  author: string | null
  publisher: string | null
  store: string | null
  link: string
  price: string | null
  in_stock: boolean
  last_in_stock: string | null
  isbn: string | null
  cover_url: string | null
  open_library_id: string | null
}

export type CatalogEvent = {
  id: number
  item_id: number
  edition_id: number
  event_type: string
  store: string | null
  event_time: string
  in_stock: boolean
  old_value: string | null
  new_value: string | null
  name: string | null
  author: string | null
  link: string | null
}

export type CatalogRestockFeedItem = {
  id: number
  event_type: string
  event_time: string
  item_id: number
  edition_id: number
  name: string | null
  author: string | null
  store: string | null
  link: string | null
  price: string | null
}

export function formatAuthor(author: string | null | undefined): string {
  const trimmed = author?.trim()
  return trimmed || '\u2014'
}
