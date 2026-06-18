-- ============================================================
-- Wrapped-style analytics from daily stock snapshots + events
-- ============================================================

-- item_status_daily has RLS enabled but no policies; views need read access.
CREATE POLICY "Public can view daily status"
  ON public.item_status_daily FOR SELECT
  USING (true);

DROP VIEW IF EXISTS public.analytics_catalog_summary;
DROP VIEW IF EXISTS public.analytics_longest_in_stock;
DROP VIEW IF EXISTS public.analytics_current_in_stock_streak;
DROP VIEW IF EXISTS public.analytics_new_item_leaderboard;
DROP VIEW IF EXISTS public.analytics_out_of_stock_leaderboard;

CREATE VIEW public.analytics_catalog_summary AS
SELECT
  (SELECT COUNT(*)::bigint FROM public.works) AS work_count,
  (SELECT COUNT(*)::bigint FROM public.editions) AS edition_count,
  (SELECT COUNT(*)::bigint FROM public.catalog_listings WHERE in_stock IS TRUE) AS in_stock_listings,
  (SELECT COUNT(*)::bigint FROM public.item_events WHERE event_time >= (now() AT TIME ZONE 'UTC') - interval '30 days') AS events_last_30_days,
  (SELECT MAX(snapshot_date) FROM public.item_status_daily) AS snapshot_through;

-- Longest consecutive in-stock run (snapshot days) per edition, all time.
CREATE VIEW public.analytics_longest_in_stock AS
SELECT *
FROM (
  WITH in_stock_days AS (
    SELECT
      isd.item_id,
      isd.snapshot_date,
      isd.snapshot_date - ROW_NUMBER() OVER (
        PARTITION BY isd.item_id ORDER BY isd.snapshot_date
      )::integer AS streak_group
    FROM public.item_status_daily isd
    WHERE isd.in_stock IS TRUE
  ),
  streak_lengths AS (
    SELECT
      item_id,
      COUNT(*)::integer AS streak_days
    FROM in_stock_days
    GROUP BY item_id, streak_group
  ),
  item_best AS (
    SELECT
      item_id,
      MAX(streak_days)::integer AS longest_in_stock_days
    FROM streak_lengths
    GROUP BY item_id
  ),
  edition_item AS (
    SELECT DISTINCT ON (rl.edition_id)
      rl.edition_id,
      ib.longest_in_stock_days,
      rl.items_seen_id AS item_id,
      rl.collection_id,
      rl.retailer_url AS link
    FROM item_best ib
    INNER JOIN public.retailer_listings rl ON rl.items_seen_id = ib.item_id
    ORDER BY rl.edition_id, ib.longest_in_stock_days DESC, rl.items_seen_id
  )
  SELECT
    ei.edition_id,
    ei.item_id,
    ei.longest_in_stock_days,
    w.title AS name,
    w.author,
    p.name AS publisher,
    c.store_name AS store,
    ei.link
  FROM edition_item ei
  INNER JOIN public.editions e ON e.id = ei.edition_id
  INNER JOIN public.works w ON w.id = e.work_id
  LEFT JOIN public.publishers p ON p.id = e.publisher_id
  LEFT JOIN public.collections c ON c.id = ei.collection_id
  ORDER BY ei.longest_in_stock_days DESC
  LIMIT 10
) q;

-- Ongoing in-stock streak for editions currently in stock (ends on latest snapshot day).
CREATE VIEW public.analytics_current_in_stock_streak AS
SELECT *
FROM (
  WITH latest_per_item AS (
    SELECT DISTINCT ON (item_id)
      item_id,
      snapshot_date,
      in_stock
    FROM public.item_status_daily
    ORDER BY item_id, snapshot_date DESC
  ),
  actively_stocked AS (
    SELECT item_id, snapshot_date AS as_of_date
    FROM latest_per_item
    WHERE in_stock IS TRUE
  ),
  grouped AS (
    SELECT
      isd.item_id,
      isd.snapshot_date,
      isd.snapshot_date - ROW_NUMBER() OVER (
        PARTITION BY isd.item_id ORDER BY isd.snapshot_date
      )::integer AS streak_group
    FROM public.item_status_daily isd
    INNER JOIN actively_stocked a ON a.item_id = isd.item_id
    WHERE isd.in_stock IS TRUE
      AND isd.snapshot_date <= a.as_of_date
  ),
  current_streaks AS (
    SELECT
      g.item_id,
      COUNT(*)::integer AS current_streak_days
    FROM grouped g
    INNER JOIN actively_stocked a
      ON a.item_id = g.item_id
     AND g.snapshot_date = a.as_of_date
    GROUP BY g.item_id, g.streak_group
  ),
  edition_item AS (
    SELECT DISTINCT ON (rl.edition_id)
      rl.edition_id,
      cs.current_streak_days,
      rl.items_seen_id AS item_id,
      rl.collection_id,
      rl.retailer_url AS link
    FROM current_streaks cs
    INNER JOIN public.retailer_listings rl ON rl.items_seen_id = cs.item_id
    ORDER BY rl.edition_id, cs.current_streak_days DESC, rl.items_seen_id
  )
  SELECT
    ei.edition_id,
    ei.item_id,
    ei.current_streak_days,
    w.title AS name,
    w.author,
    p.name AS publisher,
    c.store_name AS store,
    ei.link
  FROM edition_item ei
  INNER JOIN public.editions e ON e.id = ei.edition_id
  INNER JOIN public.works w ON w.id = e.work_id
  LEFT JOIN public.publishers p ON p.id = e.publisher_id
  LEFT JOIN public.collections c ON c.id = ei.collection_id
  ORDER BY ei.current_streak_days DESC
  LIMIT 10
) q;

CREATE VIEW public.analytics_new_item_leaderboard AS
SELECT *
FROM (
  SELECT
    e.id AS edition_id,
    w.id AS work_id,
    COUNT(*)::bigint AS new_item_count,
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
  WHERE ie.event_type = 'New Item'
  GROUP BY e.id, w.id
  ORDER BY new_item_count DESC
  LIMIT 10
) q;

CREATE VIEW public.analytics_out_of_stock_leaderboard AS
SELECT *
FROM (
  SELECT
    e.id AS edition_id,
    w.id AS work_id,
    COUNT(*)::bigint AS out_of_stock_count,
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
  WHERE ie.event_type = 'Out of Stock'
  GROUP BY e.id, w.id
  ORDER BY out_of_stock_count DESC
  LIMIT 10
) q;

GRANT SELECT ON public.analytics_catalog_summary TO anon, authenticated;
GRANT SELECT ON public.analytics_longest_in_stock TO anon, authenticated;
GRANT SELECT ON public.analytics_current_in_stock_streak TO anon, authenticated;
GRANT SELECT ON public.analytics_new_item_leaderboard TO anon, authenticated;
GRANT SELECT ON public.analytics_out_of_stock_leaderboard TO anon, authenticated;
