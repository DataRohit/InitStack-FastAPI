from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

import aiosmtplib

from config.logger import get_logger
from config.settings import settings

if TYPE_CHECKING:
    import logging


class EmailAdapter:
    """Professional Production-Grade Email SMTP Adapter.

    Inherits:
        object

    Attributes:
        _client (aiosmtplib.SMTP): Async SMTP client instance.
        _logger (logging.Logger): Logger instance for email operations.
        _is_connected (bool): Connection status flag.

    Properties:
        client: Get SMTP client instance.
        is_connected: Get connection status.

    Methods:
        connect: Establish SMTP connection.
        disconnect: Close SMTP connection.
        health_check: Perform SMTP health check.
        send_text_email: Send plain text email.
        send_html_email: Send HTML email.
        send_multipart_email: Send email with both text and HTML.
        _build_message: Build MIME message.
        _build_smtp_url: Build SMTP connection URL for logging.
    """

    def __init__(self) -> None:
        """Initialize Email Adapter.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        self._logger: logging.Logger = get_logger(name="email.adapter")

        self._client: aiosmtplib.SMTP | None = None
        self._is_connected: bool = False

        self._logger.info(
            msg="Email adapter initialized",
            extra={
                "smtp_host": settings.smtp_host,
                "smtp_port": settings.smtp_port,
                "smtp_from_email": settings.smtp_from_email,
                "smtp_use_tls": settings.smtp_use_tls,
                "smtp_use_ssl": settings.smtp_use_ssl,
            },
        )

    @property
    def client(self) -> aiosmtplib.SMTP:
        """Get SMTP Client Instance.

        Arguments:
            None

        Returns:
            aiosmtplib.SMTP: SMTP client instance.

        Raises:
            RuntimeError: If SMTP client is not connected.
        """

        if not self._client or not self._is_connected:
            msg = "SMTP client is not connected. Call connect() first."
            raise RuntimeError(msg)

        return self._client

    @property
    def is_connected(self) -> bool:
        """Get Connection Status.

        Arguments:
            None

        Returns:
            bool: True if connected to SMTP server, False otherwise.

        Raises:
            None
        """

        return self._is_connected

    async def connect(self) -> bool:
        """Establish SMTP Connection.

        Arguments:
            None

        Returns:
            bool: True if connection successful, False otherwise.

        Raises:
            Exception: If connection fails.
        """

        try:
            if self._is_connected:
                self._logger.warning(msg="SMTP client is already connected")
                return True

            self._logger.info(msg="Establishing SMTP connection")

            self._client = aiosmtplib.SMTP(
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                timeout=settings.smtp_timeout,
                use_tls=settings.smtp_use_ssl,
            )

            await self._client.connect()

            if settings.smtp_use_tls and not settings.smtp_use_ssl:
                await self._client.starttls()

            if settings.smtp_username and settings.smtp_password:
                await self._client.login(
                    settings.smtp_username,
                    settings.smtp_password,
                )

            self._is_connected = True

            self._logger.info(
                msg="SMTP connection established successfully",
                extra={
                    "smtp_host": settings.smtp_host,
                    "smtp_port": settings.smtp_port,
                    "smtp_from_email": settings.smtp_from_email,
                },
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to establish SMTP connection: {exc!s}",
                extra={
                    "smtp_host": settings.smtp_host,
                    "smtp_port": settings.smtp_port,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return True

    async def disconnect(self) -> None:
        """Close SMTP Connection.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        try:
            if not self._is_connected:
                self._logger.warning(msg="SMTP client is not connected")
                return

            self._logger.info(msg="Closing SMTP connection")

            if self._client:
                await self._client.quit()
                self._client = None

            self._is_connected = False

            self._logger.info(msg="SMTP connection closed successfully")

        except Exception as exc:
            self._logger.warning(
                msg=f"Error closing SMTP connection: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )

    async def health_check(self) -> bool:
        """Perform SMTP Health Check.

        Arguments:
            None

        Returns:
            bool: True if SMTP is healthy, False otherwise.

        Raises:
            None
        """

        try:
            if not self._is_connected:
                return False

            self._logger.debug(msg="Performing SMTP health check")

            await self._client.noop()  # ty:ignore[possibly-missing-attribute]

            self._logger.debug(msg="SMTP health check completed: healthy")

        except Exception as exc:
            self._logger.warning(
                msg=f"SMTP health check failed: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )
            return False

        else:
            return True

    async def send_text_email(  # noqa: PLR0913
        self,
        to_email: str | list[str],
        subject: str,
        body: str,
        *,
        from_email: str | None = None,
        from_name: str | None = None,
        cc: str | list[str] | None = None,
        bcc: str | list[str] | None = None,
    ) -> bool:
        """Send Plain Text Email.

        Arguments:
            to_email (str | list[str]): Recipient email address(es).
            subject (str): Email subject.
            body (str): Plain text email body.
            from_email (str | None): Sender email address.
            from_name (str | None): Sender name.
            cc (str | list[str] | None): CC recipients.
            bcc (str | list[str] | None): BCC recipients.

        Returns:
            bool: True if email sent successfully, False otherwise.

        Raises:
            Exception: If email sending fails.
        """

        try:
            self._logger.info(
                msg="Sending plain text email",
                extra={
                    "to_email": to_email,
                    "subject": subject,
                    "from_email": from_email or settings.smtp_from_email,
                },
            )

            message: MIMEText = MIMEText(body, "plain", "utf-8")
            message["Subject"] = subject
            message["From"] = f"{from_name or settings.smtp_from_name} <{from_email or settings.smtp_from_email}>"
            message["To"] = to_email if isinstance(to_email, str) else ", ".join(to_email)

            if cc:
                message["Cc"] = cc if isinstance(cc, str) else ", ".join(cc)

            if bcc:
                message["Bcc"] = bcc if isinstance(bcc, str) else ", ".join(bcc)

            recipients: list[str] = []
            if isinstance(to_email, str):
                recipients.append(to_email)
            else:
                recipients.extend(to_email)

            if cc:
                if isinstance(cc, str):
                    recipients.append(cc)
                else:
                    recipients.extend(cc)

            if bcc:
                if isinstance(bcc, str):
                    recipients.append(bcc)
                else:
                    recipients.extend(bcc)

            await self.client.send_message(message)

            self._logger.info(
                msg="Plain text email sent successfully",
                extra={
                    "to_email": to_email,
                    "subject": subject,
                    "recipients_count": len(recipients),
                },
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to send plain text email: {exc!s}",
                extra={
                    "to_email": to_email,
                    "subject": subject,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return True

    async def send_html_email(  # noqa: PLR0913
        self,
        to_email: str | list[str],
        subject: str,
        html_body: str,
        *,
        from_email: str | None = None,
        from_name: str | None = None,
        cc: str | list[str] | None = None,
        bcc: str | list[str] | None = None,
    ) -> bool:
        """Send HTML Email.

        Arguments:
            to_email (str | list[str]): Recipient email address(es).
            subject (str): Email subject.
            html_body (str): HTML email body.
            from_email (str | None): Sender email address.
            from_name (str | None): Sender name.
            cc (str | list[str] | None): CC recipients.
            bcc (str | list[str] | None): BCC recipients.

        Returns:
            bool: True if email sent successfully, False otherwise.

        Raises:
            Exception: If email sending fails.
        """

        try:
            self._logger.info(
                msg="Sending HTML email",
                extra={
                    "to_email": to_email,
                    "subject": subject,
                    "from_email": from_email or settings.smtp_from_email,
                },
            )

            message: MIMEText = MIMEText(html_body, "html", "utf-8")
            message["Subject"] = subject
            message["From"] = f"{from_name or settings.smtp_from_name} <{from_email or settings.smtp_from_email}>"
            message["To"] = to_email if isinstance(to_email, str) else ", ".join(to_email)

            if cc:
                message["Cc"] = cc if isinstance(cc, str) else ", ".join(cc)

            if bcc:
                message["Bcc"] = bcc if isinstance(bcc, str) else ", ".join(bcc)

            recipients: list[str] = []
            if isinstance(to_email, str):
                recipients.append(to_email)
            else:
                recipients.extend(to_email)

            if cc:
                if isinstance(cc, str):
                    recipients.append(cc)
                else:
                    recipients.extend(cc)

            if bcc:
                if isinstance(bcc, str):
                    recipients.append(bcc)
                else:
                    recipients.extend(bcc)

            await self.client.send_message(message)

            self._logger.info(
                msg="HTML email sent successfully",
                extra={
                    "to_email": to_email,
                    "subject": subject,
                    "recipients_count": len(recipients),
                },
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to send HTML email: {exc!s}",
                extra={
                    "to_email": to_email,
                    "subject": subject,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return True

    async def send_multipart_email(  # noqa: PLR0913
        self,
        to_email: str | list[str],
        subject: str,
        text_body: str,
        html_body: str,
        *,
        from_email: str | None = None,
        from_name: str | None = None,
        cc: str | list[str] | None = None,
        bcc: str | list[str] | None = None,
    ) -> bool:
        """Send Email With Both Text And HTML.

        Arguments:
            to_email (str | list[str]): Recipient email address(es).
            subject (str): Email subject.
            text_body (str): Plain text email body.
            html_body (str): HTML email body.
            from_email (str | None): Sender email address.
            from_name (str | None): Sender name.
            cc (str | list[str] | None): CC recipients.
            bcc (str | list[str] | None): BCC recipients.

        Returns:
            bool: True if email sent successfully, False otherwise.

        Raises:
            Exception: If email sending fails.
        """

        try:
            self._logger.info(
                msg="Sending multipart email",
                extra={
                    "to_email": to_email,
                    "subject": subject,
                    "from_email": from_email or settings.smtp_from_email,
                },
            )

            message: MIMEMultipart = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{from_name or settings.smtp_from_name} <{from_email or settings.smtp_from_email}>"
            message["To"] = to_email if isinstance(to_email, str) else ", ".join(to_email)

            if cc:
                message["Cc"] = cc if isinstance(cc, str) else ", ".join(cc)

            if bcc:
                message["Bcc"] = bcc if isinstance(bcc, str) else ", ".join(bcc)

            text_part: MIMEText = MIMEText(text_body, "plain", "utf-8")
            message.attach(text_part)

            html_part: MIMEText = MIMEText(html_body, "html", "utf-8")
            message.attach(html_part)

            recipients: list[str] = []
            if isinstance(to_email, str):
                recipients.append(to_email)
            else:
                recipients.extend(to_email)

            if cc:
                if isinstance(cc, str):
                    recipients.append(cc)
                else:
                    recipients.extend(cc)

            if bcc:
                if isinstance(bcc, str):
                    recipients.append(bcc)
                else:
                    recipients.extend(bcc)

            await self.client.send_message(message)

            self._logger.info(
                msg="Multipart email sent successfully",
                extra={
                    "to_email": to_email,
                    "subject": subject,
                    "recipients_count": len(recipients),
                },
            )

        except Exception as exc:
            self._logger.exception(
                msg=f"Failed to send multipart email: {exc!s}",
                extra={
                    "to_email": to_email,
                    "subject": subject,
                    "exception_type": type(exc).__name__,
                },
            )
            raise

        else:
            return True

    def _build_smtp_url(self) -> str:
        """Build SMTP Connection URL For Logging.

        Arguments:
            None

        Returns:
            str: SMTP connection URL.

        Raises:
            None
        """

        protocol: str = "smtps" if settings.smtp_use_ssl else "smtp"

        smtp_url: str = f"{protocol}://{settings.smtp_host}:{settings.smtp_port}"

        return smtp_url


email_adapter: EmailAdapter | None = None


async def get_email_adapter() -> EmailAdapter:
    """Get Email Adapter Instance.

    Arguments:
        None

    Returns:
        EmailAdapter: Email adapter instance.

    Raises:
        RuntimeError: If email is not enabled.
    """

    global email_adapter  # noqa: PLW0603

    if not settings.smtp_enabled:
        msg = "Email is not enabled in settings"
        raise RuntimeError(msg)

    if email_adapter is None:
        email_adapter = EmailAdapter()

    return email_adapter


async def initialize_email() -> EmailAdapter | None:
    """Initialize Email Connection.

    Arguments:
        None

    Returns:
        EmailAdapter | None: Email adapter instance if enabled, None otherwise.

    Raises:
        None
    """

    if not settings.smtp_enabled:
        logger: logging.Logger = get_logger(name="email.initialize")
        logger.info(msg="Email is disabled")
        return None

    logger: logging.Logger = get_logger(name="email.initialize")

    try:
        adapter: EmailAdapter = await get_email_adapter()

        await adapter.connect()

        is_healthy: bool = await adapter.health_check()
        if not is_healthy:
            logger.warning(msg="Email health check failed")
            return None

        logger.info(msg="Email initialization successful")

    except Exception as exc:
        logger.warning(
            msg=f"Failed to initialize Email (service will continue without Email): {exc!s}",
            extra={"exception_type": type(exc).__name__},
        )
        return None

    else:
        return adapter


async def shutdown_email() -> None:
    """Shutdown Email Connection.

    Arguments:
        None

    Returns:
        None

    Raises:
        None
    """

    global email_adapter  # noqa: PLW0603

    if email_adapter is not None:
        try:
            await email_adapter.disconnect()

            email_adapter = None

        except Exception as exc:
            logger: logging.Logger = get_logger(name="email.shutdown")
            logger.warning(
                msg=f"Error during Email shutdown: {exc!s}",
                extra={"exception_type": type(exc).__name__},
            )


__all__: list[str] = [
    "EmailAdapter",
    "get_email_adapter",
    "initialize_email",
    "shutdown_email",
]
