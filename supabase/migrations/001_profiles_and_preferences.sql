-- ============================================================
-- Migration: profiles, user_store_preferences, triggers, RLS
-- ============================================================

-- 1. profiles table (replaces the old "users" table)
CREATE TABLE profiles (
    id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email           TEXT NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    pause_all_alerts BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
    ON profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- 2. user_store_preferences table
CREATE TABLE user_store_preferences (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    store_name  TEXT NOT NULL,
    enabled     BOOLEAN NOT NULL DEFAULT true,
    UNIQUE(user_id, store_name)
);

ALTER TABLE user_store_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own store preferences"
    ON user_store_preferences FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update own store preferences"
    ON user_store_preferences FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 3. RLS on existing tables (read-only for authenticated frontend users)
--    The Lambda uses the service-role key, which bypasses RLS entirely.
ALTER TABLE item_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view events"
    ON item_events FOR SELECT
    USING (auth.uid() IS NOT NULL);

ALTER TABLE items_seen ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view items"
    ON items_seen FOR SELECT
    USING (auth.uid() IS NOT NULL);

-- 4. Trigger: auto-create a profile row when a new auth user signs up
--    SET search_path = public is required because the auth system fires
--    triggers in a session where the public schema may not be on the path.
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email)
    VALUES (NEW.id, NEW.email);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- 5. Trigger: auto-create default store preferences when a profile is created
CREATE OR REPLACE FUNCTION public.handle_new_profile()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_store_preferences (user_id, store_name) VALUES
        (NEW.id, 'Broken Binding - To The Stars'),
        (NEW.id, 'Broken Binding - Dragon''s Hoard'),
        (NEW.id, 'Broken Binding - The Infirmary');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public;

CREATE TRIGGER on_profile_created
    AFTER INSERT ON profiles
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_profile();

-- 6. updated_at auto-touch on profiles
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
