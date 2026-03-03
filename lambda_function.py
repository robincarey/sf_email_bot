import json
import os
import re
import uuid
import logging
from supabase import create_client
from broken_binding_sf import broken_binding_checks
from email_notifier import send_email

logger = logging.getLogger()
logger.setLevel(logging.INFO)

run_mode = os.getenv('RUN_MODE', 'prod').lower()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

_supabase_client = None

def get_supabase():
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client


def parse_price_cents(price_str):
    """Parse a price string like '$10.99' or '£24.99' to integer cents."""
    cleaned = re.sub(r"[^\d.]", "", price_str or "")
    try:
        return int(round(float(cleaned) * 100))
    except (ValueError, TypeError):
        return None


def get_recipients_for_run(run_id):
    """Return list of {"id": uuid|None, "email": str} dicts."""
    if run_mode == "prod":
        try:
            response = (
                get_supabase()
                .table("users")
                .select("id, email")
                .eq("is_active", True)
                .execute()
            )
            recips = [{"id": r["id"], "email": r["email"]} for r in (response.data or [])]
            logger.info(f"[{run_id}] RUN_MODE=prod recipients from supabase (count={len(recips)})")
        except Exception as e:
            logger.error(f"[{run_id}] Error loading recipients from Supabase: {e}")
            recips = []
    else:
        emails = sorted(set(json.loads(os.getenv("ADMIN_EMAILS", "[]"))))
        recips = []
        if emails:
            try:
                response = (
                    get_supabase()
                    .table("users")
                    .select("id, email")
                    .in_("email", list(emails))
                    .execute()
                )
                email_to_id = {r["email"]: r["id"] for r in (response.data or [])}
            except Exception as e:
                logger.error(f"[{run_id}] Error looking up admin user IDs: {e}")
                email_to_id = {}
            recips = [{"id": email_to_id.get(e), "email": e} for e in emails]
        logger.info(f"[{run_id}] RUN_MODE=dev admin emails (count={len(recips)})")
    return recips


def load_seen_items(run_id):
    try:
        response = (
            get_supabase()
            .table("items_seen")
            .select("name, price, store, link, in_stock")
            .execute()
        )
        items = response.data or []
        logger.info(f"[{run_id}] Loaded {len(items)} seen items from Supabase.")
        return items
    except Exception as e:
        logger.error(f"[{run_id}] Error loading seen items from Supabase: {e}")
        return []


def save_seen_items(items, run_id):
    if not items:
        return
    try:
        get_supabase().table("items_seen").upsert(items, on_conflict="link").execute()
        logger.info(f"[{run_id}] Upserted {len(items)} items into items_seen.")
    except Exception as e:
        logger.error(f"[{run_id}] Error saving to Supabase: {e}")


def fetch_item_ids_by_link(links, run_id):
    if not links:
        return {}
    try:
        resp = (
            get_supabase()
            .table("items_seen")
            .select("id, link")
            .in_("link", list(links))
            .execute()
        )
        rows = resp.data or []
        logger.info(f"[{run_id}] Fetched {len(rows)} item IDs by link.")
        return {r["link"]: r["id"] for r in rows}
    except Exception as e:
        logger.error(f"[{run_id}] Error fetching item ids by link: {e}")
        return {}


def insert_events(event_rows, run_id):
    """Insert event rows and return the inserted rows (with generated IDs)."""
    if not event_rows:
        return []
    for row in event_rows:
        row["run_id"] = run_id
    try:
        resp = get_supabase().table("item_events").insert(event_rows).execute()
        inserted = resp.data or []
        logger.info(f"[{run_id}] Inserted {len(inserted)} rows into item_events.")
        return inserted
    except Exception as e:
        logger.error(f"[{run_id}] Error inserting item_events: {e}")
        return []


def insert_email_log(log_rows, run_id):
    """Insert email_log rows and return inserted rows with generated IDs."""
    if not log_rows:
        return []
    try:
        resp = get_supabase().table("email_log").insert(log_rows).execute()
        inserted = resp.data or []
        logger.info(f"[{run_id}] Inserted {len(inserted)} email_log rows.")
        return inserted
    except Exception as e:
        logger.error(f"[{run_id}] Error inserting email_log: {e}")
        return []


def insert_email_log_events(rows, run_id):
    """Insert email_log_events junction rows."""
    if not rows:
        return
    try:
        get_supabase().table("email_log_events").insert(rows).execute()
        logger.info(f"[{run_id}] Inserted {len(rows)} email_log_events rows.")
    except Exception as e:
        logger.error(f"[{run_id}] Error inserting email_log_events: {e}")


