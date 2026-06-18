-- Per-user event-type notification preferences.

CREATE TABLE IF NOT EXISTS public.user_event_preferences (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    event_type  TEXT NOT NULL,
    enabled     BOOLEAN NOT NULL DEFAULT true,
    UNIQUE (user_id, event_type)
);

ALTER TABLE public.user_event_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own event preferences"
    ON public.user_event_preferences FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update own event preferences"
    ON public.user_event_preferences FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Seed defaults for existing users (all emailable types on).
INSERT INTO public.user_event_preferences (user_id, event_type, enabled)
SELECT p.id, et.event_type, true
FROM public.profiles p
CROSS JOIN (
    VALUES
        ('New Item'),
        ('Restocked'),
        ('Price Change')
) AS et(event_type)
ON CONFLICT (user_id, event_type) DO NOTHING;

-- New profiles: default store prefs + event-type prefs.
CREATE OR REPLACE FUNCTION public.handle_new_profile()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_store_preferences (user_id, store_name, enabled) VALUES
        (NEW.id, 'Broken Binding - To The Stars', true),
        (NEW.id, 'Broken Binding - Dragon''s Hoard', true),
        (NEW.id, 'Broken Binding - The Infirmary', true),
        (NEW.id, 'Broken Binding - The Graveyard', true),
        (NEW.id, 'Folio Society - Sci-Fi & Fantasy', true);

    INSERT INTO public.user_event_preferences (user_id, event_type, enabled) VALUES
        (NEW.id, 'New Item', true),
        (NEW.id, 'Restocked', true),
        (NEW.id, 'Price Change', true);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public;
