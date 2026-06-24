"""
Centralized logging setup for the Data Quality Framework.

All modules should obtain their logger via `get_logger(__name__)` rather
than calling `logging.getLogger` directly, so log formatting / handlers
stay consistent across the project.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

_CONFIGURED = False
DEFAULT_LOG_DIR = Path(__file__).resolve().parent.parent / "reports"
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "dq_framework.log"


def configure_logging(
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
) -> None:
    """Configure root logging handlers exactly once.

    Safe to call multiple times; subsequent calls are no-ops.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_file = log_file or DEFAULT_LOG_FILE
    log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger, configuring handlers if needed."""
    configure_logging()
    return logging.getLogger(name)
