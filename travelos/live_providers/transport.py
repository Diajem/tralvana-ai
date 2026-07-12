"""
HTTP transport abstraction — provider adapters depend on this interface,
never on a specific HTTP library, so the library can change without
touching any adapter (docs/LIVE_PROVIDER_FRAMEWORK.md). Only
`FakeTransport` is implemented here — a real transport (e.g. an `httpx`-
backed one) is deliberately deferred; see docs/ADR/ADR-021-live-provider-framework.md's
Deferred Items. No live network request is made anywhere in this module.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class TransportRequest:
    method: str  # "GET" | "POST"
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    query_params: dict[str, str] = field(default_factory=dict)
    json_body: dict[str, Any] | None = None
    timeout_seconds: float = 10.0


@dataclass
class TransportResponse:
    status_code: int
    body: Any = None
    headers: dict[str, str] = field(default_factory=dict)
    latency_ms: float = 0.0


class Transport(ABC):
    """One method — send a request, get a response. Nothing about
    `BaseLiveProvider` depends on how `send()` is implemented."""

    @abstractmethod
    def send(self, request: TransportRequest) -> TransportResponse: ...


class FakeTransport(Transport):
    """
    Deterministic, in-memory transport for tests and the example template
    (docs/LIVE_PROVIDER_ADAPTER_GUIDE.md). Never opens a socket. Records
    every request it was asked to send so tests can assert on request
    mapping without a real server.
    """

    def __init__(self, responder: Callable[[TransportRequest], TransportResponse] | None = None) -> None:
        self._responder = responder or self._default_responder
        self.sent_requests: list[TransportRequest] = []

    def send(self, request: TransportRequest) -> TransportResponse:
        self.sent_requests.append(request)
        return self._responder(request)

    @staticmethod
    def _default_responder(request: TransportRequest) -> TransportResponse:
        return TransportResponse(status_code=200, body={}, headers={})

    @classmethod
    def always_returning(cls, status_code: int, body: Any = None, headers: dict[str, str] | None = None) -> "FakeTransport":
        """Convenience constructor for the common "every call gets this
        one canned response" test case."""
        response = TransportResponse(status_code=status_code, body=body, headers=headers or {})
        return cls(responder=lambda request: response)
