import logging

from aiosmtplib import SMTP

from app.config import settings

logger = logging.getLogger(__name__)


async def _send_email(to: str, subject: str, body: str) -> None:
    """Send an email via SMTP, or log it to console when SMTP is not configured."""
    if not settings.SMTP_HOST:
        logger.info("SMTP not configured — email logged instead.")
        logger.info("To: %s | Subject: %s | Body: %s", to, subject, body)
        return

    message = f"From: {settings.EMAIL_FROM}\r\nTo: {to}\r\nSubject: {subject}\r\n\r\n{body}"
    smtp = SMTP(hostname=settings.SMTP_HOST, port=settings.SMTP_PORT, use_tls=True)
    async with smtp:
        await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        await smtp.sendmail(settings.EMAIL_FROM, to, message)


async def send_prospect_confirmation(email: str, first_name: str) -> None:
    """Send a confirmation email to the prospect after lead submission."""
    subject = "We received your information"
    body = (
        f"Hi {first_name},\n\n"
        "Thank you for submitting your information. An attorney will review your details and reach out shortly.\n\n"
        "Best regards,\nAlma"
    )
    await _send_email(email, subject, body)


async def send_attorney_notification(lead_email: str, first_name: str, last_name: str) -> None:
    """Notify the attorney that a new lead has been submitted."""
    subject = "New lead submitted"
    body = (
        f"A new lead has been submitted.\n\n"
        f"Name: {first_name} {last_name}\n"
        f"Email: {lead_email}\n\n"
        "Please log in to the dashboard to review."
    )
    await _send_email(settings.ATTORNEY_EMAIL, subject, body)
