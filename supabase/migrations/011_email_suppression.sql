-- Email suppression tracking for SES bounces/complaints

ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS email_suppressed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS email_suppressed_reason TEXT;

ALTER TABLE email_engagement_events
  ADD COLUMN IF NOT EXISTS delivery_metadata JSONB;

CREATE INDEX IF NOT EXISTS idx_email_log_ses_message_id
  ON email_log (ses_message_id);

-- Keep profiles.email in sync when auth.users email is confirmed/changed
CREATE OR REPLACE FUNCTION public.handle_auth_user_email_update()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.email IS DISTINCT FROM OLD.email THEN
    UPDATE public.profiles SET email = NEW.email WHERE id = NEW.id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public;

DROP TRIGGER IF EXISTS on_auth_user_email_updated ON auth.users;

CREATE TRIGGER on_auth_user_email_updated
  AFTER UPDATE OF email ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_auth_user_email_update();
