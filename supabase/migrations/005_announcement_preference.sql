-- ============================================================
-- Migration: add announcement email preference
-- ============================================================

ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS receive_announcements BOOLEAN NOT NULL DEFAULT true;
