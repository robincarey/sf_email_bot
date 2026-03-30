-- ============================================================
-- Migration: add Broken Binding "The Graveyard" store
-- ============================================================

-- Add preference rows for existing users.
INSERT INTO public.user_store_preferences (user_id, store_name, enabled)
SELECT id, 'Broken Binding - The Graveyard', true
FROM public.profiles
ON CONFLICT (user_id, store_name) DO NOTHING;

-- Ensure future users get the new store preference enabled by default.
CREATE OR REPLACE FUNCTION public.handle_new_profile()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_store_preferences (user_id, store_name, enabled) VALUES
        (NEW.id, 'Broken Binding - To The Stars', true),
        (NEW.id, 'Broken Binding - Dragon''s Hoard', true),
        (NEW.id, 'Broken Binding - The Infirmary', true),
        (NEW.id, 'Broken Binding - The Graveyard', true),
        (NEW.id, 'Folio Society - Sci-Fi & Fantasy', true);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public;

