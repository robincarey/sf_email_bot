"""
Backfill retailer_listings (and missing works/editions) from items_seen.

Usage:
  python scripts/backfill_retailer_listings.py          # dry run
  python scripts/backfill_retailer_listings.py --apply
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from silver_catalog import (  # noqa: E402
    build_retailer_listing_row,
    ensure_catalog_for_item,
    find_edition_id,
    find_work_id,
    normalize_title,
)

load_dotenv()


def load_collection_map(sb):
    resp = sb.table("collections").select("id, store_name, publisher_id").execute()
    return {r["store_name"]: r for r in (resp.data or [])}


def author_for_item(sb, title: str, item_author: str | None):
    if item_author:
        return item_author
    work_id = find_work_id(sb, title)
    if not work_id:
        return None
    resp = sb.table("works").select("author").eq("id", work_id).limit(1).execute()
    return (resp.data or [{}])[0].get("author")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    sb = create_client(
        os.environ["SUPABASE_URL"],
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"],
    )

    collection_map = load_collection_map(sb)
    items = (
        sb.table("items_seen")
        .select("id, name, store, link, in_stock, typed_price_cents, author")
        .not_.is_("link", "null")
        .execute()
        .data
        or []
    )
    existing = {
        r["items_seen_id"]
        for r in (sb.table("retailer_listings").select("items_seen_id").execute().data or [])
        if r.get("items_seen_id")
    }

    to_process = [i for i in items if i["id"] not in existing]
    print(f"items_seen with link: {len(items)}")
    print(f"already listed: {len(existing)}")
    print(f"to backfill: {len(to_process)}")

    rows = []
    skipped = []
    for item in to_process:
        title = item.get("name")
        store = item.get("store")
        link = item.get("link")
        if not title or not store or not link:
            skipped.append((item["id"], "missing fields"))
            continue

        author = author_for_item(sb, title, item.get("author"))
        if not args.apply:
            collection = collection_map.get(store)
            if not collection:
                skipped.append((item["id"], f"no collection for {store}"))
                continue
            edition_id = find_edition_id(sb, collection["publisher_id"], title)
            if edition_id:
                rows.append(item["id"])
            else:
                work_id = find_work_id(sb, title, author)
                skipped.append((item["id"], f"would create work={not work_id}"))
                rows.append(item["id"])
            continue

        resolved = ensure_catalog_for_item(
            sb, title=title, store=store, author=author, collection_map=collection_map
        )
        if not resolved:
            skipped.append((item["id"], f"catalog resolve failed ({store})"))
            continue

        rows.append(
            build_retailer_listing_row(
                edition_id=resolved["edition_id"],
                collection_id=resolved["collection_id"],
                items_seen_id=item["id"],
                link=link,
                in_stock=item.get("in_stock"),
                price_cents=item.get("typed_price_cents"),
            )
        )

    if not args.apply:
        print(f"Would upsert {len(rows)} retailer_listings; skipped {len(skipped)}")
        for sid, reason in skipped[:15]:
            print(f"  skip {sid}: {reason}")
        print("\nDry run. Pass --apply to write.")
        return

    if not rows:
        print("Nothing to upsert.")
        return

    batch_size = 50
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        sb.table("retailer_listings").upsert(
            batch, on_conflict="collection_id,retailer_url_normalized"
        ).execute()
        print(f"  upserted {min(i + batch_size, len(rows))}/{len(rows)}")

    print(f"\nDone. Upserted {len(rows)}, skipped {len(skipped)}")


if __name__ == "__main__":
    main()
