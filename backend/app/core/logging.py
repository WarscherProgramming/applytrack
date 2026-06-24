import json
import logging
import sys
from datetime import UTC, datetime


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)
        return json.dumps(payload)


_DEV_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"


def configure_logging() -> None:
    # Deferred import: config triggers env-var loading; deferring avoids any
    # circular-import risk if logging is imported before config is ready.
    from app.core.config import settings

    level = logging.getLevelName(settings.LOG_LEVEL)

    handler = logging.StreamHandler(sys.stdout)
    if settings.is_production:
        handler.setFormatter(_JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(_DEV_FORMAT, datefmt="%H:%M:%S"))

    logging.root.setLevel(level)
    logging.root.handlers = [handler]

    # Uvicorn registers its own access log handler; we silence it here so
    # requests aren't double-logged once our middleware handles them.
    logging.getLogger("uvicorn.access").propagate = False

    # SQLAlchemy's engine logger emits one line per query — useful at DEBUG,
    # extremely noisy otherwise.
    if level > logging.DEBUG:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
