import inspect
import logging
import sys
from typing import Callable

from loguru import logger

from argus.config import Config, LoggingConfig


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = inspect.currentframe(), 0
        while frame:
            filename = frame.f_code.co_filename
            is_logging = filename == logging.__file__
            is_frozen = "importlib" in filename and "_bootstrap" in filename
            if depth > 0 and not (is_logging or is_frozen):
                break
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _build_filter(pattern: str | None) -> Callable[[dict], bool] | None:
    if pattern is None:
        return None
    return lambda record: pattern in record["name"] or pattern in record["message"]


def _setup_loguru(config: LoggingConfig) -> None:
    logger.remove()

    logger.add(
        sys.stderr,
        level=config.stderr.level,
        filter=_build_filter(config.stderr.filter),
    )

    if config.file is not None:
        file_cfg = config.file
        file_cfg.path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            str(file_cfg.path),
            level=file_cfg.level,
            filter=_build_filter(file_cfg.filter),
            rotation=file_cfg.rotation,
            compression=file_cfg.compression,
            retention=file_cfg.retention,
        )


def setup_logging(config: Config) -> None:
    _setup_loguru(config.logging)
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
