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


async def _send_oauth_signup_email_async(  # noqa: PLR0913
    *,
    to_email: str,
    subject: str,
    first_name: str,
    last_name: str,
    username: str,
    provider: str,
    app_name: str,
    timestamp: str,
) -> bool:
    """Send OAuth Signup Email Using The Email Adapter.

    Arguments:
        to_email (str): Recipient email.
        subject (str): Email subject.
        first_name (str): User first name.
        last_name (str): User last name.
        username (str): Username.
        provider (str): OAuth provider name.
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
            Path(__file__).resolve().parents[2] / "templates" / "auth" / "oauth_signup_email_template.html"
        )
        template: str = template_path.read_text(encoding="utf-8")

        html_body: str = _render_template(
            template=template,
            context={
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "email": to_email,
                "provider": provider,
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


@celery_app.task(name="src.tasks.auth.send_oauth_signup_email")
def send_oauth_signup_email(  # noqa: PLR0913
    *,
    to_email: str,
    first_name: str,
    last_name: str,
    username: str,
    provider: str,
    subject: str | None = None,
) -> dict[str, Any]:
    """On-Demand Celery Task To Send OAuth Signup Email.

    Args:
        to_email (str): Recipient email.
        first_name (str): User first name.
        last_name (str): User last name.
        username (str): Username.
        provider (str): OAuth provider name.
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
        main=_send_oauth_signup_email_async(
            to_email=to_email,
            subject=subject or "Welcome to your account",
            first_name=first_name,
            last_name=last_name,
            username=username,
            provider=provider,
            app_name=settings.app_name,
            timestamp=send_time.isoformat(),
        ),
    )

    return {
        "status": "sent" if result else "failed",
        "to_email": to_email,
        "timestamp": send_time.isoformat(),
    }


__all__: list[str] = ["send_oauth_signup_email"]
