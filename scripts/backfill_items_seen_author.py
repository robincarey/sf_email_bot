"""
Backfill items_seen.author from linked works (via editions/retailer_listings or title match).

Usage:
  python scripts/backfill_items_seen_author.py          # dry run
  python scripts/backfill_items_seen_author.py --apply
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from silver_catalog import find_work_id, normalize_title  # noqa: E402

load_dotenv()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    sb = create_client(
        os.environ["SUPABASE_URL"],
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"],
    )

    items = (
        sb.table("items_seen")
        .select("id, name, author")
        .is_("author", "null")
        .execute()
        .data
        or []
    )
    print(f"items_seen without author: {len(items)}")

    updates = []
    for item in items:
        work_id = find_work_id(sb, item["name"])
        if not work_id:
            continue
        resp = sb.table("works").select("author").eq("id", work_id).limit(1).execute()
        author = (resp.data or [{}])[0].get("author")
        if author:
            updates.append({"id": item["id"], "name": item["name"], "author": author})

    print(f"Resolvable from works: {len(updates)}")
    for u in updates[:10]:
        print(f"  {u['name'][:50]} -> {u['author']}")

    if not args.apply:
        print("\nDry run. Pass --apply to write.")
        return

    for u in updates:
        sb.table("items_seen").update({"author": u["author"]}).eq("id", u["id"]).execute()

    remaining = (
        sb.table("items_seen")
        .select("id", count="exact")
        .is_("author", "null")
        .execute()
        .count
    )
    print(f"\nApplied {len(updates)} updates. items_seen author still null: {remaining}")


if __name__ == "__main__":
    main()
