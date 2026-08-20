"""Single logging setup used across the pipeline. Import ``get_logger`` everywhere."""

from __future__ import annotations

import logging

_CONFIGURED = False


def get_logger(name: str = "distill") -> logging.Logger:
    """Return a named logger, configuring the root handler once, consistently."""
    global _CONFIGURED
    if not _CONFIGURED:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
        _CONFIGURED = True
    return logging.getLogger(name)
