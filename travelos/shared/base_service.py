from __future__ import annotations

from abc import ABC


class BaseService(ABC):
    """
    Base class for all TravelOS services.

    Provides a consistent identity and lazy access to the platform logger
    without forcing a constructor signature on subclasses.
    """

    @property
    def service_name(self) -> str:
        return self.__class__.__name__

    @property
    def logger(self):
        from travelos.logging.travel_logger import TravelLogger
        return TravelLogger.for_service(self.service_name)
