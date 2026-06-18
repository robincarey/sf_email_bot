-- ============================================================
-- Gold analytics views (Silver-aware)
-- Join item_events → retailer_listings → editions → works
-- for title-level deduplication and canonical catalog metadata.
-- ============================================================

DROP VIEW IF EXISTS public.analytics_restock_leaderboard;
DROP VIEW IF EXISTS public.analytics_top_price_drops;
DROP VIEW IF EXISTS public.analytics_event_volume_daily;
DROP VIEW IF EXISTS public.analytics_store_event_totals;
DROP VIEW IF EXISTS public.analytics_recent_restocks;

CREATE VIEW public.analytics_restock_leaderboard AS
SELECT *
FROM (
  SELECT
    e.id AS edition_id,
    w.id AS work_id,
    COUNT(*)::bigint AS restock_count,
    MAX(w.title) AS name,
    MAX(w.author) AS author,
    MAX(p.name) AS publisher,
    MAX(c.store_name) AS store,
    MAX(rl.retailer_url) AS link,
    MAX(ie.item_id) AS item_id
  FROM public.item_events ie
  INNER JOIN public.retailer_listings rl ON rl.items_seen_id = ie.item_id
  INNER JOIN public.editions e ON e.id = rl.edition_id
  INNER JOIN public.works w ON w.id = e.work_id
  LEFT JOIN public.publishers p ON p.id = e.publisher_id
  LEFT JOIN public.collections c ON c.id = rl.collection_id
  WHERE ie.event_type = 'Restocked'
  GROUP BY e.id, w.id
  ORDER BY restock_count DESC
  LIMIT 10
) q;

CREATE VIEW public.analytics_event_volume_daily AS
SELECT
  (ie.event_time AT TIME ZONE 'UTC')::date AS day,
  ie.event_type,
  COUNT(*)::bigint AS event_count
FROM public.item_events ie
GROUP BY 1, 2
ORDER BY 1, 2;

CREATE VIEW public.analytics_store_event_totals AS
SELECT
  COALESCE(ie.store, 'Unknown') AS store,
  COUNT(*)::bigint AS event_count
FROM public.item_events ie
GROUP BY 1
ORDER BY event_count DESC;

CREATE VIEW public.analytics_top_price_drops AS
SELECT *
FROM (
  WITH parsed AS (
    SELECT
      ie.id AS event_id,
      ie.item_id,
      ie.old_value,
      ie.new_value,
      NULLIF(regexp_replace(COALESCE(ie.old_value, ''), '[^0-9.]', '', 'g'), '')::numeric AS old_num,
      NULLIF(regexp_replace(COALESCE(ie.new_value, ''), '[^0-9.]', '', 'g'), '')::numeric AS new_num
    FROM public.item_events ie
    WHERE ie.event_type = 'Price Change'
  )
  SELECT
    p.event_id,
    p.item_id,
    e.id AS edition_id,
    p.old_value,
    p.new_value,
    p.old_num,
    p.new_num,
    (p.old_num - p.new_num) AS price_drop,
    w.title AS name,
    w.author,
    p2.name AS publisher,
    c.store_name AS store,
    rl.retailer_url AS link
  FROM parsed p
  INNER JOIN public.retailer_listings rl ON rl.items_seen_id = p.item_id
  INNER JOIN public.editions e ON e.id = rl.edition_id
  INNER JOIN public.works w ON w.id = e.work_id
  LEFT JOIN public.publishers p2 ON p2.id = e.publisher_id
  LEFT JOIN public.collections c ON c.id = rl.collection_id
  WHERE p.old_num IS NOT NULL
    AND p.new_num IS NOT NULL
    AND p.new_num < p.old_num
  ORDER BY price_drop DESC
  LIMIT 10
) q;

CREATE VIEW public.analytics_recent_restocks AS
SELECT
  ie.id,
  ie.event_time,
  ie.item_id,
  e.id AS edition_id,
  w.title AS name,
  w.author,
  p.name AS publisher,
  c.store_name AS store,
  rl.retailer_url AS link
FROM public.item_events ie
INNER JOIN public.retailer_listings rl ON rl.items_seen_id = ie.item_id
INNER JOIN public.editions e ON e.id = rl.edition_id
INNER JOIN public.works w ON w.id = e.work_id
LEFT JOIN public.publishers p ON p.id = e.publisher_id
LEFT JOIN public.collections c ON c.id = rl.collection_id
WHERE ie.event_type = 'Restocked';
