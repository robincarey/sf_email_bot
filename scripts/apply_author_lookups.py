"""One-off: cleaned-title OL lookups + manual overrides for works.author."""

import os
import random
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from open_library import lookup_author, normalize_text, titles_match  # noqa: E402

load_dotenv()

MANUAL = {
    265: "Claire North",
    184: "George R. R. Martin",
    183: "Christopher Ruocchio",
    271: "Christopher Ruocchio",
    78: "Iain Banks",
    158: "Dave Rudden",
    109: "L. D. Lewis",
}

GARBAGE_MARKERS = (
    "log book",
    "dave",
    "klemp",
    "mcalpin",
    "kalman",
    "kidd",
    "pagulayan",
    "manning",
    "lady",
    "sumer",
    "burke library",
)


def clean_title(title: str) -> str:
    t = title
    patterns = [
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
        r"\s*Deluxe \d+-pack.*",
        r"\s*\d+-pack.*",
        r"\s*Collection.*",
        r"\s*Trilogy.*",
        r"\s*Sequence.*",
        r"\s*Saga.*",
        r"\s*Reprint.*",
        r"\s*Sale.*",
    ]
    for pattern in patterns:
        t = re.sub(pattern, "", t, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", t).strip(" -;")


def lookup_best(title: str, session) -> dict | None:
    queries = [clean_title(title), title.split(";")[0].strip(), title]
    seen = set()
    for query in queries:
        if not query or query in seen:
            continue
        seen.add(query)
        result = lookup_author(query, session=session)
        if result and result.get("author"):
            result["query"] = query
            return result
        time.sleep(0.15)
    return None


def main():
    sb = create_client(
        os.environ["SUPABASE_URL"],
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"],
    )
    session = requests.Session()

    def update_work(work_id, author, ol_work_key=None):
        normalized_author = normalize_text(author)
        work = sb.table("works").select("normalized_title").eq("id", work_id).single().execute().data
        payload = {"author": author, "normalized_author": normalized_author}
        if ol_work_key:
            payload["open_library_id"] = ol_work_key
        sb.table("works").update(payload).eq("id", work_id).execute()

    print("Manual overrides:")
    for work_id, author in MANUAL.items():
        update_work(work_id, author)
        print(f"  {work_id}: {author}")

    nulls = (
        sb.table("works")
        .select("id, title")
        .is_("author", "null")
        .order("id")
        .execute()
        .data
        or []
    )
    print(f"\nOL lookup for {len(nulls)} null-author works:")
    applied = 0
    for i, work in enumerate(nulls, 1):
        result = lookup_best(work["title"], session)
        if not result:
            print(f"  [{i}] {work['title'][:50]} -> no hit")
            time.sleep(random.uniform(0.2, 0.35))
            continue
        author = result["author"]
        match = titles_match(work["title"], result.get("ol_title")) or titles_match(
            result["query"], result.get("ol_title")
        )
        update_work(work["id"], author, result.get("ol_work_key"))
        applied += 1
        print(f"  [{i}] {work['title'][:45]} -> {author} (match={match}, q={result['query'][:30]})")
        time.sleep(random.uniform(0.2, 0.35))

    questionable = (
        sb.table("works")
        .select("id, title, author")
        .not_.is_("author", "null")
        .execute()
        .data
        or []
    )
    print("\nRe-checking suspicious authors:")
    fixed = 0
    for work in questionable:
        if work["id"] in MANUAL:
            continue
        old = work.get("author") or ""
        if not any(marker in old.lower() for marker in GARBAGE_MARKERS):
            continue
        result = lookup_best(work["title"], session)
        if not result or result["author"] == old:
            continue
        match = titles_match(work["title"], result.get("ol_title")) or titles_match(
            result["query"], result.get("ol_title")
        )
        if match:
            update_work(work["id"], result["author"], result.get("ol_work_key"))
            fixed += 1
            print(f"  {work['id']} {work['title'][:40]}: {old[:25]} -> {result['author']}")
        time.sleep(random.uniform(0.2, 0.35))

    null_left = sb.table("works").select("id", count="exact").is_("author", "null").execute().count
    filled = sb.table("works").select("id", count="exact").not_.is_("author", "null").execute().count
    print(f"\nApplied from nulls: {applied}, fixed suspicious: {fixed}")
    print(f"Author set: {filled} | null remaining: {null_left}")


if __name__ == "__main__":
    main()
