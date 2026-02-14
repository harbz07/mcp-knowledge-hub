"""Generate and send a daily email report using environment-provided credentials."""

from __future__ import annotations

import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage

SMTP_SERVER = os.getenv("REPORT_SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("REPORT_SMTP_PORT", "587"))
REPORT_SUBJECT = os.getenv("REPORT_SUBJECT", "Daily Automated Report")


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def generate_report() -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return (
        f"Daily Report — {today}\n\n"
        "• Metric A: 123\n"
        "• Metric B: 456\n"
        "• Status: All systems operational\n"
    )


def send_email(body: str) -> None:
    sender_email = _required_env("REPORT_SENDER_EMAIL")
    sender_password = _required_env("REPORT_EMAIL_PASSWORD")
    recipient_email = _required_env("REPORT_RECIPIENT_EMAIL")

    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = REPORT_SUBJECT
    msg.set_content(body)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)


if __name__ == "__main__":
    send_email(generate_report())
