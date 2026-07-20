"""Centralized structured logging.

Every log record is emitted as a single JSON line so logs stay easy to
ingest/query regardless of deployment target. Use `get_logger(__name__)`
from anywhere in the app instead of the stdlib `logging` module directly.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

_CONFIGURED = False

_RESERVED_RECORD_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", None, None).__dict__.keys())


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Any extra=... fields passed to the log call get merged in.
        for key, value in record.__dict__.items():
            if key not in _RESERVED_RECORD_ATTRS and key not in payload:
                payload[key] = value

        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.setLevel(level.upper())
    root.handlers = [handler]

    # Quiet down noisy third-party loggers unless something is actually wrong.
    for noisy_logger in ("uvicorn.access", "httpx", "websockets"):
        logging.getLogger(noisy_logger).setLevel(max(logging.WARNING, root.level))

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
