import argparse
import json
import os
import re
import sys
import uuid
from html import unescape
from pathlib import Path

import boto3
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
AWS_SES_REGION = os.getenv("AWS_SES_REGION")
SES_FROM_ADDRESS = os.getenv("SES_FROM_ADDRESS")
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "[]")


def parse_args():
    parser = argparse.ArgumentParser(description="Send announcement email to active users.")
    parser.add_argument("--subject", required=True, help="Email subject line")
    parser.add_argument("--body-file", required=True, help="Path to HTML file for email body")
    parser.add_argument("--dry-run", action="store_true", help="Print recipients and subject without sending")
    parser.add_argument("--limit", type=int, help="Send to at most N recipients")
    parser.add_argument(
        "--admin-only",
        action="store_true",
        help="Send only to ADMIN_EMAILS from env (for local testing).",
    )
    return parser.parse_args()


def validate_env():
    missing = []
    for key, value in (
        ("SUPABASE_URL", SUPABASE_URL),
        ("SUPABASE_KEY", SUPABASE_KEY),
        ("AWS_SES_REGION", AWS_SES_REGION),
        ("SES_FROM_ADDRESS", SES_FROM_ADDRESS),
    ):
        if not value:
            missing.append(key)

    if missing:
        print(f"Error: missing required environment variables: {', '.join(missing)}")
        sys.exit(1)


def strip_html(html_body):
    # Keep this lightweight while producing readable fallback text.
    text = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", html_body, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def get_recipients(supabase, limit=None, admin_only=False):
    if admin_only:
        try:
            admin_emails = sorted(set(json.loads(ADMIN_EMAILS)))
        except json.JSONDecodeError:
            print("Error: ADMIN_EMAILS must be valid JSON (e.g. [\"you@example.com\"])")
            sys.exit(1)

        if not admin_emails:
            print("Error: --admin-only was set but ADMIN_EMAILS is empty.")
            sys.exit(1)

        response = (
            supabase.table("profiles")
            .select("id, email")
            .in_("email", admin_emails)
            .execute()
        )
        recipients = [row for row in (response.data or []) if row.get("email")]
        found = {row["email"] for row in recipients}
        missing = [email for email in admin_emails if email not in found]
        if missing:
            print(f"Warning: admin emails not found in profiles and skipped: {', '.join(missing)}")
    else:
        response = (
            supabase.table("profiles")
            .select("id, email")
            .eq("is_active", True)
            .eq("pause_all_alerts", False)
            .eq("receive_announcements", True)
            .execute()
        )
        recipients = [row for row in (response.data or []) if row.get("email")]

    if limit is not None:
        recipients = recipients[:limit]
    return recipients


def insert_email_logs(supabase, log_rows):
    if not log_rows:
        return
    supabase.table("email_log").insert(log_rows).execute()


def send_one_email(ses_client, to_email, subject, html_body, text_body):
    ses_client.send_email(
        Source=SES_FROM_ADDRESS,
        Destination={"ToAddresses": [to_email]},
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {
                "Html": {"Data": html_body, "Charset": "UTF-8"},
                "Text": {"Data": text_body, "Charset": "UTF-8"},
            },
        },
    )


def render_unsubscribe_html(html_body, unsubscribe_url):
    unsubscribe_link_html = f'<a href="{unsubscribe_url}">click here</a>'
    if "{UNSUBSCRIBE_LINK}" in html_body:
        return html_body.replace("{UNSUBSCRIBE_LINK}", unsubscribe_link_html)
    # Fallback for templates without the token.
    return (
        f'{html_body}\n<p style="margin-top: 32px; font-size: 12px; color: #888;">\n'
        "  To manage your notification preferences or unsubscribe,\n"
        f"  {unsubscribe_link_html}.\n"
        "</p>\n"
    )


def main():
    args = parse_args()
    validate_env()

    if args.limit is not None and args.limit < 0:
        print("Error: --limit must be >= 0")
        sys.exit(1)

    body_path = Path(args.body_file)
    if not body_path.exists() or not body_path.is_file():
        print(f"Error: body file not found: {body_path}")
        sys.exit(1)

    html_body = body_path.read_text(encoding="utf-8")
    text_body = strip_html(html_body)

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    recipients = get_recipients(supabase, args.limit, admin_only=args.admin_only)

    if args.dry_run:
        print(f"DRY RUN - Subject: {args.subject}")
        print(f"Recipients ({len(recipients)}):")
        for recip in recipients:
            print(f" - {recip['email']}")
        print("Summary: 0 sent, 0 failed")
        return

    ses_client = boto3.client("ses", region_name=AWS_SES_REGION)
    run_id = str(uuid.uuid4())

    sent_count = 0
    failed_count = 0
    log_rows = []

    for recip in recipients:
        user_id = recip["id"]
        to_email = recip["email"]

        try:
            response = supabase.auth.admin.generate_link(
                {
                    "type": "magiclink",
                    "email": to_email,
                    "options": {
                        "redirect_to": "https://sffstock.com/preferences?unsubscribe=true"
                    },
                }
            )
            unsubscribe_url = response.properties.action_link
            recipient_html_body = render_unsubscribe_html(html_body, unsubscribe_url)
            recipient_text_body = (
                f"{text_body}\n\n"
                f"To manage your preferences or unsubscribe: {unsubscribe_url}"
            )
            send_one_email(ses_client, to_email, args.subject, recipient_html_body, recipient_text_body)
            sent_count += 1
            log_rows.append(
                {
                    "user_id": user_id,
                    "run_id": run_id,
                    "subject": args.subject,
                    "success": True,
                    "error_message": None,
                }
            )
            print(f"Sent: {to_email}")
        except Exception as exc:
            failed_count += 1
            log_rows.append(
                {
                    "user_id": user_id,
                    "run_id": run_id,
                    "subject": args.subject,
                    "success": False,
                    "error_message": str(exc),
                }
            )
            print(f"Failed: {to_email} ({exc})")

    insert_email_logs(supabase, log_rows)
    print(f"Summary: {sent_count} sent, {failed_count} failed")


if __name__ == "__main__":
    main()
