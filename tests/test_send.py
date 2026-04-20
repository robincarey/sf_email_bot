# test_send.py
import os
from dotenv import load_dotenv
load_dotenv()

from email_notifier import send_email

# Send to yourself only
ses_message_id = send_email(
    subject="Test tracking",
    body='<p>Test email with tracking. <a href="https://thebrokenbindingsub.com">Click here</a></p>',
    to_email="robin.carey@gmail.com",
    is_html=True
)

print(f"SES Message ID: {ses_message_id}")
# Should print a real message ID, not None