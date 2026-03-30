-- Migration: Wrapped Analytics Logging
-- Run this in Supabase SQL Editor before deploying the code changes.

-- 1. Add denormalized point-in-time columns to item_events
ALTER TABLE item_events ADD COLUMN IF NOT EXISTS store text;
ALTER TABLE item_events ADD COLUMN IF NOT EXISTS in_stock boolean;

-- 2. Create run_log table
CREATE TABLE IF NOT EXISTS run_log (
  run_id uuid PRIMARY KEY,
  started_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz,
  items_scraped int DEFAULT 0,
  events_created int DEFAULT 0,
  emails_attempted int DEFAULT 0,
  emails_sent int DEFAULT 0,
  status text DEFAULT 'started'
);

CREATE INDEX IF NOT EXISTS idx_run_log_started ON run_log(started_at DESC);

-- 3. Create item_status_daily snapshot table
CREATE TABLE IF NOT EXISTS item_status_daily (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  snapshot_date date NOT NULL DEFAULT current_date,
  item_id bigint NOT NULL REFERENCES items_seen(id),
  store text,
  in_stock boolean,
  price text,
  price_cents int,
  UNIQUE (snapshot_date, item_id)
);

CREATE INDEX IF NOT EXISTS idx_item_status_daily_item ON item_status_daily(item_id, snapshot_date DESC);
