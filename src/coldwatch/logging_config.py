"""
Centralized logging configuration for coldwatch application.

This module provides standardized logging setup with proper levels, formatters,
handlers, and rotation for the AT-SPI accessibility logger.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color coding for different log levels."""

    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        if hasattr(record, 'levelname') and record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    enable_console: bool = True,
    enable_file_rotation: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    logger_name: str = "coldwatch"
) -> logging.Logger:
    """
    Configure comprehensive logging for the coldwatch application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (if None, defaults to coldwatch.log)
        enable_console: Whether to log to console
        enable_file_rotation: Whether to enable log file rotation
        max_file_size: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        logger_name: Name of the logger

    Returns:
        Configured logger instance
    """
    # Get or create logger
    logger = logging.getLogger(logger_name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        logger.handlers.clear()

    # Set logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)-8s | %(module)s:%(lineno)d | %(funcName)s() | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_formatter = ColoredFormatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_file is None:
        log_file = Path("coldwatch.log")

    if enable_file_rotation:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
    else:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')

    file_handler.setLevel(logging.DEBUG)  # File gets all messages
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    logger.info(f"Logging configured - Level: {log_level}, File: {log_file}")
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger with the coldwatch hierarchy.

    Args:
        name: Name for the child logger (e.g., 'core', 'db', 'scanner')

    Returns:
        Child logger instance
    """
    return logging.getLogger(f"coldwatch.{name}")


def log_exception(logger: logging.Logger, message: str, exc_info: bool = True):
    """
    Log an exception with full traceback and context.

    Args:
        logger: Logger instance to use
        message: Custom message to log with the exception
        exc_info: Whether to include exception info
    """
    logger.error(message, exc_info=exc_info)


def log_atspi_event(logger: logging.Logger, event_type: str, app_name: str,
                   object_role: str, details: Optional[dict] = None):
    """
    Log AT-SPI events with structured context.

    Args:
        logger: Logger instance to use
        event_type: Type of AT-SPI event
        app_name: Name of the application
        object_role: Role of the accessibility object
        details: Additional event details
    """
    extra_info = f"app={app_name}, role={object_role}"
    if details:
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        extra_info += f", {detail_str}"

    logger.debug(f"AT-SPI Event: {event_type} | {extra_info}")


def log_database_operation(logger: logging.Logger, operation: str,
                          table: str, affected_rows: int = 0,
                          execution_time: Optional[float] = None):
    """
    Log database operations with performance metrics.

    Args:
        logger: Logger instance to use
        operation: Type of database operation (INSERT, UPDATE, SELECT, etc.)
        table: Database table name
        affected_rows: Number of rows affected
        execution_time: Operation execution time in seconds
    """
    msg = f"DB Operation: {operation} on {table}, rows={affected_rows}"
    if execution_time is not None:
        msg += f", time={execution_time:.3f}s"

    if execution_time and execution_time > 1.0:
        logger.warning(f"Slow {msg}")
    else:
        logger.debug(msg)