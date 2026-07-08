from __future__ import annotations

import logging as _stdlib_logging
import sys
from typing import Any

_FORMAT = "[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

_root_handler: _stdlib_logging.Handler | None = None


def _get_handler() -> _stdlib_logging.Handler:
    global _root_handler
    if _root_handler is None:
        handler = _stdlib_logging.StreamHandler(sys.stdout)
        handler.setFormatter(_stdlib_logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT))
        _root_handler = handler
    return _root_handler


def _resolve_level(level_name: str) -> int:
    return getattr(_stdlib_logging, level_name.upper(), _stdlib_logging.DEBUG)


class TravelLogger:
    """
    Structured logger for TravelOS services.

    Every service gets its own named logger under the 'travelos' hierarchy.
    Log level is read from ConfigurationManager (or LOG_LEVEL env var).

    Usage:
        logger = TravelLogger.for_service("GoalService")
        logger.info("Goal created", goal_id="abc-123", status="DRAFT")
    """

    def __init__(self, name: str) -> None:
        self._name = name
        self._logger = _stdlib_logging.getLogger(f"travelos.{name}")
        if not self._logger.handlers:
            self._logger.addHandler(_get_handler())
            self._logger.propagate = False
        self._apply_level()

    def _apply_level(self) -> None:
        try:
            from travelos.config.configuration_manager import config
            self._logger.setLevel(_resolve_level(config.log_level))
        except Exception:
            self._logger.setLevel(_stdlib_logging.DEBUG)

    @classmethod
    def for_service(cls, service_name: str) -> TravelLogger:
        return cls(service_name)

    # ------------------------------------------------------------------
    # Log methods
    # ------------------------------------------------------------------

    def _log(self, level: int, message: str, **context: Any) -> None:
        self._apply_level()
        if context:
            ctx_str = " | ".join(f"{k}={v}" for k, v in context.items())
            full_message = f"{message} | {ctx_str}"
        else:
            full_message = message
        self._logger.log(level, full_message)

    def info(self, message: str, **context: Any) -> None:
        self._log(_stdlib_logging.INFO, message, **context)

    def warning(self, message: str, **context: Any) -> None:
        self._log(_stdlib_logging.WARNING, message, **context)

    def error(self, message: str, **context: Any) -> None:
        self._log(_stdlib_logging.ERROR, message, **context)

    def debug(self, message: str, **context: Any) -> None:
        self._log(_stdlib_logging.DEBUG, message, **context)

    def exception(self, message: str, exc: Exception, **context: Any) -> None:
        context["exception"] = type(exc).__name__
        context["detail"] = str(exc)
        self._log(_stdlib_logging.ERROR, message, **context)
