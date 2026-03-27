"""
ResearchAI - Structured Logging
Per-agent logging with configurable levels and formatted output.
"""

import logging
import sys
from config.settings import app_settings


def get_logger(name: str) -> logging.Logger:
    """Create a structured logger for an agent or module.

    Args:
        name: Logger name (typically the agent/module name).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(f"researchai.{name}")

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(name)-30s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, app_settings.log_level.upper(), logging.INFO))

    return logger
