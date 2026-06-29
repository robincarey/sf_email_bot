"""Shared Silver catalog helpers: normalization, work/edition upsert."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from open_library import normalize_text

# Curated author corrections (normalized title -> author). Scraped/OL values must not win.
WORK_AUTHOR_OVERRIDES_BY_NORM_TITLE: dict[str, str] = {
    "green city wars": "Adrian Tchaikovsky",
    "what we eat": "Ryan Rose",
}


def resolve_work_author(title: str | None, scraped_author: str | None = None) -> str | None:
    for variant in title_lookup_variants(title):
        norm = normalize_title(variant)
        if norm and norm in WORK_AUTHOR_OVERRIDES_BY_NORM_TITLE:
            return WORK_AUTHOR_OVERRIDES_BY_NORM_TITLE[norm]
    return scraped_author

_CLEAN_TITLE_PATTERNS = [
    r"\s*-\s*TBB Press Edition.*",
    r"\s*-\s*Slightly Damaged.*",
    r"\s*-\s*Unsigned.*",
    r"\s*-\s*Numbered Edition.*",
    r"\s*-\s*Tier \d+.*",
    r"\s*-\s*EU ONLY.*",
    r"\s*-\s*Indie Endless.*",
    r"\s*with Slipcase.*",
    r"\s*\(\d+(?:st|nd|rd|th) Printing\).*",
    r"\s*;\s*Books \d+.*",
    r"\s*-\s*Leftover.*",
    r"\s*Box Bundle.*",
    r"\s*Deluxe.*",
    r"\s*\d+-pack.*",
    r"\s*Collection.*",
    r"\s*Trilogy.*",
    r"\s*Sequence.*",
    r"\s*Saga.*",
    r"\s*Reprint.*",
    r"\s*Sale.*",
    r"\s*No Dust.*",
]


def normalize_title(title: str | None) -> str | None:
    return normalize_text(title)


def clean_title(title: str | None) -> str | None:
    """Strip retailer/edition suffixes for catalog matching."""
    if not title:
        return None
    t = title
    for pattern in _CLEAN_TITLE_PATTERNS:
        t = re.sub(pattern, "", t, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", t).strip(" -;") or None


def title_lookup_variants(title: str | None) -> list[str]:
    if not title:
        return []
    variants = []
    for candidate in (title, clean_title(title), title.split(";")[0].strip()):
        if candidate and candidate not in variants:
            variants.append(candidate)
    return variants


def normalize_url(link: str | None) -> str | None:
    if not link:
        return None
    return re.sub(r"/+$", "", link.split("?")[0].lower())


def find_work_id(sb, title: str, author: str | None = None):
    """Resolve a work by normalized title + author keys."""
    for variant in title_lookup_variants(title):
        norm_title = normalize_title(variant)
        if not norm_title:
            continue
        norm_author = normalize_title(author) if author else None

        resp = (
            sb.table("works")
            .select("id, author")
            .eq("normalized_title", norm_title)
            .eq("normalized_author", norm_author or "")
            .limit(1)
            .execute()
        )
        if resp.data:
            return resp.data[0]["id"]

        if norm_author:
            resp = (
                sb.table("works")
                .select("id, author")
                .eq("normalized_title", norm_title)
                .is_("normalized_author", "null")
                .limit(1)
                .execute()
            )
            if resp.data:
                return resp.data[0]["id"]

        resp = (
            sb.table("works")
            .select("id, author")
            .eq("normalized_title", norm_title)
            .not_.is_("author", "null")
            .limit(1)
            .execute()
        )
        if len(resp.data or []) == 1:
            return resp.data[0]["id"]

    return None


def ensure_work(sb, title: str, author: str | None = None, open_library_id: str | None = None):
    """Return work id, creating the work when missing."""
    author = resolve_work_author(title, author)
    norm_title = normalize_title(title)
    if not norm_title:
        return None

    existing = find_work_id(sb, title, author)
    if existing:
        if author or open_library_id:
            update = {}
            if author:
                update["author"] = author
                update["normalized_author"] = normalize_title(author)
            if open_library_id:
                update["open_library_id"] = open_library_id
            if update:
                sb.table("works").update(update).eq("id", existing).execute()
        return existing

    norm_author = normalize_title(author) if author else None
    row = {
        "title": title,
        "normalized_title": norm_title,
        "author": author,
        "normalized_author": norm_author,
    }
    if open_library_id:
        row["open_library_id"] = open_library_id

    resp = sb.table("works").insert(row).execute()
    return resp.data[0]["id"] if resp.data else None


def find_edition_id(sb, publisher_id: int, title: str, edition_type: str | None = None):
    norm_title = normalize_title(title)
    if not norm_title:
        return None
    query = (
        sb.table("editions")
        .select("id")
        .eq("publisher_id", publisher_id)
        .eq("normalized_title", norm_title)
    )
    if edition_type:
        query = query.eq("edition_type", edition_type)
    else:
        query = query.is_("edition_type", "null")
    resp = query.limit(1).execute()
    return resp.data[0]["id"] if resp.data else None


def _normalize_isbn(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"[^0-9Xx]", "", value.strip())
    return cleaned or None


def ensure_edition(
    sb,
    *,
    work_id: int,
    publisher_id: int,
    title: str,
    edition_type: str | None = None,
    physical_format: str = "hardcover",
    isbn: str | None = None,
    cover_url: str | None = None,
):
    """Return edition id, creating the edition when missing."""
    isbn = _normalize_isbn(isbn)
    cover_url = (cover_url or "").strip() or None

    existing = find_edition_id(sb, publisher_id, title, edition_type)
    if existing:
        update: dict[str, str] = {}
        if isbn:
            update["isbn"] = isbn
        if cover_url:
            update["cover_url"] = cover_url
        if update:
            sb.table("editions").update(update).eq("id", existing).execute()
        return existing

    norm_title = normalize_title(title)
    if not norm_title:
        return None

    row = {
        "work_id": work_id,
        "publisher_id": publisher_id,
        "title": title,
        "normalized_title": norm_title,
        "physical_format": physical_format,
    }
    if edition_type:
        row["edition_type"] = edition_type
    if isbn:
        row["isbn"] = isbn
    if cover_url:
        row["cover_url"] = cover_url

    resp = sb.table("editions").insert(row).execute()
    return resp.data[0]["id"] if resp.data else None


def ensure_catalog_for_item(
    sb,
    *,
    title: str,
    store: str,
    author: str | None,
    collection_map: dict,
    isbn: str | None = None,
    cover_url: str | None = None,
):
    """Resolve collection, work, and edition for a scraped/catalog item."""
    collection = collection_map.get(store)
    if not collection:
        return None

    work_id = ensure_work(sb, title, author)
    if not work_id:
        return None

    # NOTE: Cover/ISBN enrichment from Open Library is intentionally NOT done here.
    # This runs on every scraped item in the notification-critical path; OL lookups
    # are slow and rate-limited. Cover art is cosmetic and handled offline by
    # scripts/backfill_edition_covers.py. Only persist media the scraper supplied for free.

    edition_id = ensure_edition(
        sb,
        work_id=work_id,
        publisher_id=collection["publisher_id"],
        title=title,
        isbn=isbn,
        cover_url=cover_url,
    )
    if not edition_id:
        return None

    return {
        "collection_id": collection["id"],
        "publisher_id": collection["publisher_id"],
        "work_id": work_id,
        "edition_id": edition_id,
    }


def build_retailer_listing_row(
    *,
    edition_id: int,
    collection_id: int,
    items_seen_id: int,
    link: str,
    in_stock: bool | None,
    price_cents: int | None,
):
    return {
        "edition_id": edition_id,
        "collection_id": collection_id,
        "items_seen_id": items_seen_id,
        "retailer_url": link,
        "retailer_url_normalized": normalize_url(link),
        "in_stock": in_stock,
        "price_cents": price_cents,
        "last_checked": datetime.now(timezone.utc).isoformat(),
    }
