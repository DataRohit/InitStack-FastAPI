import json
import logging
import sys
import typing
from datetime import UTC
from datetime import datetime

from colorama import Fore
from colorama import Style
from colorama import init

from config.settings import settings

init(autoreset=True, strip=False, convert=False)


class ColoredFormatter(logging.Formatter):
    """Custom Colored Formatter For Console Logging.

    Inherits:
        logging.Formatter

    Attributes:
        COLORS (ClassVar[dict[int, str]]): Color mapping for different log levels.
        RESET (ClassVar[str]): Reset color code.

    Properties:
        None

    Methods:
        format: Format log record with colors and detailed information.
    """

    COLORS: typing.ClassVar[dict[int, str]] = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA,
    }  # ty:ignore[invalid-assignment]
    RESET: typing.ClassVar[str] = Style.RESET_ALL  # ty:ignore[invalid-assignment]

    def format(self, record: logging.LogRecord) -> str:
        """Format Log Record With Colors And Detailed Information.

        Arguments:
            record (logging.LogRecord): Log record to format.

        Returns:
            str: Formatted colored log message.

        Raises:
            None
        """

        color: str = self.COLORS.get(record.levelno, "")

        relative_path: str = record.pathname.replace("\\", "/")
        if "initstack" in relative_path:
            relative_path: str = relative_path.split(sep="initstack/")[-1]

        timestamp: str = datetime.fromtimestamp(timestamp=record.created, tz=UTC).strftime(format="%Y-%m-%d %H:%M:%S")

        formatted_message = (
            f"{Fore.BLUE}timestamp{self.RESET}: {Fore.WHITE}{timestamp}{self.RESET} | "
            f"{Fore.BLUE}level{self.RESET}: {color}{record.levelname:8}{self.RESET} | "
            f"{Fore.BLUE}file{self.RESET}: {Fore.WHITE}{relative_path}:{record.lineno}{self.RESET} | "
            f"{Fore.BLUE}function{self.RESET}: {Fore.WHITE}{record.funcName}{self.RESET} | "
            f"{Fore.BLUE}message{self.RESET}: {color}{record.getMessage()}{self.RESET}"
        )

        if record.exc_info:
            formatted_message += f"\n{self.formatException(record.exc_info)}"

        return formatted_message


class JSONFormatter(logging.Formatter):
    """Custom JSON Formatter For Structured Logging With Colors.

    Inherits:
        logging.Formatter

    Attributes:
        LEVEL_COLORS (dict[int, str]): Color mapping for different log levels.
        FIELD_COLORS (dict[str, str]): Color mapping for JSON field names.

    Properties:
        None

    Methods:
        format: Format log record as colored JSON with detailed information.
        _colorize_json: Add colors to JSON string for better readability.
    """

    LEVEL_COLORS: dict[int, str] = {  # noqa: RUF012
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA,
    }  # ty:ignore[invalid-assignment]

    FIELD_COLORS: dict[str, str] = {  # noqa: RUF012
        "timestamp": Fore.BLUE,
        "level": Fore.WHITE,
        "logger": Fore.MAGENTA,
        "message": Fore.WHITE,
        "module": Fore.CYAN,
        "function": Fore.YELLOW,
        "file": Fore.CYAN,
        "process": Fore.GREEN,
        "thread": Fore.GREEN,
        "exception": Fore.RED,
        "extra": Fore.LIGHTBLUE_EX,
    }  # ty:ignore[invalid-assignment]

    def format(self, record: logging.LogRecord) -> str:
        """Format Log Record As Colored JSON With Detailed Information.

        Arguments:
            record (logging.LogRecord): Log record to format.

        Returns:
            str: Formatted colored JSON log message.

        Raises:
            None
        """

        relative_path: str = record.pathname.replace("\\", "/")
        if "initstack" in relative_path:
            relative_path: str = relative_path.split(sep="initstack/")[-1]

        log_data: dict[str, typing.Any] = {
            "timestamp": datetime.fromtimestamp(timestamp=record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "file": f"{relative_path}:{record.lineno}",
            "process": record.process,
            "thread": record.thread,
        }

        excluded: set[str] = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "getMessage",
            "exc_info",
            "exc_text",
            "stack_info",
            "message",
        }

        log_data.update(
            {key: value for key, value in record.__dict__.items() if key not in excluded and not key.startswith("_")},
        )

        if record.exc_info:
            log_data["exception"] = self.formatException(ei=record.exc_info)

        json_str: str = json.dumps(obj=log_data, separators=(",", ":"))
        return self._colorize_json(json_str, level=record.levelno)

    def _colorize_json(self, json_str: str, level: int) -> str:
        """Add Colors To JSON String For Better Readability.

        Arguments:
            json_str (str): JSON string to colorize.
            level (int): Log level for color selection.

        Returns:
            str: Colorized JSON string.

        Raises:
            None
        """

        level_color: int = self.LEVEL_COLORS.get(level, Fore.WHITE)  # ty:ignore[invalid-assignment]

        data: dict[str, typing.Any] = json.loads(s=json_str)

        colored_parts: list[typing.Any] = []
        colored_parts.append(f"{level_color}{{{Style.RESET_ALL}")

        for i, (key, value) in enumerate(iterable=data.items()):
            if i > 0:
                colored_parts.append(f"{level_color},{Style.RESET_ALL}")

            colored_parts.append(f'{Fore.BLUE}"{key}"{Style.RESET_ALL}')
            colored_parts.append(f"{level_color}:{Style.RESET_ALL}")

            if key in ("level", "message"):
                if isinstance(value, str):
                    colored_parts.append(f'{level_color}"{value}"{Style.RESET_ALL}')
                else:
                    colored_parts.append(f"{level_color}{value}{Style.RESET_ALL}")
            elif isinstance(value, str):
                colored_parts.append(f'{Fore.WHITE}"{value}"{Style.RESET_ALL}')
            elif isinstance(value, bool):
                colored_parts.append(f"{Fore.WHITE}{str(object=value).lower()}{Style.RESET_ALL}")
            elif value is None:
                colored_parts.append(f"{Fore.WHITE}null{Style.RESET_ALL}")
            else:
                colored_parts.append(f"{Fore.WHITE}{value}{Style.RESET_ALL}")

        colored_parts.append(f"{level_color}}}{Style.RESET_ALL}")
        return "".join(colored_parts)