def check_for_updates():
    run_id = str(uuid.uuid4())
    logger.info(f"[{run_id}] Starting update check.")

    recipients = get_recipients_for_run(run_id)
    seen_items = load_seen_items(run_id)
    seen_items_dict = {
        item['link']: {k: v for k, v in item.items() if k != 'link'}
        for item in seen_items
    }

    new_items = broken_binding_checks()
    if not new_items:
        logger.warning(f"[{run_id}] Scraper returned no items; skipping diff and upsert.")
        return

    seen_set = {frozenset(s.items()) for s in seen_items}
    new_set = {frozenset(n.items()) for n in new_items}
    unseen_items_set = new_set.difference(seen_set)
    unseen_items = [dict(x) for x in unseen_items_set]

    # Single sweep: classify changes, build event rows, annotate books for email
    events = []
    for book in unseen_items:
        prev = seen_items_dict.get(book["link"])

        if prev is None:
            if book.get("in_stock"):
                event_type = "New Item"
            else:
                event_type = "New Item - Out of Stock"
            old_value = None
            new_value = None

        elif book.get("in_stock") and not prev.get("in_stock"):
            event_type = "Restocked"
            old_value = "out_of_stock"
            new_value = "in_stock"

        elif not book.get("in_stock") and prev.get("in_stock"):
            event_type = "Out of Stock"
            old_value = "in_stock"
            new_value = "out_of_stock"

        elif book.get("price") != prev.get("price"):
            event_type = "Price Change"
            old_value = prev.get("price")
            new_value = book.get("price")

        elif book.get("store") != prev.get("store"):
            event_type = "Store Change"
            old_value = prev.get("store")
            new_value = book.get("store")

        else:
            event_type = "Unknown Change"
            old_value = None
            new_value = None

        book["event_type"] = event_type

        # Intermediate structure; link is used to resolve item_id, not stored in DB
        events.append({
            "link": book["link"],
            "event_type": event_type,
            "old_value": old_value,
            "new_value": new_value,
        })

    logger.info(f"[{run_id}] Found {len(unseen_items)} changed items, {len(events)} events.")

    # Attach typed_price_cents before upserting
    for item in new_items:
        item["typed_price_cents"] = parse_price_cents(item.get("price"))

    # Step 1: Upsert items_seen so IDs exist for new items
    save_seen_items(new_items, run_id)

    # Step 2: Fetch IDs for changed items
    changed_links = list({e["link"] for e in events})
    link_to_id = fetch_item_ids_by_link(changed_links, run_id)

    # Step 3: Insert item_events
    event_rows = []
    for e in events:
        item_id = link_to_id.get(e["link"])
        if not item_id:
            logger.warning(f"[{run_id}] No item_id found for link {e['link']}; skipping event.")
            continue
        event_rows.append({
            "item_id": item_id,
            "event_type": e["event_type"],
            "old_value": e.get("old_value"),
            "new_value": e.get("new_value"),
        })
    inserted_events = insert_events(event_rows, run_id)

    # Step 4: Send emails for in-stock items only
    items_to_email = [i for i in unseen_items if i.get("in_stock")]

    if not recipients:
        logger.info(f"[{run_id}] No recipients found; skipping email send.")
        logger.info(f"[{run_id}] Update check complete.")
        return
    if not items_to_email:
        logger.info(f"[{run_id}] No in-stock items to email; skipping email send.")
        logger.info(f"[{run_id}] Update check complete.")
        return

    # Determine which event IDs correspond to emailed (in-stock) items
    emailed_item_ids = {link_to_id[item["link"]] for item in items_to_email if item["link"] in link_to_id}
    emailed_event_ids = [evt["id"] for evt in inserted_events if evt["item_id"] in emailed_item_ids]

    email_subject = "New Broken Binding Books Available!"
    html_table = f"""
    <style>
        @media only screen and (max-width: 600px) {{
            table {{
                width: 100%;
            }}
            th, td {{
                padding: 10px !important;
                font-size: 14px !important;
            }}
        }}
        table {{
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
        }}
    </style>
    <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; border-bottom: 1px solid #ddd;">
        <thead style="background-color: #f2f2f2;">
            <tr>
                <th style="padding: 8px; text-align: left;">Item Name</th>
                <th style="padding: 8px; text-align: left;">Price</th>
                <th style="padding: 8px; text-align: left;">Store</th>
                <th style="padding: 8px; text-align: left;">Update Type</th>
            </tr>
        </thead>
        <tbody>
            {''.join(f"<tr style='border-bottom: 1px solid #ddd;'>"
                    f"<td style='padding: 8px;'><a href='{item['link']}'>"
                    f"{item['name']}</a></td>"
                    f"<td style='padding: 8px;'>{item['price']}</td>"
                    f"<td style='padding: 8px;'>{item['store']}</td>"
                    f"<td style='padding: 8px;'>{item['event_type']}</td>"
                    f"</tr>"
                    for item in items_to_email)
            }
        </tbody>
    </table>
    """
    message = f"""
    <html>
    <body>
        <p>New book(s) available:</p>
        {html_table}
    </body>
    </html>
    """

    # Send emails, tracking per-recipient success/failure
    email_results = []
    for recip in recipients:
        try:
            send_email(email_subject, message, recip["email"])
            email_results.append({"user_id": recip["id"], "success": True, "error_message": None})
        except Exception as e:
            logger.error(f"[{run_id}] Failed to send email to {recip['email']}: {e}")
            email_results.append({"user_id": recip["id"], "success": False, "error_message": str(e)})

    sent_count = sum(1 for r in email_results if r["success"])
    logger.info(f"[{run_id}] Emails sent: {sent_count}/{len(email_results)}.")

    # Step 5: Batch insert email_log rows
    log_rows = [{
        "user_id": r["user_id"],
        "run_id": run_id,
        "subject": email_subject,
        "success": r["success"],
        "error_message": r["error_message"],
    } for r in email_results]
    inserted_logs = insert_email_log(log_rows, run_id)

    # Step 6: Insert email_log_events junction rows
    junction_rows = []
    for log_row in inserted_logs:
        for event_id in emailed_event_ids:
            junction_rows.append({
                "email_log_id": log_row["id"],
                "event_id": event_id,
            })
    insert_email_log_events(junction_rows, run_id)

    logger.info(f"[{run_id}] Update check complete.")


def lambda_handler(event, context):
    try:
        check_for_updates()
        return {
            'statusCode': 200,
            'body': json.dumps('Update check completed!')
        }
    except Exception as e:
        logger.error(f"Lambda execution failed: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {e}")
        }


def main():
    try:
        check_for_updates()
        print('Update check completed!')
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()
