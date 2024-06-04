
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
from typing import List
from fastapi import BackgroundTasks
from .config import settings

def send_email(to_email: str, subject: str, html_content: str):
    from_email = settings.EMAIL_FROM
    password = settings.EMAIL_PASSWORD

    msg = MIMEMultipart()
    msg['From'] = formataddr((settings.EMAIL_FROM_NAME, from_email))
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
    except Exception as e:
        print(f"Error: {e}")

def send_verification_email(background_tasks: BackgroundTasks, email: str, token: str):
    subject = "Verify your email address"
    verify_url = f"{settings.BASE_URL}/verify-email?token={token}"
    html_content = f"<p>Please click the following link to verify your email address:</p><p><a href='{verify_url}'>{verify_url}</a></p>"
    background_tasks.add_task(send_email, email, subject, html_content)
