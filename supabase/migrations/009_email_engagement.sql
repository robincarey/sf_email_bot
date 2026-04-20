-- Add to email_log
alter table public.email_log 
add column ses_message_id text;

-- Create new table
create table public.email_engagement_events (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  email_log_id bigint references public.email_log(id),
  ses_message_id text not null,
  event_type text not null,
  event_timestamp timestamptz,
  url_clicked text,
  user_id uuid references public.profiles(id),
  item_id bigint references public.items_seen(id)
);