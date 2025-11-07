"""Logging configuration for Instagram Reels Knowledge Base Creator."""

import logging
import sys
from pathlib import Path
from typing import Optional

from .config import Config


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors.

        Args:
            record: Log record to format

        Returns:
            Formatted log string
        """
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{self.BOLD}{levelname}{self.RESET}"
            )

        # Format the message
        formatted = super().format(record)

        # Reset levelname to original (for other handlers)
        record.levelname = levelname

        return formatted


class ProgressFormatter(logging.Formatter):
    """Formatter optimized for progress tracking."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for progress display.

        Args:
            record: Log record to format

        Returns:
            Formatted log string
        """
        # For INFO level, show simplified format
        if record.levelno == logging.INFO:
            return f"[{record.name}] {record.getMessage()}"

        # For other levels, use standard format
        return super().format(record)


def setup_logger(
    name: str = "reels_scraper",
    config: Optional[Config] = None,
    verbose: bool = False,
) -> logging.Logger:
    """Set up and configure logger.

    Args:
        name: Logger name
        config: Configuration object
        verbose: Enable verbose logging

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Determine log level
    if verbose:
        log_level = logging.DEBUG
    elif config and config.general:
        log_level = getattr(logging, config.general.log_level, logging.INFO)
    else:
        log_level = logging.INFO

    logger.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Use colored formatter for console if not in a pipe
    if sys.stdout.isatty():
        console_formatter = ColoredFormatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
    else:
        console_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if configured)
    if config and config.general.log_file:
        log_file = config.general.log_file

        # Create log directory if needed
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file

        file_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str = "reels_scraper") -> logging.Logger:
    """Get logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    # If logger hasn't been set up yet, set it up with defaults
    if not logger.handlers:
        setup_logger(name)

    return logger


class LoggerContextManager:
    """Context manager for temporary logger configuration."""

    def __init__(self, logger: logging.Logger, level: int):
        """Initialize context manager.

        Args:
            logger: Logger to modify
            level: Temporary log level
        """
        self.logger = logger
        self.level = level
        self.original_level = logger.level

    def __enter__(self) -> logging.Logger:
        """Enter context and set new log level."""
        self.logger.setLevel(self.level)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and restore original log level."""
        self.logger.setLevel(self.original_level)


def set_verbose(logger: logging.Logger, verbose: bool = True) -> None:
    """Set logger to verbose mode.

    Args:
        logger: Logger to modify
        verbose: Enable verbose mode
    """
    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
            handler.setLevel(level)


# Import handlers for rotating logs
import logging.handlers  # noqa: E402
