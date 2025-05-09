import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

load_dotenv()

# Grab credentials from environmental vars
SF_EMAIL_USERNAME = os.getenv("SF_EMAIL_USERNAME")
SF_EMAIL_PASSWORD = os.getenv("SF_EMAIL_PASSWORD")

def send_email(subject, body, to_email, is_html=True):
    from_email = SF_EMAIL_USERNAME
    password = SF_EMAIL_PASSWORD

    # Email setup
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach the email body
    if is_html:
        msg.attach(MIMEText(body, 'html'))  # Send HTML content
    else:
        msg.attach(MIMEText(body, 'plain'))  # Send plain text content

    # Sending email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.close()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    # Example usage
    send_email("Test HTML Email", "<h1>This is a test email</h1><p>This is a paragraph in the email body.</p>", "robin.carey@gmail.com", is_html=True)
