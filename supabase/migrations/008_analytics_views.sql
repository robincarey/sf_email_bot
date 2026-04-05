-- ============================================================
-- Analytics views for dashboard (PostgREST / Supabase JS)
-- ============================================================

CREATE OR REPLACE VIEW public.analytics_restock_leaderboard AS
SELECT *
FROM (
  SELECT
    ie.item_id,
    COUNT(*)::bigint AS restock_count,
    MAX(i.name) AS name,
    MAX(i.store) AS store,
    MAX(i.link) AS link
  FROM public.item_events ie
  INNER JOIN public.items_seen i ON i.id = ie.item_id
  WHERE ie.event_type = 'Restocked'
  GROUP BY ie.item_id
  ORDER BY restock_count DESC
  LIMIT 10
) q;

CREATE OR REPLACE VIEW public.analytics_event_volume_daily AS
SELECT
  (ie.event_time AT TIME ZONE 'UTC')::date AS day,
  ie.event_type,
  COUNT(*)::bigint AS event_count
FROM public.item_events ie
GROUP BY 1, 2
ORDER BY 1, 2;

CREATE OR REPLACE VIEW public.analytics_store_event_totals AS
SELECT
  COALESCE(ie.store, 'Unknown') AS store,
  COUNT(*)::bigint AS event_count
FROM public.item_events ie
GROUP BY 1
ORDER BY event_count DESC;

CREATE OR REPLACE VIEW public.analytics_top_price_drops AS
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
    p.old_value,
    p.new_value,
    p.old_num,
    p.new_num,
    (p.old_num - p.new_num) AS price_drop,
    i.name,
    i.store,
    i.link
  FROM parsed p
  INNER JOIN public.items_seen i ON i.id = p.item_id
  WHERE p.old_num IS NOT NULL
    AND p.new_num IS NOT NULL
    AND p.new_num < p.old_num
  ORDER BY price_drop DESC
  LIMIT 10
) q;
