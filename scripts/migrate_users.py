"""
One-off migration: move existing users from the `users` table into
Supabase Auth + the new `profiles` table.

Prerequisites:
  - The 001_profiles_and_preferences.sql migration has already been applied.
  - SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY env vars are set.
    (The service-role key is required to call auth.admin methods.)

Usage:
  python scripts/migrate_users.py                    # dry-run (default)
  python scripts/migrate_users.py --apply            # create accounts
  python scripts/migrate_users.py --apply --verbose  # create accounts with full error output
  python scripts/migrate_users.py --check-trigger    # verify the profiles trigger works
"""

import argparse
import os
import sys
import traceback

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")


def check_trigger(sb):
    """Verify the profiles table and trigger exist and work."""
    print("--- Trigger health check ---\n")

    print("1. Checking if `profiles` table exists...")
    try:
        resp = sb.table("profiles").select("id").limit(1).execute()
        print(f"   OK — profiles table accessible ({len(resp.data or [])} rows sampled)\n")
    except Exception as e:
        print(f"   FAIL — Cannot query profiles table: {e}")
        print("   -> Run supabase/migrations/001_profiles_and_preferences.sql first.\n")
        return False

    print("2. Checking if `user_store_preferences` table exists...")
    try:
        resp = sb.table("user_store_preferences").select("id").limit(1).execute()
        print(f"   OK — user_store_preferences table accessible ({len(resp.data or [])} rows sampled)\n")
    except Exception as e:
        print(f"   FAIL — Cannot query user_store_preferences table: {e}")
        return False

    print("3. Checking trigger by creating + deleting a test auth user...")
    test_email = "sf-bot-migration-test@example.invalid"
    try:
        auth_resp = sb.auth.admin.create_user({
            "email": test_email,
            "email_confirm": True,
        })
        test_uid = auth_resp.user.id
        print(f"   Created test auth user: {test_uid}")

        profile_resp = sb.table("profiles").select("id, email").eq("id", str(test_uid)).execute()
        if profile_resp.data:
            print(f"   OK — Trigger created profile row for {test_email}")
        else:
            print("   WARN — No profile row was created. The trigger may not be installed.")

        prefs_resp = sb.table("user_store_preferences").select("id, store_name").eq("user_id", str(test_uid)).execute()
        if prefs_resp.data:
            stores = [r["store_name"] for r in prefs_resp.data]
            print(f"   OK — Store preferences created: {stores}")
        else:
            print("   WARN — No store preferences created. The profile trigger may not be installed.")

        sb.auth.admin.delete_user(str(test_uid))
        print(f"   Cleaned up test user {test_uid}\n")
        return True

    except Exception as e:
        print(f"   FAIL — Could not create test user: {e}")
        print(f"   Full error: {traceback.format_exc()}")
        print("   -> This is the same error your migration is hitting.")
        print("   -> Check that the migration SQL was applied and the trigger exists.\n")
        return False


def main():
    parser = argparse.ArgumentParser(description="Migrate users -> Supabase Auth + profiles")
    parser.add_argument("--apply", action="store_true", help="Actually create auth accounts (default is dry-run)")
    parser.add_argument("--verbose", action="store_true", help="Print full tracebacks on errors")
    parser.add_argument("--check-trigger", action="store_true", help="Verify profiles table and trigger, then exit")
    args = parser.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set.")
        sys.exit(1)

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    if args.check_trigger:
        ok = check_trigger(sb)
        sys.exit(0 if ok else 1)

    print("Fetching existing users from `users` table...")
    resp = sb.table("users").select("id, email, is_active").execute()
    existing_users = resp.data or []
    print(f"Found {len(existing_users)} users.\n")

    if not existing_users:
        print("Nothing to migrate.")
        return

    created = 0
    skipped = 0
    errors = 0

    for user in existing_users:
        email = user["email"].strip()
        is_active = user.get("is_active", True)
        label = "DRY-RUN" if not args.apply else "APPLY"

        if not args.apply:
            print(f"  [{label}] Would create auth user for {email} (is_active={is_active})")
            created += 1
            continue

        try:
            auth_resp = sb.auth.admin.create_user({
                "email": email,
                "email_confirm": True,
            })
            new_uid = auth_resp.user.id
            print(f"  [{label}] Created auth user {email} -> {new_uid}")

            sb.table("profiles").update({
                "is_active": is_active,
            }).eq("id", str(new_uid)).execute()

            created += 1
        except Exception as e:
            err_str = str(e)
            if "already been registered" in err_str or "already exists" in err_str:
                print(f"  [{label}] Skipped {email} (already registered)")
                skipped += 1
            else:
                print(f"  [{label}] ERROR migrating {email}: {e}")
                if args.verbose:
                    traceback.print_exc()
                errors += 1

    print(f"\nDone. Created: {created}, Skipped: {skipped}, Errors: {errors}")
    if not args.apply:
        print("(This was a dry run. Pass --apply to actually create accounts.)")
    if errors > 0:
        print("\nTroubleshooting:")
        print("  1. Run: python scripts/migrate_users.py --check-trigger")
        print("     This verifies the profiles table and trigger are working.")
        print("  2. Re-run with --verbose for full error tracebacks.")
        print("  3. Ensure supabase/migrations/001_profiles_and_preferences.sql has been applied.")


if __name__ == "__main__":
    main()
