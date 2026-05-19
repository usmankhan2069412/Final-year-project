import os
from pathlib import Path
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from app.core.config import settings

# Path to the directory where we will store HTML email templates
TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "email"
os.makedirs(TEMPLATE_DIR, exist_ok=True)

mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USERNAME,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.SMTP_FROM,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_FROM_NAME=settings.SMTP_FROM_NAME,
    MAIL_STARTTLS=settings.SMTP_TLS,
    MAIL_SSL_TLS=settings.SMTP_SSL,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=TEMPLATE_DIR
)

async def send_reset_password_email(email_to: str, reset_link: str):
    """Sends a premium styled HTML password reset email asynchronously."""
    message = MessageSchema(
        subject="Reset your Aina Platform Password",
        recipients=[email_to],
        template_body={
            "reset_link": reset_link,
            "expiry_minutes": 15
        },
        subtype=MessageType.html
    )
    
    fm = FastMail(mail_config)
    # Sends email using a Jinja2 template file: "reset_password.html"
    await fm.send_message(message, template_name="reset_password.html")
