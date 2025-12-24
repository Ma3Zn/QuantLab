from __future__ import annotations

import json
import logging
from typing import IO, Any, Dict

from quantlab.data.errors import DataError

_STANDARD_ATTRS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
}


class StructuredJSONFormatter(logging.Formatter):
    """Minimal structured formatter emitting JSON for diagnostics and audit trails."""

    def format(self, record: logging.LogRecord) -> str:
        base: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra_context = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_ATTRS
        }
        if extra_context:
            base["context"] = extra_context
        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(base, default=str, separators=(",", ":"))


def get_logger(name: str, *, stream: IO[str] | None = None) -> logging.Logger:
    """Return a logger configured with structured JSON formatting."""

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler(stream)
        handler.setFormatter(StructuredJSONFormatter())
        logger.addHandler(handler)

    return logger


def log_data_error(logger: logging.Logger, error: DataError) -> None:
    """Emit a structured error log for a DataError."""

    logger.error(
        error.message,
        extra={"error_type": type(error).__name__, "context": dict(error.context)},
        exc_info=error.cause,
    )

