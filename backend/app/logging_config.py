"""
Logging configuration for Claudia backend using Loguru

Provides:
- Colorized console output for development
- File logging with automatic rotation and compression
- Separate error log with longer retention
- Async-safe logging for FastAPI
"""
from loguru import logger
from pathlib import Path
import sys

from app.config import settings

# Ensure logs directory exists
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


def setup_logging():
    """
    Configure Loguru for the FastAPI application

    Features:
    - Console: Colorized output at INFO level
    - app.log: All logs (DEBUG+) with 10MB rotation, 30-day retention
    - errors.log: Error logs only with 50MB rotation, 60-day retention
    - All handlers are async-safe (enqueue=True)
    - Automatic compression of rotated logs (zip)
    - Backtrace and diagnostics for better error debugging
    """

    # Remove default handler
    logger.remove()

    # Console handler - colorized for development
    logger.add(
        sys.stdout,
        level=settings.backend_log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>",
        colorize=True,
        enqueue=True,  # Thread-safe, async-safe
        backtrace=True,
        diagnose=True
    )

    # File handler - all logs with rotation
    logger.add(
        LOGS_DIR / "app.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",      # Rotate when file reaches 10MB
        retention="30 days",   # Keep logs for 30 days
        compression="zip",     # Compress rotated logs
        enqueue=True,
        backtrace=True,
        diagnose=True
    )

    # Error-only file with longer retention
    logger.add(
        LOGS_DIR / "errors.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
        rotation="50 MB",      # Larger size for errors
        retention="60 days",   # Keep errors longer
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=True
    )

    logger.info(f"Logging configured - Level: {settings.backend_log_level}")
    logger.info(f"Logs directory: {LOGS_DIR.absolute()}")

    return logger
