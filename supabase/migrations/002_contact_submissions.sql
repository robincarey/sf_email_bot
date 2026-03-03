-- ============================================================
-- Migration: contact_submissions table
-- ============================================================

CREATE TABLE public.contact_submissions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    user_email  TEXT NOT NULL,
    category    TEXT NOT NULL CHECK (category IN ('suggest_website', 'report_bug', 'general')),
    url         TEXT,
    description TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.contact_submissions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can insert own submissions"
    ON public.contact_submissions FOR INSERT
    WITH CHECK (auth.uid() = user_id);
