# sf_email_bot

Automated email notifications for new and restocked special edition books from The Broken Binding.

## Overview

This bot monitors The Broken Binding's storefronts (To the Stars, Dragon's Hoard, and The Infirmary), detects changes — new listings, restocks, price changes, stock-outs — and sends email alerts to subscribed users. All item and event data is persisted in Supabase for history tracking and future analytics.

A **frontend dashboard** (Vite + React) lets users sign up, manage per-store alert preferences, view recent events, and deactivate their account.

## Features

- **Multi-store scraping** with retry logic and exponential backoff
- **Change detection** — new items, restocks, out-of-stock, price changes, store changes
- **Per-event logging** — every detected change is recorded in `item_events` with a run-level UUID for traceability
- **Per-recipient email tracking** — `email_log` records delivery success/failure per user, linked to events via `email_log_events`
- **Per-store preferences** — users choose which stores they receive alerts for
- **Structured logging** — every log line includes a `run_id` for easy CloudWatch debugging
- **Normalized pricing** — `typed_price` stores price as integer cents alongside the display string
- **Empty-scrape guard** — if the scraper returns no items, the diff and upsert are skipped to prevent data wipes
- **AWS Lambda deployment** — runs serverless on a schedule via EventBridge
- **CI/CD** — GitHub Actions builds and deploys to Lambda on push to `main`
- **Frontend dashboard** — self-service sign-up, preferences, recent alerts, account management

## Architecture

```
EventBridge (schedule)
  └─ Lambda (lambda_function.py)
       ├─ broken_binding_sf.py   — scrapes product pages
       ├─ email_notifier.py      — sends email via SMTP
       └─ Supabase (PostgreSQL)
            ├─ profiles                — user accounts (linked to Supabase Auth)
            ├─ user_store_preferences  — per-user per-store notification toggles
            ├─ items_seen              — canonical item catalog
            ├─ item_events             — change history per item
            ├─ item_status_daily       — daily price/stock snapshots
            ├─ email_log               — one row per email sent
            ├─ email_log_events        — junction: email ↔ events
            └─ run_log                 — run metadata and counters

Vercel (frontend/)
  └─ Vite + React SPA
       ├─ Supabase Auth (magic links)
       └─ Supabase JS client (anon key + RLS)
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js 20.19+ (for the frontend)
- A [Supabase](https://supabase.com) project with the schema tables created
- A Gmail account (or other SMTP provider) for sending notifications

### Install dependencies

**Backend:**

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Frontend:**

```bash
cd frontend
npm install
```

### Environment variables

**Backend** — create a `.env` file or set these in your Lambda configuration:

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Supabase service-role key (bypasses RLS) |
| `SF_EMAIL_USERNAME` | SMTP sender email address |
| `SF_EMAIL_PASSWORD` | SMTP password or app password |
| `RUN_MODE` | `prod` (default) or `dev` |
| `ADMIN_EMAILS` | JSON array of emails for dev-mode testing, e.g. `'["you@example.com"]'` |

**Frontend** — create `frontend/.env`:

| Variable | Description |
|---|---|
| `VITE_SUPABASE_URL` | Your Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon key (safe for frontend; RLS protects data) |

### Database migrations

Apply the SQL migration to set up the `profiles`, `user_store_preferences` tables, triggers, and RLS policies:

```bash
# Run supabase/migrations/001_profiles_and_preferences.sql against your Supabase database
# via the Supabase SQL Editor or the Supabase CLI
```

### Migrate existing users

If you have existing users in the old `users` table, run the migration script:

```bash
source venv/bin/activate
# Dry run first
python scripts/migrate_users.py
# Then apply
python scripts/migrate_users.py --apply
```

### Run locally

**Backend:**

```bash
source venv/bin/activate
python lambda_function.py
```

**Frontend:**

```bash
cd frontend
npm run dev
```

### Run tests

```bash
source venv/bin/activate
python -m unittest test_lambda_function -v
```

## Deployment

### Lambda (backend)

Pushes to `main` trigger the GitHub Actions workflow (`.github/workflows/lambda_deployment.yml`), which:

1. Builds the Lambda package in a Docker container matching the Lambda Python 3.11 runtime
2. Zips the artifact
3. Deploys to the `sf_bot` Lambda function via `aws lambda update-function-code`

Required GitHub Actions secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`.

### Vercel (frontend)

1. Connect the GitHub repo to [Vercel](https://vercel.com)
2. Set **Root Directory** to `frontend/`
3. Framework preset: **Vite**
4. Add environment variables: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`

Vercel auto-deploys on push to `main` via its GitHub integration.

### Supabase Auth configuration

In the Supabase Dashboard under **Auth > URL Configuration**:

- Set **Site URL** to your Vercel production URL (e.g. `https://your-app.vercel.app`)
- Add `http://localhost:5173` to **Redirect URLs** for local development

Enable the **Magic Link** provider under **Auth > Providers**.

## Database schema

| Table | Purpose |
|---|---|
| `profiles` | User accounts linked to Supabase Auth, with `is_active` and `pause_all_alerts` |
| `user_store_preferences` | Per-user per-store notification toggles |
| `items_seen` | Canonical item catalog; upserted on every scrape |
| `item_events` | One row per detected change (restock, price change, etc.) |
| `item_status_daily` | Daily snapshots of item price/stock status |
| `email_log` | One row per email sent, with success/failure and error message |
| `email_log_events` | Junction linking each email to the events it covered |
| `run_log` | Run metadata: timestamps, counters, status |

## Future enhancements

- **Multi-site monitoring** — add scraping modules for more special edition book retailers
- **Per-event-type preferences** — filter by event type (restocks, price changes, etc.)
- **AWS SES migration** — replace SMTP with SES for scalable email delivery
- **Analytics dashboard** — "wrapped"-style metrics (most restocked, longest in stock, etc.)
- **Hard account deletion** — Supabase Edge Function to fully delete auth + profile data

## Contributing

Contributions are welcome. Fork the repository and submit a pull request for any enhancements or bug fixes.
