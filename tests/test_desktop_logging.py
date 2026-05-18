import logging

from desktop.logging_config import setup_desktop_logging


def test_desktop_logging_writes_rotating_log_file(tmp_path):
    log_file = setup_desktop_logging(tmp_path, reset=True)
    logger = logging.getLogger("hermes.test")

    logger.info("desktop-log-smoke")
    for handler in logging.getLogger().handlers:
        handler.flush()

    assert log_file.exists()
    assert "desktop-log-smoke" in log_file.read_text(encoding="utf-8")

