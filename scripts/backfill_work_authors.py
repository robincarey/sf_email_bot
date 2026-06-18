"""
Backfill works.author from Open Library with a reviewable CSV step.

Prerequisites:
  - SUPABASE_URL and SUPABASE_KEY (or SUPABASE_SERVICE_ROLE_KEY) env vars set.

Usage:
  python scripts/backfill_work_authors.py propose
  python scripts/backfill_work_authors.py propose --limit 50
  python scripts/backfill_work_authors.py apply --input out/work_author_proposals_....csv
"""

import argparse
import csv
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from open_library import lookup_author, normalize_text, titles_match  # noqa: E402

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
OUT_DIR = ROOT / "out"

CSV_FIELDS = [
    "work_id",
    "title",
    "normalized_title",
    "ol_author",
    "ol_work_key",
    "ol_title",
    "ol_num_docs",
    "approve",
]


def get_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set.")
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_null_author_works(sb, limit=None, offset=0):
    query = (
        sb.table("works")
        .select("id, title, normalized_title, author")
        .is_("author", "null")
        .order("id")
    )
    if limit is not None:
        end = offset + limit - 1
        query = query.range(offset, end)
    resp = query.execute()
    return resp.data or []


def load_resume_ids(csv_paths):
    seen = set()
    for path in csv_paths:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("work_id"):
                    seen.add(int(row["work_id"]))
    return seen


def cmd_propose(args):
    sb = get_supabase()
    works = fetch_null_author_works(sb, limit=args.limit, offset=args.offset)
    if args.resume:
        skip_ids = load_resume_ids(args.resume)
        works = [w for w in works if w["id"] not in skip_ids]

    print(f"Proposing authors for {len(works)} works (author is null).")
    OUT_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = OUT_DIR / f"work_author_proposals_{ts}.csv"

    import requests

    session = requests.Session()
    rows = []
    for i, work in enumerate(works, 1):
        title = work["title"]
        print(f"  [{i}/{len(works)}] {title[:60]}...")
        result = None
        try:
            result = lookup_author(title, session=session)
        except Exception as e:
            print(f"    OL error: {e}")
        ol_author = result["author"] if result else ""
        ol_work_key = result["ol_work_key"] if result else ""
        ol_title = result["ol_title"] if result else ""
        ol_num_docs = result["num_docs"] if result else 0
        approve = ""
        if result and ol_author and titles_match(title, ol_title):
            approve = "y"
        rows.append({
            "work_id": work["id"],
            "title": title,
            "normalized_title": work.get("normalized_title") or "",
            "ol_author": ol_author or "",
            "ol_work_key": ol_work_key or "",
            "ol_title": ol_title or "",
            "ol_num_docs": ol_num_docs,
            "approve": approve,
        })
        time.sleep(random.uniform(0.2, 0.5))

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    auto = sum(1 for r in rows if r["approve"] == "y")
    print(f"\nWrote {len(rows)} proposals to {out_path}")
    print(f"Auto-approved (approve=y): {auto}")
    print("Review the CSV, set approve=y on rows you want applied, then run apply --input ...")


def fetch_existing_work_keys(sb, normalized_title, normalized_author, exclude_id):
    norm_author_key = normalized_author or ""
    resp = (
        sb.table("works")
        .select("id, title, author")
        .eq("normalized_title", normalized_title)
        .execute()
    )
    collisions = []
    for row in resp.data or []:
        if row["id"] == exclude_id:
            continue
        row_author = row.get("author")
        row_norm = normalize_text(row_author) if row_author else ""
        if row_norm == norm_author_key:
            collisions.append(row)
    return collisions


def cmd_apply(args):
    sb = get_supabase()
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: input file not found: {input_path}")
        sys.exit(1)

    with open(input_path, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if (r.get("approve") or "").strip().lower() == "y"]

    if not rows:
        print("No rows with approve=y found in CSV.")
        return

    print(f"Applying {len(rows)} approved author updates...")
    OUT_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    skipped_path = OUT_DIR / f"work_author_apply_skipped_{ts}.csv"

    applied = 0
    skipped = []
    for row in rows:
        work_id = int(row["work_id"])
        author = (row.get("ol_author") or "").strip()
        if not author:
            skipped.append({**row, "reason": "empty ol_author"})
            continue
        normalized_author = normalize_text(author)
        normalized_title = row.get("normalized_title") or normalize_text(row.get("title"))
        ol_work_key = (row.get("ol_work_key") or "").strip() or None

        collisions = fetch_existing_work_keys(sb, normalized_title, normalized_author, work_id)
        if collisions:
            skipped.append({
                **row,
                "reason": f"uniqueness collision with work_id={collisions[0]['id']}",
            })
            continue

        update = {
            "author": author,
            "normalized_author": normalized_author,
        }
        if ol_work_key:
            update["open_library_id"] = ol_work_key

        sb.table("works").update(update).eq("id", work_id).execute()
        applied += 1
        print(f"  Updated work_id={work_id}: {author}")

    if skipped:
        with open(skipped_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = list(CSV_FIELDS) + ["reason"]
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(skipped)
        print(f"\nSkipped {len(skipped)} rows -> {skipped_path}")

    print(f"\nDone. Applied: {applied}, Skipped: {len(skipped)}")


def main():
    parser = argparse.ArgumentParser(description="Backfill works.author from Open Library")
    sub = parser.add_subparsers(dest="command")

    p_propose = sub.add_parser("propose", help="Query OL and write review CSV (default)")
    p_propose.add_argument("--limit", type=int, default=None)
    p_propose.add_argument("--offset", type=int, default=0)
    p_propose.add_argument(
        "--resume",
        nargs="*",
        default=[],
        help="Prior proposal CSV paths; skip work_ids already present",
    )

    p_apply = sub.add_parser("apply", help="Apply reviewed CSV to works table")
    p_apply.add_argument("--input", required=True, help="Reviewed proposals CSV path")

    args = parser.parse_args()
    if args.command == "apply":
        cmd_apply(args)
    else:
        cmd_propose(args)


if __name__ == "__main__":
    main()
