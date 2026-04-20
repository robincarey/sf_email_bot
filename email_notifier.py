import boto3
from dotenv import load_dotenv
import os

load_dotenv()

ses_client = boto3.client('ses', region_name=os.environ['AWS_SES_REGION'])
SES_FROM_ADDRESS = os.environ['SES_FROM_ADDRESS']

def send_email(subject, body, to_email, is_html=True):
    body_type = 'Html' if is_html else 'Text'
    try:
        response = ses_client.send_email(
            Source=SES_FROM_ADDRESS,
            Destination={'ToAddresses': [to_email]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    body_type: {'Data': body, 'Charset': 'UTF-8'}
                }
            },
            ConfigurationSetName=os.environ['SES_CONFIGURATION_SET']
        )
        return response['MessageId']  # return it so the caller can store it
    except Exception as e:
        print(f"Failed to send email: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    send_email("Test HTML Email", "<h1>This is a test email</h1><p>This is a paragraph in the email body.</p>", "robin.carey@gmail.com", is_html=True)
