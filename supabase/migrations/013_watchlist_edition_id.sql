-- Watchlist: add edition_id for Silver-layer tracking (dual-write with item_id).

alter table public.watchlist
  add column if not exists edition_id integer references public.editions(id) on delete cascade;

create unique index if not exists watchlist_user_edition_uniq
  on public.watchlist (user_id, edition_id)
  where edition_id is not null;

create index if not exists watchlist_edition_id_idx
  on public.watchlist (edition_id);
