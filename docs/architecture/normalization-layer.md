# Normalization Layer Design (Silver)

## Context

The app ingests bookstore listings and sends subscriber alerts for new and restocked
special editions. Raw operational records are captured in `items_seen` and `item_events`.
As product scope expanded (watchlists, publisher-level analytics, cross-store tracking),
raw URL-centric entities became limiting for stable joins and deduplication.

This design introduces a canonical Silver layer while preserving compatibility for a
live production app with approximately 180 users.

## Objectives

- Normalize raw scrape data into stable entities (`publishers`, `collections`, `works`,
  `editions`, `retailer_listings`)
- Support deterministic joins for notifications, watchlists, and analytics
- Backfill safely with idempotent steps and reversible rollout
- Improve observability with explicit Silver promotion quality gates

## Medallion mapping

- **Bronze**: `items_seen`, `item_events` (raw operational ingest)
- **Silver**: canonical catalog + listing model (new normalized tables)
- **Gold**: analytics and product marts derived from Silver joins

## Key modeling decisions

- **Work vs edition separation**
  - `works` represents logical title/author identity
  - `editions` represents publication-specific variants
- **Listing bridge**
  - `retailer_listings` connects canonical editions to collection-specific URLs
  - `items_seen_id` preserves lineage back to Bronze records
- **Deterministic normalization keys**
  - normalized title and URL fields reduce duplicate/ambiguous matching
- **Schema-level contracts**
  - uniqueness indexes and foreign keys enforce data quality at write time

## Migration strategy

1. Create Silver tables and indexes without modifying existing read paths
2. Seed `publishers` and `collections` from existing store domain knowledge
3. Run idempotent backfill into `works` and `editions`
4. Run idempotent backfill into `retailer_listings`
5. Validate coverage, duplicates, and referential integrity
6. Enable dual-write (legacy + Silver) in scraper pipeline
7. Migrate dependent features (for example, watchlist foreign key) via dual-read/dual-write
8. Cut over reads to Silver behind a rollback-safe switch
9. Decommission legacy writes after a stabilization window

## Silver quality gate (promotion criteria)

Before production reads move from legacy to Silver:

- Coverage: >= 99% for Bronze records with non-null URL mapped to `retailer_listings`
- Duplicates: zero duplicates on Silver uniqueness keys
- Orphans: zero orphaned references on required foreign keys
- Null rates: within documented thresholds for key fields

If any gate fails, read path remains on legacy tables while mapping rules are corrected
and backfill is rerun.

## Rollout and risk controls

- Dual-write transition to avoid feature interruption during migration
- Idempotent backfills (`on conflict` patterns) to enable safe retries
- Read-path cutover only after parity checks and quality gate pass
- Fast rollback path to legacy reads if regressions are detected

## Outcome

The normalization layer converts a scraper-oriented schema into a production-grade data
foundation that is easier to reason about, safer to evolve, and better aligned with
data engineering best practices for canonical modeling and analytics enablement.

