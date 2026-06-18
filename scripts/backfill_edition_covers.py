"""Backfill editions.cover_url and editions.isbn from Shopify, with Open Library fallback."""

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

from open_library import lookup_metadata  # noqa: E402
from scrapers.broken_binding_sf import (  # noqa: E402
    cover_and_isbn_from_shopify_json,
    extract_isbn_from_html,
)

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


def fetch_shopify_html(session: requests.Session, url: str) -> str | None:
    for attempt in range(4):
        try:
            resp = session.get(url.rstrip("/"), headers={"User-Agent": UA}, timeout=20)
            if resp.status_code == 429 or resp.status_code >= 500:
                time.sleep(2 ** attempt + random.uniform(0, 1))
                continue
            resp.raise_for_status()
            return resp.text
        except requests.RequestException:
            if attempt == 3:
                return None
            time.sleep(2 ** attempt + random.uniform(0, 1))
    return None


def load_edition_meta(sb, edition_ids: list[int]) -> dict[int, dict]:
    if not edition_ids:
        return {}
    meta: dict[int, dict] = {}
    chunk_size = 100
    for start in range(0, len(edition_ids), chunk_size):
        chunk = edition_ids[start : start + chunk_size]
        resp = (
            sb.table("editions")
            .select("id, isbn, cover_url, title, works(open_library_id, title)")
            .in_("id", chunk)
            .execute()
        )
        for row in resp.data or []:
            work = row.get("works") or {}
            meta[row["id"]] = {
                "title": row.get("title") or work.get("title"),
                "open_library_id": work.get("open_library_id"),
                "isbn": row.get("isbn"),
                "cover_url": row.get("cover_url"),
            }
    return meta


def apply_ol_fallback(
    session: requests.Session,
    *,
    title: str | None,
    open_library_id: str | None,
    cover_url: str | None,
    isbn: str | None,
) -> tuple[str | None, str | None, bool]:
    if cover_url and isbn:
        return cover_url, isbn, False
    try:
        meta = lookup_metadata(title=title, ol_work_key=open_library_id, session=session)
    except Exception as exc:
        print(f"OL lookup failed for {title!r}: {exc}", flush=True)
        return cover_url, isbn, False
    if not meta:
        return cover_url, isbn, False
    used = False
    if not isbn and meta.get("isbn"):
        isbn = meta["isbn"]
        used = True
    if not cover_url and meta.get("cover_url"):
        cover_url = meta["cover_url"]
        used = True
    return cover_url, isbn, used


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print updates without writing")
    parser.add_argument("--limit", type=int, default=0, help="Max listings to process (0 = all)")
    parser.add_argument("--edition-id", type=int, action="append", default=[], help="Only these edition IDs")
    parser.add_argument("--url", action="append", default=[], help="Only listings matching these URLs")
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

    if args.url:
        allowed = {u.rstrip("/") for u in args.url}
        listings = [row for row in listings if row["retailer_url"].rstrip("/") in allowed]

    if args.edition_id:
        allowed_ids = set(args.edition_id)
        listings = [row for row in listings if row["edition_id"] in allowed_ids]

    if args.limit:
        listings = listings[: args.limit]

    print(f"Found {len(listings)} Broken Binding retailer listings", flush=True)

    edition_ids = sorted({row["edition_id"] for row in listings})
    edition_meta = load_edition_meta(sb, edition_ids)

    session = requests.Session()
    updated = 0
    skipped = 0
    failed = 0
    ol_fallback = 0

    seen_editions: set[int] = set()

    for row in listings:
        edition_id = row["edition_id"]
        if edition_id in seen_editions:
            continue
        seen_editions.add(edition_id)

        link = row["retailer_url"]
        meta = edition_meta.get(edition_id, {})
        cover_url = meta.get("cover_url")
        isbn = meta.get("isbn")

        product_data = fetch_shopify_product(session, link)
        if product_data:
            shop_cover, shop_isbn = cover_and_isbn_from_shopify_json(product_data)
            if shop_cover:
                cover_url = shop_cover
            if shop_isbn:
                isbn = shop_isbn
            if not isbn:
                html = fetch_shopify_html(session, link)
                if html:
                    from bs4 import BeautifulSoup

                    isbn = extract_isbn_from_html(BeautifulSoup(html, "html.parser"))
        else:
            print(f"Shopify FAIL {link}", flush=True)

        cover_url, isbn, used_ol = apply_ol_fallback(
            session,
            title=meta.get("title"),
            open_library_id=meta.get("open_library_id"),
            cover_url=cover_url,
            isbn=isbn,
        )
        if used_ol:
            ol_fallback += 1

        payload: dict[str, str] = {}
        if cover_url and cover_url != meta.get("cover_url"):
            payload["cover_url"] = cover_url
        if isbn and isbn != meta.get("isbn"):
            payload["isbn"] = isbn

        if not payload:
            if not product_data and not used_ol:
                failed += 1
            else:
                skipped += 1
            time.sleep(random.uniform(0.15, 0.35))
            continue

        source = "OL" if used_ol and not product_data else ("OL+shop" if used_ol else "shop")
        print(
            f"{'DRY ' if args.dry_run else ''}edition {edition_id} ({source}): {payload}",
            flush=True,
        )

        if not args.dry_run:
            sb.table("editions").update(payload).eq("id", edition_id).execute()

        updated += 1
        time.sleep(random.uniform(0.2, 0.5))

    print(
        f"Done. updated={updated} skipped={skipped} failed={failed} ol_fallback={ol_fallback}",
        flush=True,
    )


if __name__ == "__main__":
    main()
