import { supabase } from './supabase'

export type WatchlistTargets = {
  editionIds: Set<number>
}

export async function fetchWatchlistTargets(userId: string): Promise<WatchlistTargets> {
  const { data, error } = await supabase
    .from('watchlist')
    .select('edition_id')
    .eq('user_id', userId)

  if (error) {
    console.error('Error fetching watchlist:', error)
    return { editionIds: new Set() }
  }

  const editionIds = new Set<number>()
  for (const row of data ?? []) {
    if (row.edition_id != null) editionIds.add(row.edition_id)
  }
  return { editionIds }
}

export async function addToWatchlist(userId: string, editionId: number): Promise<void> {
  const { data: existing } = await supabase
    .from('watchlist')
    .select('id')
    .eq('user_id', userId)
    .eq('edition_id', editionId)
    .limit(1)
    .maybeSingle()
  if (existing) return

  const { error } = await supabase.from('watchlist').insert({
    user_id: userId,
    edition_id: editionId,
  })
  if (error) throw error
}

export async function removeFromWatchlist(userId: string, editionId: number): Promise<void> {
  const { error } = await supabase
    .from('watchlist')
    .delete()
    .eq('user_id', userId)
    .eq('edition_id', editionId)
  if (error) throw error
}

export function isItemWatched(
  editionId: number | null | undefined,
  targets: WatchlistTargets,
): boolean {
  return editionId != null && targets.editionIds.has(editionId)
}
