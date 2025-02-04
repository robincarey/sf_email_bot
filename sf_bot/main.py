import json
import os
import logging
from broken_binding_sf import broken_binding_sf
from email_notifier import send_email
import boto3
from io import BytesIO
from tabulate import tabulate

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

RECIPIENT_EMAIL = "robin.carey@gmail.com"
DATA_FILE = "items_seen.json"

# Reading files from S3
def read_file_from_s3(bucket_name, key):
    s3_client = boto3.client('s3')
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        content = response['Body'].read().decode('utf-8')
        return content
    except Exception as e:
        logger.error(f"Error reading from S3: {e}")
        raise

bucket = os.getenv('BUCKET_NAME')
file_key = os.getenv('FILE_PATH')

# Load previous items from S3
def load_seen_items():
    try:
        # Read the file content from S3
        file_content = read_file_from_s3(bucket, file_key)
        # Parse the JSON content into a set of tuples
        return {tuple(item) for item in json.loads(file_content)}  # Ensure tuples are returned
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    
    # Return an empty set if any error occurs
    return set()


# Save items to S3
def save_seen_items(items):
    json_data = json.dumps(list(items))
    byte_stream = BytesIO(json_data.encode('utf-8'))

    s3_client = boto3.client('s3')

    try:
        s3_client.upload_fileobj(byte_stream, bucket, file_key)
        logger.info(f"File uploaded successfully to {bucket}/{file_key}")
    except Exception as e:
        logger.error(f"Error uploading to S3: {e}")


# Compare previously seen items to current site listing
def check_for_updates():
    seen_items = load_seen_items()
    new_items = broken_binding_sf()
    current_item_names = {(item['name'], item['price']) for item in new_items}

    # Find new unseen items
    unseen_items = current_item_names - seen_items

    if unseen_items:
        headers = ["Item Name", "Price"]
        table = tabulate(unseen_items, headers=headers, tablefmt="grid")
        message = f"New items available:\n{table}"
        send_email("New Store Items Available!", message, RECIPIENT_EMAIL)
        logger.info("New items found and email sent!")
        save_seen_items(current_item_names)
    else:
        logger.info("No new items found.")
        
# The Lambda handler
def lambda_handler(event, context):
    try:
        check_for_updates()  # Call your function when Lambda is triggered
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
