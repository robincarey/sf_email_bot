-- ============================================================
-- Hide "Unknown Change" from user-facing read paths (still stored in item_events)
-- ============================================================

DROP VIEW IF EXISTS public.catalog_events;

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
LEFT JOIN public.collections c ON c.id = rl.collection_id
WHERE ie.event_type <> 'Unknown Change';

GRANT SELECT ON public.catalog_events TO anon, authenticated;

DROP VIEW IF EXISTS public.analytics_event_volume_daily;
DROP VIEW IF EXISTS public.analytics_store_event_totals;
DROP VIEW IF EXISTS public.analytics_catalog_summary;

CREATE VIEW public.analytics_event_volume_daily AS
SELECT
  (ie.event_time AT TIME ZONE 'UTC')::date AS day,
  ie.event_type,
  COUNT(*)::bigint AS event_count
FROM public.item_events ie
WHERE ie.event_type <> 'Unknown Change'
GROUP BY 1, 2
ORDER BY 1, 2;

CREATE VIEW public.analytics_store_event_totals AS
SELECT
  COALESCE(ie.store, 'Unknown') AS store,
  COUNT(*)::bigint AS event_count
FROM public.item_events ie
WHERE ie.event_type <> 'Unknown Change'
GROUP BY 1
ORDER BY event_count DESC;

CREATE VIEW public.analytics_catalog_summary AS
SELECT
  (SELECT COUNT(*)::bigint FROM public.works) AS work_count,
  (SELECT COUNT(*)::bigint FROM public.editions) AS edition_count,
  (SELECT COUNT(*)::bigint FROM public.catalog_listings WHERE in_stock IS TRUE) AS in_stock_listings,
  (
    SELECT COUNT(*)::bigint
    FROM public.item_events
    WHERE event_time >= (now() AT TIME ZONE 'UTC') - interval '30 days'
      AND event_type <> 'Unknown Change'
  ) AS events_last_30_days,
  (SELECT MAX(snapshot_date) FROM public.item_status_daily) AS snapshot_through;

GRANT SELECT ON public.analytics_event_volume_daily TO anon, authenticated;
GRANT SELECT ON public.analytics_store_event_totals TO anon, authenticated;
GRANT SELECT ON public.analytics_catalog_summary TO anon, authenticated;
