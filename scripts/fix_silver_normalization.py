"""
Repair corrupted normalized_title / normalized_author on works and editions.

The initial backfill used a broken Postgres regexp that stripped the first
character of each word. This script recomputes keys using silver_catalog.normalize_title.

Usage:
  python scripts/fix_silver_normalization.py          # dry run
  python scripts/fix_silver_normalization.py --apply
"""

import argparse
import os
import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from silver_catalog import normalize_title  # noqa: E402

load_dotenv()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    sb = create_client(
        os.environ["SUPABASE_URL"],
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ["SUPABASE_KEY"],
    )

    works = sb.table("works").select("id, title, author, normalized_title, normalized_author").execute().data or []
    editions = (
        sb.table("editions")
        .select("id, title, normalized_title, work_id, publisher_id, edition_type")
        .execute()
        .data
        or []
    )

    work_updates = []
    for w in works:
        new_title = normalize_title(w["title"])
        new_author = normalize_title(w.get("author")) if w.get("author") else None
        if new_title != w.get("normalized_title") or new_author != w.get("normalized_author"):
            work_updates.append({
                "id": w["id"],
                "normalized_title": new_title,
                "normalized_author": new_author,
            })

    edition_updates = []
    for e in editions:
        new_title = normalize_title(e["title"])
        if new_title != e.get("normalized_title"):
            edition_updates.append({"id": e["id"], "normalized_title": new_title})

    work_key_collisions = defaultdict(list)
    for w in works:
        wid = w["id"]
        upd = next((u for u in work_updates if u["id"] == wid), None)
        norm_title = upd["normalized_title"] if upd else w.get("normalized_title")
        norm_author = upd["normalized_author"] if upd else w.get("normalized_author")
        work_key_collisions[(norm_title, norm_author or "")].append(wid)

    work_collisions = {k: v for k, v in work_key_collisions.items() if len(v) > 1}
    edition_key_collisions = defaultdict(list)
    for e in editions:
        eid = e["id"]
        upd = next((u for u in edition_updates if u["id"] == eid), None)
        norm_title = upd["normalized_title"] if upd else e.get("normalized_title")
        edition_key_collisions[
            (e["work_id"], e["publisher_id"], norm_title, e.get("edition_type") or "")
        ].append(eid)
    edition_collisions = {k: v for k, v in edition_key_collisions.items() if len(v) > 1}

    print(f"Works to update: {len(work_updates)} / {len(works)}")
    print(f"Editions to update: {len(edition_updates)} / {len(editions)}")
    print(f"Work key collisions after fix: {len(work_collisions)}")
    print(f"Edition key collisions after fix: {len(edition_collisions)}")

    if work_collisions:
        print("\nWork collisions (need manual merge):")
        for key, ids in list(work_collisions.items())[:10]:
            print(f"  {key}: work_ids={ids}")

    if edition_collisions:
        print("\nEdition collisions (need manual merge):")
        for key, ids in list(edition_collisions.items())[:10]:
            print(f"  {key}: edition_ids={ids}")

    if not args.apply:
        print("\nDry run. Pass --apply to write changes.")
        return

    if work_collisions or edition_collisions:
        print("\nRefusing to apply while uniqueness collisions exist.")
        sys.exit(1)

    for u in work_updates:
        sb.table("works").update({
            "normalized_title": u["normalized_title"],
            "normalized_author": u["normalized_author"],
        }).eq("id", u["id"]).execute()

    for u in edition_updates:
        sb.table("editions").update({
            "normalized_title": u["normalized_title"],
        }).eq("id", u["id"]).execute()

    print("\nApplied normalization fixes.")


if __name__ == "__main__":
    main()
