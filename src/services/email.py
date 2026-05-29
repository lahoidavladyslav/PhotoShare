from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.core.config import settings
from src.core.security import create_access_token

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME="PhotoShare App",
    MAIL_STARTTLS=settings.MAIL_STARTTLS, 
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,   
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / 'templates',
)

async def send_email(email: EmailStr, username: str, host: str):
    """Відправляє лист із посиланням для підтвердження пошти."""
    try:
        token_verification = create_access_token(data={"sub": email}, expires_delta=86400)

        url_verification = f"{host}api/users/confirmed_email/{token_verification}"

        message = MessageSchema(
            subject="Confirm your email",
            recipients=[email],
            template_body={"host": host, "username": username, "url_verification": url_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="email_template.html")
    except ConnectionErrors as err:
        print(err)