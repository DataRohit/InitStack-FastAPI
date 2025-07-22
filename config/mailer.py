# Standard Library Imports
from email.message import EmailMessage

# Third-Party Imports
import aiofiles
import aiosmtplib

# Local Imports
from config.settings import settings


# Render Template Function
async def render_template(template_path: str, context: dict) -> str:
    """
    Render Jinja Template

    Args:
        template_path: Path to Template File
        context: Context Variables for Template

    Returns:
        str: Rendered Template Content

    Raises:
        FileNotFoundError: If Template File Does Not Exist
        Exception: For Any Other Rendering Errors
    """

    # Open Template File
    async with aiofiles.open(template_path, encoding="utf-8") as f:
        # Read Template File
        template = await f.read()

    # Traverse Context
    for key, value in context.items():
        # Replace Context Variables
        template = template.replace(f"{{{{ {key} }}}}", str(value))

    # Return Rendered Template
    return template


# Send Email Function
async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    from_email: str = settings.MAILER_FROM,
) -> None:
    """
    Send Email

    Args:
        to_email: Recipient Email
        subject: Email Subject
        html_content: Email HTML Content
        from_email: Sender Email

    Raises:
        aiosmtplib.SMTPException: For SMTP Related Errors
        Exception: For Any Other Email Sending Errors
    """

    # Create Email Message
    message = EmailMessage()
    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(html_content, subtype="html")

    # Send Email
    await aiosmtplib.send(
        message,
        hostname=settings.MAILER_HOST,
        port=settings.MAILER_PORT,
        username=settings.MAILER_USER or None,
        password=settings.MAILER_PASS or None,
        use_tls=settings.MAILER_IS_TLS,
        start_tls=settings.MAILER_IS_TLS,
    )
