import json
import os
import logging
from broken_binding_sf import broken_binding_checks
from email_notifier import send_email
import boto3
from io import BytesIO


# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
# Set global vars from environment vars
bucket = os.getenv('BUCKET_NAME')
file_key = os.getenv('FILE_PATH')
run_mode = os.getenv('RUN_MODE', 'prod').lower() # prod or dev, dev for local testing

# Get the appropriate file key for the run mode
def get_state_file_key():
    if run_mode == "dev":
        return os.getenv("DEV_FILE_KEY") or file_key
    return file_key

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
        logger.info(f"RUN_MODE=prod using S3 recipients (count={len(recips)})")
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

# Load previous items from S3
def load_seen_items():
    state_key = get_state_file_key()
    try:
        file_content = read_file_from_s3(bucket, state_key)
        return json.loads(file_content)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {e}")
    except Exception as e:
        logger.error(f"Error loading from S3: {e}")
    return []

# Save items to S3
def save_seen_items(items):
    state_key = get_state_file_key()
    json_data = json.dumps(items, indent=2)
    byte_stream = BytesIO(json_data.encode("utf-8"))

    s3_client = boto3.client("s3")
    try:
        s3_client.upload_fileobj(byte_stream, bucket, state_key)
        logger.info(f"File uploaded successfully to {bucket}/{state_key}")
    except Exception as e:
        logger.error(f"Error uploading to S3: {e}")

# Compare previously seen items to current site listing
def check_for_updates():
    recipient_emails = get_recipients_for_run()
    seen_items = load_seen_items()
    # Build a dictionary of dictionaries for faster searching for update types
    seen_items_dict = {item['name']: {key: value for key, value in item.items() if key != 'name'} for item in seen_items}
    new_items = broken_binding_checks()
    seen_set = {frozenset(s.items()) for s in seen_items}
    new_set = {frozenset(n.items()) for n in new_items}
    # Find new unseen items
    unseen_items_set = new_set.difference(seen_set)
    unseen_items = [dict(x) for x in unseen_items_set]

    # Check items for differences
    for book in unseen_items:
        if book['name'] not in seen_items_dict.keys():
            book['update_type'] = 'New Item'
        elif book['price'] != seen_items_dict[book['name']]['price']:
            old_price = seen_items_dict[book['name']]['price']
            book['update_type'] = 'Price Change - Previously ' + old_price
        elif book['store'] != seen_items_dict[book['name']]['store']:
            book['update_type'] = 'Store Change'
        elif book['link'] != seen_items_dict[book['name']]['link']:
            book['update_type'] = 'URL Change'
        else:
            book['update_type'] = 'Unknown Change'

    if unseen_items:
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
                        for item in unseen_items)
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
            send_email("New Broken Binding Books Available!", message, email)
        logger.info("New books found and email sent!")
        save_seen_items(new_items)
    else:
        logger.info("No new books found.")
        
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
