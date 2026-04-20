---
name: Skip DB writes in dev
overview: Guard all database write operations in `check_for_updates()` behind a `run_mode != 'dev'` check so that local test runs still scrape, diff, and send emails to admins, but never persist changes to the database.
todos:
  - id: add-dry-run-flag
    content: Add `dry_run` flag and log line at the top of `check_for_updates()`
    status: completed
  - id: guard-writes
    content: Wrap all 7 DB write call sites with `if not dry_run:` guards, using `[]` fallback for `insert_events`
    status: completed
isProject: false
---

# Skip DB Writes in Dev Mode

## Problem

Running `RUN_MODE=dev` locally triggers the full pipeline: scrape, diff, upsert items, insert events, send emails, and log everything. The DB writes cause the frontend to display test artifacts (e.g., a fake "Restocked" event from a manually toggled item).

## Approach

Add a `dry_run` flag derived from `run_mode == 'dev'` inside `check_for_updates()` in [lambda_function.py](lambda_function.py). When `dry_run` is true, skip all seven DB write call sites while keeping reads, scraping, diffing, and email sends intact.

### Writes to skip (all in `check_for_updates()`):


| Line | Call | Table |
| ---- | ---- | ----- |


- **Line 328**: `insert_run_log(run_id)` -- `run_log`
- **Line 525**: `save_seen_items(new_items_canonical, run_id)` -- `items_seen`
- **Line 532**: `insert_daily_snapshots(...)` -- `item_status_daily`
- **Line 552**: `insert_events(event_rows, run_id)` -- `item_events`
- **Line 634**: `insert_email_log(log_rows, run_id)` -- `email_log`
- **Line 645**: `insert_email_log_events(junction_rows, run_id)` -- `email_log_events`
- **Lines 415, 559, 564, 648**: `update_run_log(run_id, ...)` -- `run_log`

### What stays the same in dev mode:

- DB **reads** (load seen items, fetch recipients, store prefs, watchlists) -- needed to compute the diff
- **Scraping** -- the whole point of running locally
- **Email sending** -- the whole point of testing; dev mode already restricts recipients to `ADMIN_EMAILS`

### Implementation detail

`inserted_events` (returned by `insert_events`) is used downstream at line 595 to build `recip_event_ids` for the email log junction table. When `dry_run` is true, `inserted_events` will be set to `[]`, which means `recip_event_ids` will be empty -- that's fine because we're also skipping the `email_log` and `email_log_events` inserts. Email sending itself does not depend on `inserted_events`.

### Changes in [lambda_function.py](lambda_function.py):

1. Add `dry_run = (run_mode == 'dev')` at the top of `check_for_updates()`, with a log line announcing it.
2. Wrap each of the seven write call sites with `if not dry_run:` guards.
3. Where a write's return value is used downstream (only `insert_events`), assign an empty list as the fallback.

