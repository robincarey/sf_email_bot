-- Silver catalog layer (publishers, collections, works, editions, retailer_listings).
-- Idempotent: safe to run against a project where these objects already exist.

create table if not exists public.publishers (
  id serial primary key,
  name text not null,
  country text,
  base_url text,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.collections (
  id serial primary key,
  publisher_id int not null references public.publishers(id),
  name text not null,
  store_name text not null unique,
  scrape_url text,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.works (
  id serial primary key,
  title text not null,
  author text,
  normalized_title text not null,
  normalized_author text,
  open_library_id text,
  created_at timestamptz not null default now()
);

create table if not exists public.editions (
  id serial primary key,
  work_id int references public.works(id),
  publisher_id int references public.publishers(id),
  title text not null,
  normalized_title text not null,
  isbn text,
  edition_type text,
  print_run_size int,
  cover_artist text,
  sprayed_edges boolean,
  slipcase boolean,
  foil_details text,
  physical_format text,
  description text,
  created_at timestamptz not null default now()
);

create table if not exists public.retailer_listings (
  id serial primary key,
  edition_id int references public.editions(id),
  collection_id int not null references public.collections(id),
  retailer_url text not null,
  retailer_url_normalized text not null,
  items_seen_id bigint references public.items_seen(id),
  in_stock boolean,
  price_cents int,
  last_checked timestamptz,
  created_at timestamptz not null default now()
);

create unique index if not exists works_norm_uniq
  on public.works (normalized_title, coalesce(normalized_author, ''));

create unique index if not exists editions_norm_uniq
  on public.editions (work_id, publisher_id, normalized_title, coalesce(edition_type, ''));

create unique index if not exists retailer_listings_collection_url_uniq
  on public.retailer_listings (collection_id, retailer_url_normalized);

-- Correct normalization helper (use in backfills; do NOT use word-boundary stripping).
-- lower(regexp_replace(trim(title), '[^a-z0-9]+', ' ', 'g'))
