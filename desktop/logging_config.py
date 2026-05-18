from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_desktop_logging(log_dir: str | Path, level: int = logging.INFO, reset: bool = False) -> Path:
    path = Path(log_dir).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    log_file = path / "desktop.log"

    root_logger = logging.getLogger()
    if reset:
        _remove_hermes_handlers(root_logger)

    for handler in root_logger.handlers:
        if getattr(handler, "_hermes_desktop_handler", False):
            return log_file

    handler = RotatingFileHandler(
        log_file,
        maxBytes=2 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    handler._hermes_desktop_handler = True
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    root_logger.setLevel(level)
    root_logger.addHandler(handler)
    return log_file


def _remove_hermes_handlers(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        if getattr(handler, "_hermes_desktop_handler", False):
            logger.removeHandler(handler)
            handler.close()

