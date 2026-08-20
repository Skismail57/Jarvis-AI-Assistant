import sys
from pathlib import Path
from loguru import logger as _logger
from ..config import settings, LOGS_DIR


def setup_logger():
    _logger.remove()
    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    _logger.add(
        sys.stdout,
        level=settings.log_level,
        format=fmt,
        colorize=True,
        enqueue=True,
    )
    log_file = Path(LOGS_DIR) / "jarvis_{time:YYYYMMDD}.log"
    _logger.add(
        str(log_file),
        level="DEBUG",
        format=fmt,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
        encoding="utf-8",
    )
    return _logger


logger = setup_logger()
