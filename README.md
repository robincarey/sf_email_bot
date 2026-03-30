# sf_email_bot

Automated email notifications for new and restocked special-edition books from **The Broken Binding** and **The Folio Society** (Sci-Fi & Fantasy listing).

## Overview

This bot monitors storefronts: The Broken Binding’s four collections (To the Stars, Dragon’s Hoard, The Infirmary, and The Graveyard) and The Folio Society’s USA Sci-Fi & Fantasy category. It detects changes — new listings, restocks, price changes, stock-outs — and sends email alerts to subscribed users. All item and event data is persisted in Supabase for history tracking and future analytics.

Emails are sent with **Amazon SES** (via `boto3`); the Lambda execution role needs permission to send from your verified domain or address in SES.

A **frontend dashboard** (Vite + React) lets users sign up, manage per-store alert preferences, view recent events, and deactivate their account.

## Features

- **Multi-store scraping** with retry logic and exponential backoff (Broken Binding + Folio Society)
- **Change detection** — new items, restocks, out-of-stock, price changes, store changes
- **Canonical per-link store handling** — if the same Broken Binding product URL appears in multiple collections during one run, the bot picks a deterministic canonical store per `items_seen.link` to prevent noisy `Store Change` events, while still matching emails to users who enabled any store the item appeared in.
- **Per-event logging** — every detected change is recorded in `item_events` with a run-level UUID for traceability
- **Per-recipient email tracking** — `email_log` records delivery success/failure per user, linked to events via `email_log_events`
- **Per-store preferences** — users choose which stores they receive alerts for (Folio is added in migration `004`; new users default with Folio off until they opt in)
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
       ├─ broken_binding_sf.py   — scrapes Broken Binding collections
       ├─ folio_society_sf.py   — scrapes Folio Society Sci-Fi & Fantasy listing
       ├─ email_notifier.py     — sends email via Amazon SES
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
- An [AWS](https://aws.amazon.com) account with **Amazon SES** configured in your chosen region: verified sending identity (domain or email), and (if still in the SES sandbox) verified recipient addresses for testing

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
| `AWS_SES_REGION` | AWS region where SES is configured (e.g. `us-east-1`) |
| `SES_FROM_ADDRESS` | Verified SES sender address (must match SES configuration) |
| `RUN_MODE` | `prod` (default) or `dev` |
| `SEED_MODE` | set to `true` (or `1`) to run baseline catalog seeding (`run_log.status="seed"`) without generating `item_events` or sending emails |
| `ADMIN_EMAILS` | JSON array of emails for dev-mode testing, e.g. `'["you@example.com"]'` |

Ensure the **Lambda IAM role** attached to the function includes `ses:SendEmail` (and that the `Source` address or domain is verified in SES).

**Frontend** — create `frontend/.env`:

| Variable | Description |
|---|---|
| `VITE_SUPABASE_URL` | Your Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon key (safe for frontend; RLS protects data) |

### Database migrations

Apply the SQL migrations in order via the Supabase SQL Editor or Supabase CLI, including:

- `supabase/migrations/001_profiles_and_preferences.sql` — profiles, `user_store_preferences`, triggers, RLS
- Subsequent migrations as needed for your project (e.g. contact form, watchlist, **`004_folio_society_store.sql`** for the Folio Society store preference)

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
2. Zips the artifact (including `folio_society_sf.py` and SES-backed `email_notifier.py`)
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
| `user_store_preferences` | Per-user per-store notification toggles (Broken Binding collections + Folio Society) |
| `items_seen` | Canonical item catalog; upserted on every scrape |
| `item_events` | One row per detected change (restock, price change, etc.) |
| `item_status_daily` | Daily snapshots of item price/stock status |
| `email_log` | One row per email sent, with success/failure and error message |
| `email_log_events` | Junction linking each email to the events it covered |
| `run_log` | Run metadata: timestamps, counters, status |

## Future enhancements

- **Per-event-type preferences** — filter by event type (restocks, price changes, etc.)
- **Analytics dashboard** — "wrapped"-style metrics (most restocked, longest in stock, etc.)
- **Hard account deletion** — Supabase Edge Function to fully delete auth + profile data

## Contributing

Contributions are welcome. Fork the repository and submit a pull request for any enhancements or bug fixes.
