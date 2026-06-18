-- Watchlist: drop legacy item_id; edition_id is the canonical target.

ALTER TABLE public.watchlist
  DROP CONSTRAINT IF EXISTS watchlist_item_id_fkey;

ALTER TABLE public.watchlist
  DROP CONSTRAINT IF EXISTS watchlist_user_id_item_id_key;

ALTER TABLE public.watchlist
  DROP COLUMN IF EXISTS item_id;

ALTER TABLE public.watchlist
  ALTER COLUMN edition_id SET NOT NULL;
