"""
Silver layer promotion quality gate.

Runs the checks defined in docs/architecture/normalization-layer.md before
cutting reads to Silver or deploying Gold views.

Usage:
  python scripts/silver_quality_gate.py           # human-readable report
  python scripts/silver_quality_gate.py --json    # machine-readable
  python scripts/silver_quality_gate.py --strict  # fail on author null-rate warnings

Exit code 0 = all required checks pass, 1 = at least one failure.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

load_dotenv()

MIN_LISTING_COVERAGE_PCT = 99.0
MAX_WORKS_AUTHOR_NULL_PCT = 5.0
MAX_ITEMS_SEEN_AUTHOR_NULL_PCT = 5.0


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str
    severity: str = "error"  # error | warn


def connect():
    url = os.getenv("SUPABASE_URL", "")
    password = os.getenv("SUPABASE_PASS")
    if not password:
        raise SystemExit("SUPABASE_PASS is required")
    m = re.search(r"https://([^.]+)\.supabase\.co", url)
    if not m:
        raise SystemExit(f"Could not parse project ref from SUPABASE_URL: {url}")
    ref = m.group(1)
    return psycopg2.connect(
        host="aws-1-us-east-1.pooler.supabase.com",
        dbname="postgres",
        user=f"postgres.{ref}",
        password=password,
        port=5432,
        sslmode="require",
    )


def run_checks(cur) -> list[CheckResult]:
    results: list[CheckResult] = []

    # --- Coverage ---
    cur.execute(
        """
        SELECT
          count(*)::int AS total,
          count(rl.id)::int AS matched
        FROM public.items_seen i
        LEFT JOIN public.retailer_listings rl ON rl.items_seen_id = i.id
        WHERE i.link IS NOT NULL
        """
    )
    total, matched = cur.fetchone()
    pct = round(100.0 * matched / total, 2) if total else 100.0
    results.append(
        CheckResult(
            name="retailer_listings_coverage",
            passed=pct >= MIN_LISTING_COVERAGE_PCT,
            detail=f"{matched}/{total} items with link mapped ({pct}%; need >= {MIN_LISTING_COVERAGE_PCT}%)",
        )
    )

    cur.execute(
        """
        SELECT i.id, i.name, i.store, i.link
        FROM public.items_seen i
        LEFT JOIN public.retailer_listings rl ON rl.items_seen_id = i.id
        WHERE i.link IS NOT NULL AND rl.id IS NULL
        ORDER BY i.id
        LIMIT 5
        """
    )
    unmatched = cur.fetchall()
    if unmatched:
        sample = "; ".join(f"id={r[0]} {r[1]!r}" for r in unmatched)
        results.append(
            CheckResult(
                name="unmapped_items_sample",
                passed=True,
                detail=f"sample unmapped ({len(unmatched)} shown): {sample}",
                severity="warn",
            )
        )

    # --- Duplicates ---
    dup_queries = [
        (
            "works_normalized_uniq",
            """
            SELECT normalized_title, coalesce(normalized_author, ''), count(*)::int
            FROM public.works
            GROUP BY 1, 2
            HAVING count(*) > 1
            LIMIT 5
            """,
        ),
        (
            "editions_normalized_uniq",
            """
            SELECT work_id, publisher_id, normalized_title, coalesce(edition_type, ''), count(*)::int
            FROM public.editions
            GROUP BY 1, 2, 3, 4
            HAVING count(*) > 1
            LIMIT 5
            """,
        ),
        (
            "retailer_listings_url_uniq",
            """
            SELECT collection_id, retailer_url_normalized, count(*)::int
            FROM public.retailer_listings
            GROUP BY 1, 2
            HAVING count(*) > 1
            LIMIT 5
            """,
        ),
        (
            "watchlist_user_edition_uniq",
            """
            SELECT user_id, edition_id, count(*)::int
            FROM public.watchlist
            WHERE edition_id IS NOT NULL
            GROUP BY 1, 2
            HAVING count(*) > 1
            LIMIT 5
            """,
        ),
    ]
    for name, sql in dup_queries:
        cur.execute(sql)
        rows = cur.fetchall()
        results.append(
            CheckResult(
                name=name,
                passed=len(rows) == 0,
                detail="no duplicates" if not rows else f"duplicates found: {rows}",
            )
        )

    # --- Orphans ---
    orphan_queries = [
        (
            "retailer_listings_missing_edition",
            "SELECT count(*)::int FROM public.retailer_listings WHERE edition_id IS NULL",
        ),
        (
            "retailer_listings_missing_collection",
            "SELECT count(*)::int FROM public.retailer_listings WHERE collection_id IS NULL",
        ),
        (
            "retailer_listings_missing_items_seen",
            "SELECT count(*)::int FROM public.retailer_listings WHERE items_seen_id IS NULL",
        ),
        (
            "editions_missing_work",
            "SELECT count(*)::int FROM public.editions WHERE work_id IS NULL",
        ),
        (
            "collections_missing_publisher",
            "SELECT count(*)::int FROM public.collections WHERE publisher_id IS NULL",
        ),
        (
            "watchlist_missing_edition",
            "SELECT count(*)::int FROM public.watchlist WHERE edition_id IS NULL",
        ),
    ]
    for name, sql in orphan_queries:
        cur.execute(sql)
        (count,) = cur.fetchone()
        results.append(
            CheckResult(
                name=name,
                passed=count == 0,
                detail=f"{count} orphan rows",
            )
        )

    # --- Null rates ---
    cur.execute(
        """
        SELECT
          count(*)::int AS total,
          count(*) FILTER (WHERE author IS NULL)::int AS null_author
        FROM public.works
        """
    )
    w_total, w_null = cur.fetchone()
    w_pct = round(100.0 * w_null / w_total, 2) if w_total else 0.0
    results.append(
        CheckResult(
            name="works_author_null_rate",
            passed=w_pct <= MAX_WORKS_AUTHOR_NULL_PCT,
            detail=f"{w_null}/{w_total} works missing author ({w_pct}%; warn above {MAX_WORKS_AUTHOR_NULL_PCT}%)",
            severity="warn" if w_pct <= MAX_WORKS_AUTHOR_NULL_PCT else "error",
        )
    )

    cur.execute(
        """
        SELECT
          count(*)::int AS total,
          count(*) FILTER (WHERE author IS NULL)::int AS null_author
        FROM public.items_seen
        WHERE link IS NOT NULL
        """
    )
    i_total, i_null = cur.fetchone()
    i_pct = round(100.0 * i_null / i_total, 2) if i_total else 0.0
    results.append(
        CheckResult(
            name="items_seen_author_null_rate",
            passed=i_pct <= MAX_ITEMS_SEEN_AUTHOR_NULL_PCT,
            detail=f"{i_null}/{i_total} items missing author ({i_pct}%; warn above {MAX_ITEMS_SEEN_AUTHOR_NULL_PCT}%)",
            severity="warn" if i_pct <= MAX_ITEMS_SEEN_AUTHOR_NULL_PCT else "error",
        )
    )

    # --- Row counts (informational) ---
    for table in ("publishers", "collections", "works", "editions", "retailer_listings", "watchlist"):
        cur.execute(f"SELECT count(*)::int FROM public.{table}")
        (count,) = cur.fetchone()
        results.append(
            CheckResult(
                name=f"count_{table}",
                passed=True,
                detail=str(count),
                severity="info",
            )
        )

    return results


def evaluate(results: list[CheckResult], strict: bool) -> bool:
    for r in results:
        if r.severity == "info":
            continue
        if r.severity == "warn" and not strict:
            continue
        if not r.passed:
            return False
    return True


def print_report(results: list[CheckResult], overall: bool) -> None:
    print("Silver quality gate\n" + "=" * 40)
    for r in results:
        if r.severity == "info":
            print(f"  {r.name}: {r.detail}")
            continue
        icon = "PASS" if r.passed else "FAIL"
        level = r.severity.upper()
        print(f"[{icon}] ({level}) {r.name}: {r.detail}")
    print("=" * 40)
    print("OVERALL:", "PASS" if overall else "FAIL")


def main():
    parser = argparse.ArgumentParser(description="Silver layer promotion quality gate")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat author null-rate warnings as failures",
    )
    args = parser.parse_args()

    conn = connect()
    try:
        cur = conn.cursor()
        results = run_checks(cur)
        overall = evaluate(results, args.strict)
    finally:
        conn.close()

    if args.json:
        payload = {
            "passed": overall,
            "checks": [asdict(r) for r in results],
        }
        print(json.dumps(payload, indent=2))
    else:
        print_report(results, overall)

    sys.exit(0 if overall else 1)


if __name__ == "__main__":
    main()
