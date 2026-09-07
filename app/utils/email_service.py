import os
import smtplib
import logging
from typing import Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

logger = logging.getLogger("app.utils.email_service")

class EmailService:
    """
    Automated Candidate Email Notification Service.
    Supports real SMTP email delivery (Gmail, Outlook, SendGrid, custom SMTP)
    and fallback logger simulation.
    """

    @staticmethod
    def dispatch_email(to_email: str, subject: str, body: str) -> bool:
        """
        Sends real email via SMTP if configured, else logs message simulation.
        """
        smtp_host = settings.SMTP_HOST or os.getenv("SMTP_HOST", "")
        smtp_port = settings.SMTP_PORT or int(os.getenv("SMTP_PORT", "587"))
        smtp_user = settings.SMTP_USER or os.getenv("SMTP_USER", "")
        smtp_pass = settings.SMTP_PASSWORD or os.getenv("SMTP_PASSWORD", "")
        from_email = settings.SMTP_FROM_EMAIL or smtp_user or "no-reply@proctoring.ai"

        if not smtp_host or not smtp_user or not smtp_pass:
            logger.info(
                f"ℹ️ [SMTP NOT CONFIGURED - SIMULATION LOG]\n"
                f"To: {to_email}\nSubject: {subject}\nBody:\n{body}\n{'-'*60}"
            )
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_email
            msg["To"] = to_email

            part = MIMEText(body, "plain", "utf-8")
            msg.attach(part)

            if settings.SMTP_USE_TLS:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                server.starttls()
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)

            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, [to_email], msg.as_string())
            server.quit()

            logger.info(f"✅ [REAL EMAIL DISPATCHED] Successfully sent email to {to_email} via {smtp_host}:{smtp_port}")
            return True
        except Exception as e:
            logger.error(f"❌ [SMTP DISPATCH ERROR] Failed sending email to {to_email}: {e}")
            return False

    @classmethod
    def send_password_email(cls, email: str, username: str, password: str, match_confidence: str) -> Dict[str, Any]:
        """
        Dispatches password notification email upon successful face verification.
        """
        subject = f"AI Proctoring System - Your Access Password for {username}"
        body = (
            f"Dear Candidate ({username}),\n\n"
            f"Your face verification was SUCCESSFUL with a match confidence of {match_confidence}.\n\n"
            f"🔑 YOUR SINGLE-USE ACCESS PASSWORD: {password}\n\n"
            f"Instructions:\n"
            f"1. Return to the examination portal.\n"
            f"2. Enter Username: '{username}'\n"
            f"3. Enter Password: '{password}'\n\n"
            f"Only after entering this password will you gain access to the proctored exam session.\n\n"
            f"Best regards,\n"
            f"AI Examination & Proctoring Team"
        )
        sent_real = cls.dispatch_email(email, subject, body)
        return {
            "status": "SENT" if sent_real else "LOGGED_SIMULATION",
            "real_smtp": sent_real,
            "email": email,
            "subject": subject,
            "message": f"Password email delivered to {email}." if sent_real else f"Password email logged (SMTP unconfigured)."
        }

    @classmethod
    def send_login_confirmation_email(cls, email: str, username: str) -> Dict[str, Any]:
        """
        Dispatches confirmation email to user when login credentials match successfully.
        """
        subject = f"AI Proctoring Portal - Login Successful for {username}"
        body = (
            f"Dear Candidate ({username}),\n\n"
            f"Notice: Credentials for username '{username}' matched successfully!\n\n"
            f"Your session access token has been issued. You may now complete candidate consent and environment readiness checks.\n\n"
            f"If you did not initiate this login, please contact exam support immediately.\n\n"
            f"Best regards,\n"
            f"AI Examination & Proctoring Support"
        )
        sent_real = cls.dispatch_email(email, subject, body)
        return {
            "status": "SENT" if sent_real else "LOGGED_SIMULATION",
            "real_smtp": sent_real,
            "email": email,
            "subject": subject,
            "message": "Credential match confirmation email delivered."
        }
