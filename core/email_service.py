import aiosmtplib
from email.message import EmailMessage
import io
from .config import settings
import logging

async def send_report_email(to_email: str, user_name: str, pdf_buf: io.BytesIO, filename: str = "Archetype_Strategy.pdf"):
    """
    Sends the PDF report to the specified email.
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logging.warning("SMTP settings missing, skipping email send.")
        return False

    message = EmailMessage()
    message["From"] = settings.SMTP_USER
    message["To"] = to_email
    message["Subject"] = f"Ваша стратегія Архетипів - {user_name}"
    message.set_content(f"Вітаємо, {user_name}!\n\nДякуємо за проходження тесту. Ваш персональний звіт у форматі PDF додано до цього листа.\n\nЗ повагою,\nКоманда Твій Архетип")

    # Attachment
    pdf_buf.seek(0)
    message.add_attachment(
        pdf_buf.read(),
        maintype="application",
        subtype="pdf",
        filename=filename
    )

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=(settings.SMTP_PORT == 465),
            start_tls=(settings.SMTP_PORT == 587)
        )
        
        # Also send a copy to Admin/User if needed
        if settings.ADMIN_EMAIL and settings.ADMIN_EMAIL != to_email:
             admin_msg = EmailMessage()
             admin_msg["From"] = settings.SMTP_USER
             admin_msg["To"] = settings.ADMIN_EMAIL
             admin_msg["Subject"] = f"Новий звіт: {user_name} ({to_email})"
             admin_msg.set_content(f"Новий користувач завершив тест: {user_name} ({to_email})")
             admin_msg.add_attachment(message.get_payload()[1].get_content(), maintype="application", subtype="pdf", filename=filename)
             await aiosmtplib.send(admin_msg, hostname=settings.SMTP_HOST, port=settings.SMTP_PORT, username=settings.SMTP_USER, password=settings.SMTP_PASSWORD, use_tls=(settings.SMTP_PORT == 465), start_tls=(settings.SMTP_PORT == 587))

        logging.info(f"Report sent to {to_email}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}: {e}")
        return False
