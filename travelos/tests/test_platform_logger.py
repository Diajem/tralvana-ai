import logging

from travelos.logging.travel_logger import TravelLogger, _resolve_level


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


def test_level_resolution_is_case_insensitive_and_safe():
    assert _resolve_level("info") == logging.INFO
    assert _resolve_level("WARNING") == logging.WARNING
    assert _resolve_level("not-a-level") == logging.DEBUG


def test_logger_uses_service_namespace_and_structured_context(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    logger = TravelLogger.for_service("PlatformCoverage")
    handler = ListHandler()
    logger._logger.handlers = [handler]

    logger.info("Trip planned", trip_id="trip-1", confidence=0.9)

    assert logger._logger.name == "travelos.PlatformCoverage"
    assert logger._logger.propagate is False
    assert len(handler.records) == 1
    assert handler.records[0].levelno == logging.INFO
    assert (
        handler.records[0].getMessage()
        == "Trip planned | trip_id=trip-1 | confidence=0.9"
    )


def test_logger_reapplies_environment_level(monkeypatch):
    logger = TravelLogger.for_service("DynamicLevelCoverage")
    handler = ListHandler()
    logger._logger.handlers = [handler]

    monkeypatch.setenv("LOG_LEVEL", "ERROR")
    logger.warning("hidden")
    logger.error("visible")

    assert [record.getMessage() for record in handler.records] == ["visible"]


def test_exception_logging_records_type_and_detail(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    logger = TravelLogger.for_service("ExceptionCoverage")
    handler = ListHandler()
    logger._logger.handlers = [handler]

    logger.exception("Provider failed", ValueError("bad response"), provider="test")

    assert len(handler.records) == 1
    assert handler.records[0].levelno == logging.ERROR
    assert handler.records[0].getMessage() == (
        "Provider failed | provider=test | exception=ValueError | "
        "detail=bad response"
    )
