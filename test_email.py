import os
import smtplib
from email.message import EmailMessage


print("========================================")
print("E-Mail-Test")
print("========================================")


# ========================================
# Zugangsdaten aus GitHub Secrets
# ========================================

MAIL_USERNAME = os.environ["MAIL_USERNAME"]
MAIL_PASSWORD = os.environ["MAIL_PASSWORD"]
MAIL_TO = os.environ["MAIL_TO"]


# ========================================
# Test-E-Mail
# ========================================

msg = EmailMessage()

msg["Subject"] = "Mediathek Monitor – Test"
msg["From"] = MAIL_USERNAME
msg["To"] = MAIL_TO

msg.set_content(
    """Hallo,

dies ist eine Test-E-Mail des Mediathek Monitors.

Wenn du diese Nachricht erhalten hast,
funktioniert der E-Mail-Versand über GitHub Actions.

Viele Grüße

Mediathek Monitor
"""
)


# ========================================
# SMTP-Verbindung zu iCloud
# ========================================

print("Verbinde mit iCloud Mail...")


with smtplib.SMTP(
    "smtp.mail.me.com",
    587,
    timeout=30
) as smtp:

    print("SMTP-Verbindung erfolgreich!")

    smtp.starttls()

    print("TLS-Verschlüsselung aktiviert.")

    smtp.login(
        MAIL_USERNAME,
        MAIL_PASSWORD
    )

    print("Anmeldung erfolgreich.")

    smtp.send_message(msg)

    print("E-Mail erfolgreich versendet!")


print("========================================")
print("TEST ERFOLGREICH")
print("========================================")
