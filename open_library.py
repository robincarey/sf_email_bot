import random
import re
import time

import requests

OL_SEARCH = "https://openlibrary.org/search.json"
UA = "sf_bot-author-backfill/1.0"


def normalize_text(value):
    """Match Postgres: lower(regexp_replace(trim(x), '[^a-z0-9]+', ' ', 'g'))."""
    if not value:
        return None
    cleaned = re.sub(r"[^a-z0-9]+", " ", (value or "").strip().lower())
    return re.sub(r"\s+", " ", cleaned).strip() or None


def lookup_author(title, session=None):
    """Look up author and Open Library work key by title."""
    s = session or requests
    for attempt in range(4):
        try:
            resp = s.get(
                OL_SEARCH,
                params={"title": title, "limit": 1},
                headers={"User-Agent": UA},
                timeout=15,
            )
            if resp.status_code == 429 or resp.status_code >= 500:
                wait = 2 ** attempt + random.uniform(0, 1)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            docs = resp.json().get("docs") or []
            if not docs:
                return None
            doc = docs[0]
            authors = doc.get("author_name") or []
            return {
                "author": authors[0] if authors else None,
                "ol_work_key": doc.get("key"),
                "ol_title": doc.get("title"),
                "num_docs": len(docs),
            }
        except requests.RequestException:
            if attempt == 3:
                raise
            wait = 2 ** attempt + random.uniform(0, 1)
            time.sleep(wait)
    return None


def titles_match(work_title, ol_title):
    """Simple normalized title equality for auto-approve."""
    a = normalize_text(work_title)
    b = normalize_text(ol_title)
    if not a or not b:
        return False
    return a == b or a in b or b in a
