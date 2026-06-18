"""Backfill editions.cover_url and editions.isbn from Broken Binding Shopify .json."""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scrapers.broken_binding_sf import cover_and_isbn_from_shopify_json  # noqa: E402

load_dotenv()

BB_HOST = "thebrokenbindingsub.com"
UA = "sf_bot-cover-backfill/1.0"


def fetch_shopify_product(session: requests.Session, url: str) -> dict | None:
    json_url = url.rstrip("/") + ".json"
    for attempt in range(4):
        try:
            resp = session.get(json_url, headers={"User-Agent": UA}, timeout=20)
            if resp.status_code == 429 or resp.status_code >= 500:
                time.sleep(2 ** attempt + random.uniform(0, 1))
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            if attempt == 3:
                return None
            time.sleep(2 ** attempt + random.uniform(0, 1))
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print updates without writing")
    parser.add_argument("--limit", type=int, default=0, help="Max listings to process (0 = all)")
    args = parser.parse_args()

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise SystemExit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY) required")

    sb = create_client(url, key)

    listings: list[dict] = []
    offset = 0
    page_size = 500
    while True:
        resp = (
            sb.table("retailer_listings")
            .select("id, edition_id, retailer_url")
            .ilike("retailer_url", f"%{BB_HOST}%")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        batch = resp.data or []
        listings.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size

    if args.limit:
        listings = listings[: args.limit]

    print(f"Found {len(listings)} Broken Binding retailer listings")

    session = requests.Session()
    updated = 0
    skipped = 0
    failed = 0

    seen_editions: set[int] = set()

    for row in listings:
        edition_id = row["edition_id"]
        if edition_id in seen_editions:
            continue
        seen_editions.add(edition_id)

        link = row["retailer_url"]
        product_data = fetch_shopify_product(session, link)
        if not product_data:
            print(f"FAIL {link}")
            failed += 1
            time.sleep(random.uniform(0.3, 0.6))
            continue

        cover_url, isbn = cover_and_isbn_from_shopify_json(product_data)
        if not cover_url and not isbn:
            skipped += 1
            time.sleep(random.uniform(0.2, 0.4))
            continue

        payload: dict[str, str] = {}
        if cover_url:
            payload["cover_url"] = cover_url
        if isbn:
            payload["isbn"] = isbn

        print(f"{'DRY ' if args.dry_run else ''}edition {edition_id}: {payload}")

        if not args.dry_run:
            sb.table("editions").update(payload).eq("id", edition_id).execute()

        updated += 1
        time.sleep(random.uniform(0.2, 0.5))

    print(f"Done. updated={updated} skipped={skipped} failed={failed}")


if __name__ == "__main__":
    main()
