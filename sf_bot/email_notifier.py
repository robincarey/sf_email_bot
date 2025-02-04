import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os


load_dotenv()
# Grab credentials from environmental vars
SF_EMAIL_USERNAME = os.getenv("SF_EMAIL_USERNAME")
SF_EMAIL_PASSWORD = os.getenv("SF_EMAIL_PASSWORD")


def send_email(subject, body, to_email):
    from_email = SF_EMAIL_USERNAME
    password = SF_EMAIL_PASSWORD

    # Email setup
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Add body
    msg.attach(MIMEText(body, 'plain'))

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
    send_email("Test Subject", "This is a test email.", "robin.carey@gmail.com")
    print(SF_EMAIL_USERNAME)
