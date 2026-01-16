import aiosmtplib
from email.message import EmailMessage
import io
from .config import settings
import logging

async def send_report_email(to_email: str, user_name: str, user_phone: str, pdf_buf: io.BytesIO, filename: str = "Archetype_Strategy.pdf"):
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

    async def try_send(port, use_tls, start_tls, timeout):
        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=port,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=use_tls,
                start_tls=start_tls,
                timeout=timeout
            )
            return True
        except Exception as e:
            logging.warning(f"SMTP failed on port {port}: {e}")
            return False

    try:
        # Step 1: Try Port 465 (SSL) - often preferred by Gmail
        success = await try_send(465, True, False, 15.0)
        
        # Step 2: Try Port 587 (STARTTLS) - fallback
        if not success:
            logging.info("Attempting fallback to port 587...")
            success = await try_send(587, False, True, 15.0)
            
        if success:
            logging.info(f"Email successfully sent to {to_email}")
            # Admin notification (simplified port logic here for brevity or repeat)
            if settings.ADMIN_EMAIL and settings.ADMIN_EMAIL != to_email:
                 admin_msg = EmailMessage()
                 admin_msg["From"] = settings.SMTP_USER
                 admin_msg["To"] = settings.ADMIN_EMAIL
                 admin_msg["Subject"] = f"Новий Ліда: {user_name} ({user_phone})"
                 admin_msg.set_content(f"Користувач завершив тест!\n\nІм'я: {user_name}\nEmail: {to_email}\nТелефон: {user_phone}\n\nЗвіт додано до листа.")
                 admin_msg.add_attachment(message.get_payload()[1].get_content(), maintype="application", subtype="pdf", filename=filename)
                 # Direct try on 587 for admin if it's the one that worked or just simpler
                 await aiosmtplib.send(admin_msg, hostname=settings.SMTP_HOST, port=587, username=settings.SMTP_USER, password=settings.SMTP_PASSWORD, use_tls=False, start_tls=True, timeout=10)
        else:
            raise Exception("All SMTP ports (465, 587) timed out or failed.")
            

        logging.info(f"Report sent to {to_email}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}: {e}")
        return False
