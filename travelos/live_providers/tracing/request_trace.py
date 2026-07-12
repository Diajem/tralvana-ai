"""
Safe request tracing (docs/PROVIDER_OBSERVABILITY.md) — logged through
the existing TravelLogger, never a new logging system. Only the fields
listed in this task's brief are ever logged: internal request id,
provider request id (if available), provider name, capability, start/
end time, latency, and result status. Traveller personal data,
credentials, and full provider payloads are never passed into a trace.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from travelos.intelligence_gateway.provider_status import Capability
from travelos.logging.travel_logger import TravelLogger

_logger = TravelLogger.for_service("ProviderTracing")


@dataclass
class RequestTrace:
    internal_request_id: str
    provider_name: str
    capability: Capability
    started_at: str
    _start_monotonic: float = field(repr=False)
    provider_request_id: str | None = None
    ended_at: str | None = None
    latency_ms: float | None = None
    status: str | None = None

    def finish(self, status: str, provider_request_id: str | None = None) -> None:
        self.ended_at = _now_iso()
        self.latency_ms = (time.monotonic() - self._start_monotonic) * 1000
        self.status = status
        self.provider_request_id = provider_request_id
        _logger.info(
            "Provider request trace",
            internal_request_id=self.internal_request_id,
            provider_request_id=self.provider_request_id or "",
            provider=self.provider_name,
            capability=self.capability.value,
            started_at=self.started_at,
            ended_at=self.ended_at,
            latency_ms=round(self.latency_ms, 1),
            status=self.status,
        )


def start_trace(provider_name: str, capability: Capability) -> RequestTrace:
    return RequestTrace(
        internal_request_id=str(uuid.uuid4()),
        provider_name=provider_name,
        capability=capability,
        started_at=_now_iso(),
        _start_monotonic=time.monotonic(),
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
