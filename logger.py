"""Central logging configuration.

Every module should import :func:`get_logger` instead of configuring the
``logging`` module itself::

    from logger import get_logger

    logger = get_logger(__name__)

All records are appended to ``logs/app.txt`` next to this file. The file is
rotated once it reaches 1 MB (three backups kept) so it can never grow
without bound. Warnings and errors are also echoed to the console, while
debug/info records stay in the file so they do not clutter the CLI.

Setup is idempotent: importing five modules must not attach five handlers.

Sensitive values (passwords, verification codes, decrypted entries) must
never be passed to a logger call.
"""

import logging
import logging.handlers
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_FILE = LOG_DIR / "app.txt"

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def setup_logging(level=logging.DEBUG):
    """Configure the application logger exactly once."""
    global _configured

    if _configured:
        return

    logger = logging.getLogger("password_manager")

    if logger.handlers:
        # Already configured by another import path or a previous call.
        _configured = True
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    _configured = True


def get_logger(name):
    """Return a module-scoped logger nested under the application namespace."""
    setup_logging()
    return logging.getLogger(f"password_manager.{name}")
