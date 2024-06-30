"""Logger for wenxian."""

from __future__ import annotations

import logging


def _get_logger(name):
    """Get a logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.WARNING)
    handler = logging.StreamHandler()
    handler.setLevel(logging.WARNING)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logger = _get_logger(__name__)
"""Global logger for wenxian."""

__all__ = ["logger"]
