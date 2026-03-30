-- ============================================================
-- Migration: add Folio Society store preference
-- ============================================================

-- Add preference row for existing users, defaulting to disabled.
INSERT INTO public.user_store_preferences (user_id, store_name, enabled)
SELECT id, 'Folio Society - Sci-Fi & Fantasy', false
FROM public.profiles
ON CONFLICT (user_id, store_name) DO NOTHING;

-- Ensure future users get the new store preference defaulted off.
CREATE OR REPLACE FUNCTION public.handle_new_profile()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_store_preferences (user_id, store_name, enabled) VALUES
        (NEW.id, 'Broken Binding - To The Stars', true),
        (NEW.id, 'Broken Binding - Dragon''s Hoard', true),
        (NEW.id, 'Broken Binding - The Infirmary', true),
        (NEW.id, 'Folio Society - Sci-Fi & Fantasy', false);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public;
