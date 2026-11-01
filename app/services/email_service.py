import aiosmtplib

from email.message import EmailMessage

from app.config import settings


class EmailService:
    @staticmethod
    async def send_verification_otp(*, recipient: str, otp: str,) -> None:
        message = EmailMessage()

        message["From"] = (
            f"{settings.smtp_from_name} "
            f"<{settings.smtp_from_email}>"
        )
        message["To"] = recipient
        message["Subject"] = "Verify your NeuroOceans AI Recruiter account"

        message.set_content(
            f"""
Your NeuroOceans AI Recruiter verification code is:

{otp}

This code expires in {settings.auth_otp_expiry_minutes} minutes.

If you did not create this account, you can ignore this email.

NeuroOceans AI Recruiter
""".strip()
        )

        smtp_password = (
            settings.smtp_password.get_secret_value()
            if settings.smtp_password
            else None
        )

        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=smtp_password,
            start_tls=settings.smtp_start_tls,
        )