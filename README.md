# sf_email_bot

Automated email notifications for new and restocked special edition books from The Broken Binding.

## Overview

This bot monitors The Broken Binding's storefronts (To the Stars, Dragon's Hoard, and The Infirmary), detects changes — new listings, restocks, price changes, stock-outs — and sends email alerts to subscribed users. All item and event data is persisted in Supabase for history tracking and future analytics.

## Features

- **Multi-store scraping** with retry logic and exponential backoff
- **Change detection** — new items, restocks, out-of-stock, price changes, store changes
- **Per-event logging** — every detected change is recorded in `item_events` with a run-level UUID for traceability
- **Per-recipient email tracking** — `email_log` records delivery success/failure per user, linked to events via `email_log_events`
- **Structured logging** — every log line includes a `run_id` for easy CloudWatch debugging
- **Normalized pricing** — `typed_price` stores price as integer cents alongside the display string
- **Empty-scrape guard** — if the scraper returns no items, the diff and upsert are skipped to prevent data wipes
- **AWS Lambda deployment** — runs serverless on a schedule via EventBridge
- **CI/CD** — GitHub Actions builds and deploys to Lambda on push to `main`

## Architecture

```
EventBridge (schedule)
  └─ Lambda (lambda_function.py)
       ├─ broken_binding_sf.py   — scrapes product pages
       ├─ email_notifier.py      — sends email via SMTP
       └─ Supabase (PostgreSQL)
            ├─ users                — subscriber list
            ├─ user_preferences     — per-user per-store notification settings
            ├─ items_seen           — canonical item catalog
            ├─ item_events          — change history per item
            ├─ email_log            — one row per email sent
            └─ email_log_events     — junction: email ↔ events
```

## Setup

### Prerequisites

- Python 3.11+
- A [Supabase](https://supabase.com) project with the schema tables created
- A Gmail account (or other SMTP provider) for sending notifications

### Install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment variables

Create a `.env` file or set these in your Lambda configuration:

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Supabase service-role or anon key |
| `SF_EMAIL_USERNAME` | SMTP sender email address |
| `SF_EMAIL_PASSWORD` | SMTP password or app password |
| `RUN_MODE` | `prod` (default) or `dev` |
| `ADMIN_EMAILS` | JSON array of emails for dev-mode testing, e.g. `'["you@example.com"]'` |

### Run locally

```bash
source venv/bin/activate
python lambda_function.py
```

### Run tests

```bash
source venv/bin/activate
python -m unittest test_lambda_function -v
```

## Deployment

Pushes to `main` trigger the GitHub Actions workflow (`.github/workflows/lambda_deployment.yml`), which:

1. Builds the Lambda package in a Docker container matching the Lambda Python 3.11 runtime
2. Zips the artifact
3. Deploys to the `sf_bot` Lambda function via `aws lambda update-function-code`

Required GitHub Actions secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`.

## Database schema

| Table | Purpose |
|---|---|
| `users` | Subscribers with email and active status |
| `user_preferences` | Per-user per-store notification toggles |
| `items_seen` | Canonical item catalog; upserted on every scrape |
| `item_events` | One row per detected change (restock, price change, etc.) |
| `email_log` | One row per email sent, with success/failure and error message |
| `email_log_events` | Junction linking each email to the events it covered |

## Future enhancements

- **Multi-site monitoring** — add scraping modules for more special edition book retailers
- **User preferences filtering** — only notify users about stores they've opted into
- **AWS SES migration** — replace SMTP with SES for scalable email delivery
- **Analytics dashboard** — "wrapped"-style metrics (most restocked, longest in stock, etc.)
- **Front-end interface** — sign-up, login, and preference management

## Contributing

Contributions are welcome. Fork the repository and submit a pull request for any enhancements or bug fixes.
