import asyncio
import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

from config.adapters.email import get_email_adapter
from config.celery_app import celery_app
from config.settings import settings

if TYPE_CHECKING:
    from config.adapters import EmailAdapter


def _render_template(template: str, context: dict[str, Any]) -> str:
    """Render A Simple HTML Template Using Token Replacement.

    Arguments:
        template (str): Template string containing placeholders like {{ key }}.
        context (dict[str, Any]): Values to substitute into the template.

    Returns:
        str: Rendered template.

    Raises:
        None
    """

    rendered: str = template
    for key, value in context.items():
        rendered: str = rendered.replace(f"{{{{ {key} }}}}", str(object=value))
        rendered: str = rendered.replace(f"{{{{{key}}}}}", str(object=value))
    return rendered


async def _send_password_reset_email_async(  # noqa: PLR0913
    *,
    to_email: str,
    subject: str,
    first_name: str,
    last_name: str,
    username: str,
    reset_url: str,
    app_name: str,
    timestamp: str,
) -> bool:
    """Send Password Reset Email Using The Email Adapter.

    Arguments:
        to_email (str): Recipient email.
        subject (str): Email subject.
        first_name (str): User first name.
        last_name (str): User last name.
        username (str): Username.
        reset_url (str): Password reset URL.
        app_name (str): Application name to show in the email.
        timestamp (str): Timestamp to render in the email.

    Returns:
        bool: True if email was sent successfully.

    Raises:
        Exception: For Any Unexpected Errors During Email Sending.
    """

    adapter: EmailAdapter = await get_email_adapter()
    await adapter.connect()

    try:
        template_path: Path = (
            Path(__file__).resolve().parents[2] / "templates" / "auth" / "password_reset_email_template.html"
        )
        template: str = template_path.read_text(encoding="utf-8")

        html_body: str = _render_template(
            template=template,
            context={
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "email": to_email,
                "reset_url": reset_url,
                "app_name": app_name,
                "timestamp": timestamp,
            },
        )

        await adapter.send_html_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
        )

        return True
    finally:
        await adapter.disconnect()


async def _send_password_updated_email_async(  # noqa: PLR0913
    *,
    to_email: str,
    subject: str,
    first_name: str,
    last_name: str,
    username: str,
    app_name: str,
    timestamp: str,
) -> bool:
    """Send Password Updated Email Using The Email Adapter.


    Arguments:
        to_email (str): Recipient email.
        subject (str): Email subject.
        first_name (str): User first name.
        last_name (str): User last name.
        username (str): Username.
        app_name (str): Application name to show in the email.
        timestamp (str): Timestamp to render in the email.


    Returns:
        bool: True if email was sent successfully.


    Raises:
        Exception: For Any Unexpected Errors During Email Sending.
    """

    adapter: EmailAdapter = await get_email_adapter()
    await adapter.connect()

    try:
        template_path: Path = (
            Path(__file__).resolve().parents[2] / "templates" / "auth" / "password_updated_email_template.html"
        )
        template: str = template_path.read_text(encoding="utf-8")

        html_body: str = _render_template(
            template=template,
            context={
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "email": to_email,
                "app_name": app_name,
                "timestamp": timestamp,
            },
        )

        await adapter.send_html_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
        )

        return True
    finally:
        await adapter.disconnect()


@celery_app.task(name="src.tasks.auth.send_password_reset_email")
def send_password_reset_email(  # noqa: PLR0913
    *,
    to_email: str,
    first_name: str,
    last_name: str,
    username: str,
    reset_url: str,
    subject: str | None = None,
) -> dict[str, Any]:
    """On-Demand Celery Task To Send Password Reset Email.

    Arguments:
        to_email (str): Recipient email.
        first_name (str): User first name.
        last_name (str): User last name.
        username (str): Username.
        reset_url (str): Password reset URL.
        subject (str | None): Optional subject override.

    Returns:
        dict[str, Any]: Result payload containing status and timestamp.

    Raises:
        Exception: For Any Unexpected Errors During Email Sending.
    """

    if not settings.smtp_enabled:
        return {"status": "skipped", "reason": "Email is not enabled in settings"}

    send_time: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

    result: bool = asyncio.run(
        main=_send_password_reset_email_async(
            to_email=to_email,
            subject=subject or "Reset your password",
            first_name=first_name,
            last_name=last_name,
            username=username,
            reset_url=reset_url,
            app_name=settings.app_name,
            timestamp=send_time.isoformat(),
        ),
    )

    return {
        "status": "sent" if result else "failed",
        "to_email": to_email,
        "timestamp": send_time.isoformat(),
    }


@celery_app.task(name="src.tasks.auth.send_password_updated_email")
def send_password_updated_email(
    *,
    to_email: str,
    first_name: str,
    last_name: str,
    username: str,
    subject: str | None = None,
) -> dict[str, Any]:
    """On-Demand Celery Task To Send Password Updated Email.


    Arguments:
        to_email (str): Recipient email.
        first_name (str): User first name.
        last_name (str): User last name.
        username (str): Username.
        subject (str | None): Optional subject override.


    Returns:
        dict[str, Any]: Result payload containing status and timestamp.


    Raises:
        Exception: For Any Unexpected Errors During Email Sending.
    """

    if not settings.smtp_enabled:
        return {"status": "skipped", "reason": "Email is not enabled in settings"}

    send_time: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

    result: bool = asyncio.run(
        main=_send_password_updated_email_async(
            to_email=to_email,
            subject=subject or "Your password has been updated",
            first_name=first_name,
            last_name=last_name,
            username=username,
            app_name=settings.app_name,
            timestamp=send_time.isoformat(),
        ),
    )

    return {
        "status": "sent" if result else "failed",
        "to_email": to_email,
        "timestamp": send_time.isoformat(),
    }


__all__: list[str] = ["send_password_reset_email", "send_password_updated_email"]
