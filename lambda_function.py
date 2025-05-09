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
recipient_emails = json.loads(os.getenv('RECIPIENT_EMAILS', '[]'))
bucket = os.getenv('BUCKET_NAME')
file_key = os.getenv('FILE_PATH')

# Reading files from S3
def read_file_from_s3(bucket_name, key):
    
    s3_client = boto3.client('s3')
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        content = response['Body'].read().decode('utf-8')
        return content
    except Exception as e:
        print(f"BUCKET_NAME: {bucket}, FILE_PATH: {file_key}, RECIPIENT_EMAILS: {recipient_emails}")
        logger.error(f"Error reading from S3: {e}")
        raise

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
        logger.error(f"Error loading from S3: {e}")
    
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
    new_items = broken_binding_checks()
    current_item_names = {(item['name'], item['price'], item['store'], item['link']) for item in new_items}

    # Find new unseen items
    unseen_items = current_item_names - seen_items

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
                </tr>
            </thead>
            <tbody>
                {''.join(f"<tr style='border-bottom: 1px solid #ddd;'>"
                        f"<td style='padding: 8px;'><a href='{item[3]}'>"
                        f"{item[0]}</a></td>"
                        f"<td style='padding: 8px;'>{item[1]}</td>"
                        f"<td style='padding: 8px;'>{item[2]}</td>"
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
        save_seen_items(current_item_names)
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
# Testing Github Actions to deploy to lambda