-- ============================================================
-- Migration: allow public (anon) reads for restocks feed
-- ============================================================

-- Existing migration(s) enable RLS and provide SELECT policies for authenticated users only.
-- This migration adds permissive SELECT policies so the landing page can display public
-- "Recent Restocks" without requiring a logged-in session.

ALTER TABLE public.item_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public can view events"
  ON public.item_events FOR SELECT
  USING (true);

ALTER TABLE public.items_seen ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public can view items"
  ON public.items_seen FOR SELECT
  USING (true);

