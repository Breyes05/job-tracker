"""Sending email over SMTP.

Configure with SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASSWORD, and
EMAIL_FROM (defaults to SMTP_USER). Without SMTP_HOST, messages are written to
the log instead, which is handy for local development.
"""

import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger("app.email")


def send_email(to: str, subject: str, body: str) -> None:
    host = os.getenv("SMTP_HOST")
    if not host:
        logger.warning("SMTP_HOST is not set; not sending email.\nTo: %s\nSubject: %s\n\n%s", to, subject, body)
        return

    user = os.getenv("SMTP_USER", "")
    message = EmailMessage()
    message["From"] = os.getenv("EMAIL_FROM") or user
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=10) as smtp:
            smtp.starttls()
            if user:
                smtp.login(user, os.getenv("SMTP_PASSWORD", ""))
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError):
        # Runs after the response is sent, so log it rather than failing a request.
        logger.exception("Couldn't send email to %s", to)
