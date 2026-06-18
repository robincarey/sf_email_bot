import { describe, expect, it } from 'vitest'
import {
  coverCandidates,
  normalizeOpenLibraryId,
  olCoverByIsbn,
  olCoverByOlid,
} from './coverUtils'

describe('coverUtils', () => {
  it('normalizes open library work ids', () => {
    expect(normalizeOpenLibraryId('/works/OL123456W')).toBe('OL123456W')
    expect(normalizeOpenLibraryId('OL123456W')).toBe('OL123456W')
  })

  it('builds OL cover URLs', () => {
    expect(olCoverByIsbn('978-0-123456-78-9', 'S')).toBe(
      'https://covers.openlibrary.org/b/isbn/9780123456789-S.jpg',
    )
    expect(olCoverByOlid('/works/OL123456W', 'M')).toBe(
      'https://covers.openlibrary.org/b/olid/OL123456W-M.jpg',
    )
  })

  it('orders cover candidates shopify then isbn then olid', () => {
    expect(
      coverCandidates(
        {
          cover_url: 'https://cdn.shopify.com/cover.jpg',
          isbn: '9780123456789',
          open_library_id: 'OL123456W',
        },
        'sm',
      ),
    ).toEqual([
      'https://cdn.shopify.com/cover.jpg',
      'https://covers.openlibrary.org/b/isbn/9780123456789-S.jpg',
      'https://covers.openlibrary.org/b/olid/OL123456W-S.jpg',
    ])
  })
})
