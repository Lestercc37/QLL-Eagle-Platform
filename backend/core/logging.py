from __future__ import annotations

import logging
import sys

from backend.core.settings import Settings


def configure_logging(settings: Settings) -> None:
    """Configure process-wide logging for the API service."""

    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
