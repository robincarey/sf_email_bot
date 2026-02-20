import json
import os
import logging
import boto3
from supabase import create_client
from broken_binding_sf import broken_binding_checks
from email_notifier import send_email
from io import BytesIO

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
# Set global vars from environment vars
bucket = os.getenv('BUCKET_NAME')
file_key = os.getenv('FILE_PATH')
run_mode = os.getenv('RUN_MODE', 'prod').lower() # prod or dev, dev for local testing

# Connect to supabase db
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load recipients from S3 or env var
def load_recipients():
    env_list = json.loads(os.getenv("RECIPIENT_EMAILS", "[]"))
    admin_list = json.loads(os.getenv("ADMIN_EMAILS", "[]"))
    recipients_key = os.getenv("RECIPIENTS_KEY")  # <-- runtime read

    if not bucket or not recipients_key:
        return env_list if run_mode != "prod" else admin_list

    try:
        content = read_file_from_s3(bucket, recipients_key)
        data = json.loads(content)
        if isinstance(data, list):
            return sorted(set(data))
        if isinstance(data, dict) and "recipients" in data:
            return sorted(set(data["recipients"]))
        logger.error("Recipients JSON must be a list or a dict with 'recipients'.")
    except Exception as e:
        logger.error(f"Could not load recipients from S3: {e}")

    return admin_list if run_mode == "prod" else env_list

# Load real recipients for production, local dev only uses env var
def get_recipients_for_run():
    if run_mode == "prod":
        recips = load_recipients()
        logger.info(f"RUN_MODE=prod using recipients from supabase db (count={len(recips)})")
        return recips

    recips = sorted(set(json.loads(os.getenv("RECIPIENT_EMAILS", "[]"))))
    logger.info(f"RUN_MODE=dev using env recipients (count={len(recips)})")
    return recips

# Reading files from S3
def read_file_from_s3(bucket_name, key):
    s3_client = boto3.client('s3')
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        content = response['Body'].read().decode('utf-8')
        return content
    except Exception as e:
        print(f"BUCKET_NAME: {bucket}, FILE_PATH: {file_key}")
        logger.error(f"Error reading from S3: {e}")
        raise

# Load previous items from supabase db
def load_seen_items():
    try:
        response = (
            supabase
            .table("items_seen")
            .select("name, price, store, link, in_stock")
            .execute()
        )
        return response.data or []
    except Exception as e:
        logger.error(f"Error loading from Supabase: {e}")
        return []

# Save items to supabase db
def save_seen_items(items):
    if not items:
        return

    try:
        response = (
            supabase
            .table("items_seen")
            .upsert(items, on_conflict="link")
            .execute()
        )
        logger.info(f"Upserted {len(items)} items into Supabase.")
    except Exception as e:
        logger.error(f"Error saving to Supabase: {e}")

# Compare previously seen items to current site listing
def check_for_updates():
    recipient_emails = get_recipients_for_run()
    seen_items = load_seen_items()
    # Build a dictionary of dictionaries for faster searching for update types
    seen_items_dict = {item['link']: {key: value for key, value in item.items() if key != 'link'} for item in seen_items}
    new_items = broken_binding_checks()
    if not new_items:
        logger.info("Scraper returned no items; skipping diff and upsert.")
        return
    seen_set = {frozenset(s.items()) for s in seen_items}
    new_set = {frozenset(n.items()) for n in new_items}
    # Find new unseen items
    unseen_items_set = new_set.difference(seen_set)
    unseen_items = [dict(x) for x in unseen_items_set]

    # Check items for differences
    for book in unseen_items:
        if book['link'] not in seen_items_dict:
            book['update_type'] = 'New Item'
        elif book['in_stock'] is True and seen_items_dict[book['link']]['in_stock'] is False:
            book['update_type'] = 'Restocked'
        elif book['in_stock'] is False and seen_items_dict[book['link']]['in_stock'] is True:
            book['update_type'] = 'Out of Stock'
        elif book['price'] != seen_items_dict[book['link']]['price']:
            old_price = seen_items_dict[book['link']]['price']
            book['update_type'] = 'Price Change - Previously ' + old_price
        elif book['store'] != seen_items_dict[book['link']]['store']:
            book['update_type'] = 'Store Change'
        else:
            book['update_type'] = 'Unknown Change'
    # Only email items that are not out of stock
    items_to_email = [i for i in unseen_items if i['update_type'] != 'Out of Stock']

    try:
        if items_to_email:
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
                            f"<td style='padding: 8px;'>{item['update_type']}</td>"
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
            for email in recipient_emails:
                try:
                    send_email("New Broken Binding Books Available!", message, email)
                except Exception as e:
                    logger.error(f"Failed to send email to {email}: {e}")
            logger.info("New books found and email sent!")
        else:
            logger.info("No alert-worthy changes found.")
    except Exception as e:
        logger.error(f"Email send failed: {e}")
    finally:
        # Update db with scraped items
        save_seen_items(new_items)
        
# The Lambda handler
def lambda_handler(event, context):
    try:
        check_for_updates()  # Call function when Lambda is triggered
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

# Main function for local testing
def main():
    
    try:
        check_for_updates()
        print('Update check completed!')
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()
