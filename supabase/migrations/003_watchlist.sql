-- ============================================================
-- Migration: watchlist table
-- ============================================================

CREATE TABLE public.watchlist (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    item_id    INTEGER NOT NULL REFERENCES public.items_seen(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, item_id)
);

ALTER TABLE public.watchlist ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own watchlist"
    ON public.watchlist FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can add to own watchlist"
    ON public.watchlist FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can remove from own watchlist"
    ON public.watchlist FOR DELETE
    USING (auth.uid() = user_id);
