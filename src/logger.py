from __future__ import annotations

import logging
import os
from pathlib import Path


def configure_logging(level: str | None = None) -> logging.Logger:
    """Configure console and file logging for command runs."""
    log_level = (level or os.getenv("LOG_LEVEL") or "INFO").upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "thermal_intelligence.log", encoding="utf-8"),
        ],
        force=True,
    )
    return logging.getLogger("thermal_intelligence")
