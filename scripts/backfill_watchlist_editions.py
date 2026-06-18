"""
Backfill watchlist.edition_id from retailer_listings.items_seen_id.

Usage:
  python scripts/backfill_watchlist_editions.py          # dry run
  python scripts/backfill_watchlist_editions.py --apply
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    sb = create_client(
        os.environ["SUPABASE_URL"],
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"],
    )

    watchlist = (
        sb.table("watchlist")
        .select("id, user_id, item_id, edition_id")
        .execute()
        .data
        or []
    )
    listings = (
        sb.table("retailer_listings")
        .select("items_seen_id, edition_id")
        .execute()
        .data
        or []
    )
    edition_by_item = {
        r["items_seen_id"]: r["edition_id"]
        for r in listings
        if r.get("items_seen_id") and r.get("edition_id")
    }

    to_update = []
    to_delete = []
    skipped = []
    groups = {}
    for row in watchlist:
        edition_id = row.get("edition_id") or edition_by_item.get(row["item_id"])
        if not edition_id:
            skipped.append(row)
            continue
        groups.setdefault((row["user_id"], edition_id), []).append(row)

    for (_user_id, edition_id), rows in groups.items():
        with_edition = [r for r in rows if r.get("edition_id")]
        keeper = with_edition[0] if with_edition else rows[0]
        for row in rows:
            if row["id"] != keeper["id"]:
                to_delete.append(row["id"])
        if not keeper.get("edition_id"):
            to_update.append({"id": keeper["id"], "edition_id": edition_id})

    print(f"watchlist rows: {len(watchlist)}")
    print(f"already have edition_id: {sum(1 for r in watchlist if r.get('edition_id'))}")
    print(f"to backfill: {len(to_update)}")
    print(f"duplicate rows to remove: {len(to_delete)}")
    print(f"unmapped item_id: {len(skipped)}")

    if not args.apply:
        print("\nDry run. Pass --apply to write.")
        return

    for row_id in to_delete:
        sb.table("watchlist").delete().eq("id", row_id).execute()

    for row in to_update:
        sb.table("watchlist").update({"edition_id": row["edition_id"]}).eq("id", row["id"]).execute()

    remaining = (
        sb.table("watchlist")
        .select("id", count="exact")
        .is_("edition_id", "null")
        .execute()
        .count
    )
    print(f"\nApplied {len(to_update)} updates. edition_id still null: {remaining}")


if __name__ == "__main__":
    main()
