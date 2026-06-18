-- ============================================================
-- Gold read-path views for frontend cutover (Silver-backed)
-- ============================================================

DROP VIEW IF EXISTS public.catalog_restock_feed;
DROP VIEW IF EXISTS public.catalog_events;
DROP VIEW IF EXISTS public.catalog_listings;

CREATE VIEW public.catalog_listings AS
SELECT
  rl.items_seen_id AS id,
  rl.id AS listing_id,
  rl.edition_id,
  e.work_id,
  w.title AS name,
  w.author,
  p.name AS publisher,
  c.store_name AS store,
  rl.retailer_url AS link,
  COALESCE(rl.in_stock, i.in_stock) AS in_stock,
  i.last_in_stock,
  CASE
    WHEN i.price IS NOT NULL AND btrim(i.price) <> '' THEN i.price
    WHEN rl.price_cents IS NOT NULL THEN
      '$' || to_char(rl.price_cents / 100.0, 'FM999999990.00')
    ELSE NULL
  END AS price
FROM public.retailer_listings rl
INNER JOIN public.editions e ON e.id = rl.edition_id
INNER JOIN public.works w ON w.id = e.work_id
INNER JOIN public.collections c ON c.id = rl.collection_id
LEFT JOIN public.publishers p ON p.id = e.publisher_id
INNER JOIN public.items_seen i ON i.id = rl.items_seen_id;

CREATE VIEW public.catalog_events AS
SELECT
  ie.id,
  ie.item_id,
  rl.edition_id,
  ie.event_type,
  COALESCE(ie.store, c.store_name) AS store,
  ie.event_time,
  ie.in_stock,
  ie.old_value,
  ie.new_value,
  w.title AS name,
  w.author,
  rl.retailer_url AS link
FROM public.item_events ie
INNER JOIN public.retailer_listings rl ON rl.items_seen_id = ie.item_id
INNER JOIN public.editions e ON e.id = rl.edition_id
INNER JOIN public.works w ON w.id = e.work_id
LEFT JOIN public.collections c ON c.id = rl.collection_id;

CREATE VIEW public.catalog_restock_feed AS
SELECT
  ie.id,
  ie.event_type,
  ie.event_time,
  ie.item_id,
  e.id AS edition_id,
  w.title AS name,
  w.author,
  c.store_name AS store,
  rl.retailer_url AS link,
  CASE
    WHEN i.price IS NOT NULL AND btrim(i.price) <> '' THEN i.price
    WHEN rl.price_cents IS NOT NULL THEN
      '$' || to_char(rl.price_cents / 100.0, 'FM999999990.00')
    ELSE NULL
  END AS price
FROM public.item_events ie
INNER JOIN public.retailer_listings rl ON rl.items_seen_id = ie.item_id
INNER JOIN public.editions e ON e.id = rl.edition_id
INNER JOIN public.works w ON w.id = e.work_id
LEFT JOIN public.collections c ON c.id = rl.collection_id
INNER JOIN public.items_seen i ON i.id = ie.item_id
WHERE ie.event_type IN ('Restocked', 'New Item');

GRANT SELECT ON public.catalog_listings TO anon, authenticated;
GRANT SELECT ON public.catalog_events TO anon, authenticated;
GRANT SELECT ON public.catalog_restock_feed TO anon, authenticated;