class LoggerManager:
    """Logger Manager For Creating And Managing Logger Instances.

    Inherits:
        object

    Attributes:
        _loggers (dict[str, logging.Logger]): Cache of created loggers.

    Properties:
        None

    Methods:
        get_logger: Get or create a logger instance.
        _setup_console_handler: Setup console handler with appropriate formatter.
        _configure_third_party_loggers: Configure third-party library loggers.
        setup_root_logger: Setup the root logger configuration.
    """

    _loggers: typing.ClassVar[dict[str, logging.Logger]] = {}

    @classmethod
    def get_logger(
        cls,
        name: str = __name__,
        level: str = "INFO",
        format_type: str = "standard",
    ) -> logging.Logger:
        """Get Or Create A Logger Instance.

        Arguments:
            name (str): Logger name (default: __name__).
            level (str): Logging level (default: "INFO").
            format_type (str): Format type - "standard" or "json" (default: "standard").

        Returns:
            logging.Logger: Configured logger instance.

        Raises:
            ValueError: If format_type is not "standard" or "json".
        """

        if format_type not in {"standard", "json"}:
            msg = "format_type must be 'standard' or 'json'"
            raise ValueError(msg)

        logger_key = f"{name}_{level}_{format_type}"

        if logger_key not in cls._loggers:
            logger: logging.Logger = logging.getLogger(name)
            logger.setLevel(level=getattr(logging, level.upper()))

            for handler in logger.handlers[:]:
                logger.removeHandler(hdlr=handler)

            cls._setup_console_handler(logger, format_type)
            logger.propagate = False
            cls._loggers[logger_key] = logger

        return cls._loggers[logger_key]

    @classmethod
    def _setup_console_handler(cls, logger: logging.Logger, format_type: str) -> None:
        """Setup Console Handler With Appropriate Formatter.

        Arguments:
            logger (logging.Logger): Logger instance to configure.
            format_type (str): Format type - "standard" or "json".

        Returns:
            None

        Raises:
            None
        """

        console_handler: logging.StreamHandler[typing.TextIO] = logging.StreamHandler(stream=sys.stdout)
        console_handler.setLevel(logger.level)

        formatter: JSONFormatter | ColoredFormatter = JSONFormatter() if format_type == "json" else ColoredFormatter()

        console_handler.setFormatter(fmt=formatter)
        logger.addHandler(hdlr=console_handler)

    @classmethod
    def _configure_third_party_loggers(cls) -> None:
        """Configure Third-Party Library Loggers.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        third_party_loggers: list[str] = [
            "uvicorn",
            "uvicorn.access",
            "uvicorn.error",
            "fastapi",
            "starlette",
            "httpx",
            "asyncio",
        ]

        for logger_name in third_party_loggers:
            logger: logging.Logger = logging.getLogger(name=logger_name)
            logger.setLevel(level=logging.WARNING)

    @classmethod
    def setup_root_logger(cls) -> None:
        """Setup The Root Logger Configuration.

        Arguments:
            None

        Returns:
            None

        Raises:
            None
        """

        root_logger: logging.Logger = logging.getLogger()
        root_logger.handlers.clear()

        log_level: int = getattr(logging, settings.log_level.upper(), logging.INFO)
        root_logger.setLevel(level=log_level)

        console_handler: logging.StreamHandler[typing.TextIO] = logging.StreamHandler(stream=sys.stdout)
        console_handler.setLevel(level=log_level)

        formatter: JSONFormatter | ColoredFormatter = (
            JSONFormatter() if settings.log_format.lower() == "json" else ColoredFormatter()
        )

        console_handler.setFormatter(fmt=formatter)
        root_logger.addHandler(hdlr=console_handler)

        root_logger.propagate = False
        cls._configure_third_party_loggers()


def get_logger(name: str = __name__, level: str | None = None, format_type: str | None = None) -> logging.Logger:
    """Get Logger Instance With Settings From Configuration.

    Arguments:
        name (str): Logger name (default: __name__).
        level (str | None): Logging level (default: from settings).
        format_type (str | None): Format type (default: from settings).

    Returns:
        logging.Logger: Configured logger instance.

    Raises:
        None
    """

    return LoggerManager.get_logger(
        name=name,
        level=level or settings.log_level,
        format_type=format_type or settings.log_format,
    )


__all__: list[str] = ["ColoredFormatter", "JSONFormatter", "LoggerManager", "get_logger"]
