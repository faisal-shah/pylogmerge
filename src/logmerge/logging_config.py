#!/usr/bin/env python3
"""
Logging configuration for the Merged Log Viewer application.

This module provides centralized logging configuration and utilities for the application.
"""

import logging
import sys
from typing import Optional


def setup_logging(log_level: str = "WARNING") -> logging.Logger:
    """
    Set up logging configuration for the application.

    Args:
        log_level: The logging level as a string (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        The configured logger instance
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.WARNING)

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Get logger for our application
    logger = logging.getLogger("logmerge")
    logger.setLevel(numeric_level)

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: The logger name, typically __name__ from the calling module

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f'logmerge.{name.split(".")[-1]}')
    else:
        return logging.getLogger("logmerge")
