from __future__ import annotations

from email.message import EmailMessage
from pathlib import Path
import os
import smtplib

from .config import EmailConfig


def send_report(config: EmailConfig, html_report: Path) -> bool:
    if not config.enabled:
        return False
    password = os.environ.get(config.password_env, "")
    missing = [
        name
        for name, value in {
            "smtp_host": config.smtp_host,
            "username": config.username,
            "password": password,
            "recipient": config.recipient,
        }.items()
        if not value
    ]
    if missing:
        raise ValueError(f"Email is enabled but required fields are missing: {', '.join(missing)}")

    sender = config.sender or config.username
    message = EmailMessage()
    message["Subject"] = "Daily Storage Health Report"
    message["From"] = sender
    message["To"] = config.recipient
    message.set_content("Attached is the latest storage health report.")
    message.add_alternative(html_report.read_text(encoding="utf-8"), subtype="html")

    with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(config.username, password)
        smtp.send_message(message)
    return True
