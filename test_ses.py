# test_ses.py
from dotenv import load_dotenv
load_dotenv()
from email_notifier import send_email

send_email(
    subject="SES Test",
    body="<p>This is a test email from SFF Stock Alerts via SES.</p>",
    to_email="robin.carey@gmail.com"
)
print("Done")