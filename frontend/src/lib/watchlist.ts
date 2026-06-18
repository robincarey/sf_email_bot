import { supabase } from './supabase'

export type WatchlistTargets = {
  itemIds: Set<number>
  editionIds: Set<number>
}

export async function resolveEditionId(itemId: number): Promise<number | null> {
  const { data, error } = await supabase
    .from('retailer_listings')
    .select('edition_id')
    .eq('items_seen_id', itemId)
    .limit(1)
    .maybeSingle()

  if (error) {
    console.error('Error resolving edition_id:', error)
    return null
  }
  return data?.edition_id ?? null
}

export async function fetchWatchlistTargets(userId: string): Promise<WatchlistTargets> {
  const { data, error } = await supabase
    .from('watchlist')
    .select('item_id, edition_id')
    .eq('user_id', userId)

  if (error) {
    console.error('Error fetching watchlist:', error)
    return { itemIds: new Set(), editionIds: new Set() }
  }

  const itemIds = new Set<number>()
  const editionIds = new Set<number>()
  for (const row of data ?? []) {
    if (row.item_id != null) itemIds.add(row.item_id)
    if (row.edition_id != null) editionIds.add(row.edition_id)
  }
  return { itemIds, editionIds }
}

export async function addToWatchlist(userId: string, itemId: number): Promise<void> {
  const editionId = await resolveEditionId(itemId)
  if (editionId != null) {
    const { data: existing } = await supabase
      .from('watchlist')
      .select('id')
      .eq('user_id', userId)
      .eq('edition_id', editionId)
      .limit(1)
      .maybeSingle()
    if (existing) return
  }
  const row: { user_id: string; item_id: number; edition_id?: number } = {
    user_id: userId,
    item_id: itemId,
  }
  if (editionId != null) {
    row.edition_id = editionId
  }
  const { error } = await supabase.from('watchlist').insert(row)
  if (error) throw error
}

export async function removeFromWatchlist(
  userId: string,
  itemId: number,
  editionId?: number | null,
): Promise<void> {
  if (editionId != null) {
    const { error } = await supabase
      .from('watchlist')
      .delete()
      .eq('user_id', userId)
      .or(`item_id.eq.${itemId},edition_id.eq.${editionId}`)
    if (error) throw error
    return
  }

  const { error } = await supabase
    .from('watchlist')
    .delete()
    .eq('user_id', userId)
    .eq('item_id', itemId)
  if (error) throw error
}

export function isItemWatched(
  itemId: number,
  editionId: number | null | undefined,
  targets: WatchlistTargets,
): boolean {
  if (targets.itemIds.has(itemId)) return true
  if (editionId != null && targets.editionIds.has(editionId)) return true
  return false
}
