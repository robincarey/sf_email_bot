import random
import re
import time

import requests

OL_SEARCH = "https://openlibrary.org/search.json"
UA = "sf_bot-author-backfill/1.0"

ISBN_RE = re.compile(
    r"(?:ISBN(?:-1[03])?:?\s*)?((?:97[89][\-\s]?)?(?:\d[\-\s]?){9}[\dXx])",
    re.IGNORECASE,
)


def normalize_text(value):
    """Match Postgres: lower(regexp_replace(trim(x), '[^a-z0-9]+', ' ', 'g'))."""
    if not value:
        return None
    cleaned = re.sub(r"[^a-z0-9]+", " ", (value or "").strip().lower())
    return re.sub(r"\s+", " ", cleaned).strip() or None


def normalize_isbn(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"[^0-9Xx]", "", value.strip())
    if len(cleaned) not in (10, 13):
        return None
    return cleaned.upper() if len(cleaned) == 10 and cleaned[-1] in "Xx" else cleaned


def normalize_ol_work_key(value: str | None) -> str | None:
    if not value:
        return None
    key = value.strip().replace("/works/", "")
    return key or None


def extract_isbn_from_text(text: str | None) -> str | None:
    if not text:
        return None
    for match in ISBN_RE.finditer(text):
        isbn = normalize_isbn(match.group(1))
        if isbn:
            return isbn
    return None


def ol_cover_url_by_isbn(isbn: str, size: str = "M") -> str:
    cleaned = normalize_isbn(isbn) or ""
    return f"https://covers.openlibrary.org/b/isbn/{cleaned}-{size}.jpg"


def ol_cover_url_by_olid(ol_work_key: str, size: str = "M") -> str:
    olid = normalize_ol_work_key(ol_work_key)
    if not olid:
        return ""
    return f"https://covers.openlibrary.org/b/olid/{olid}-{size}.jpg"


def _search_docs(params: dict, session) -> list[dict]:
    for attempt in range(4):
        try:
            resp = session.get(
                OL_SEARCH,
                params=params,
                headers={"User-Agent": UA},
                timeout=15,
            )
            if resp.status_code == 429 or resp.status_code >= 500:
                time.sleep(2 ** attempt + random.uniform(0, 1))
                continue
            resp.raise_for_status()
            return resp.json().get("docs") or []
        except requests.RequestException:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt + random.uniform(0, 1))
    return []


def _pick_isbn_from_doc(doc: dict) -> str | None:
    for field in ("isbn_13", "isbn"):
        for value in doc.get(field) or []:
            isbn = normalize_isbn(str(value))
            if isbn:
                return isbn
    return None


def lookup_author(title, session=None):
    """Look up author and Open Library work key by title."""
    s = session or requests
    docs = _search_docs({"title": title, "limit": 1}, s)
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


def lookup_metadata(
    *,
    title: str | None = None,
    ol_work_key: str | None = None,
    session=None,
) -> dict | None:
    """Resolve ISBN and a covers.openlibrary.org URL from OL search."""
    s = session or requests
    doc = None

    norm_key = normalize_ol_work_key(ol_work_key)
    if norm_key:
        docs = _search_docs({"q": f"key:/works/{norm_key}", "limit": 1}, s)
        doc = docs[0] if docs else None

    if not doc and title:
        docs = _search_docs({"title": title, "limit": 1}, s)
        doc = docs[0] if docs else None

    if not doc:
        return None

    isbn = _pick_isbn_from_doc(doc)
    work_key = doc.get("key") or (f"/works/{norm_key}" if norm_key else None)
    cover_url = None
    if work_key:
        cover_url = ol_cover_url_by_olid(work_key)
    if not cover_url and isbn:
        cover_url = ol_cover_url_by_isbn(isbn)

    return {
        "isbn": isbn,
        "cover_url": cover_url or None,
        "ol_work_key": work_key,
        "ol_title": doc.get("title"),
    }


def titles_match(work_title, ol_title):
    """Simple normalized title equality for auto-approve."""
    a = normalize_text(work_title)
    b = normalize_text(ol_title)
    if not a or not b:
        return False
    return a == b or a in b or b in a
