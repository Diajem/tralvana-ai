"""
HttpxTransport — the first real (non-fake) Transport implementation
(T-037), closing TD-021. Implements the same `Transport.send(TransportRequest)
-> TransportResponse` interface `FakeTransport` already implements —
`BaseLiveProvider` and every concrete provider (e.g. `DuffelFlightProvider`)
are unaware which concrete `Transport` they were constructed with, per
docs/LIVE_PROVIDER_FRAMEWORK.md's dependency-inversion design.

No provider-specific logic lives here — this is a plain HTTP client
adapter, nothing Duffel-specific. `httpx` is already a pinned dependency
(services/api/requirements.txt, `httpx==0.28.1`), used elsewhere via
FastAPI's TestClient — no new third-party dependency is introduced.
"""

from __future__ import annotations

import httpx

from travelos.live_providers.transport import Transport, TransportRequest, TransportResponse


class HttpxTransport(Transport):
    """A synchronous `httpx.Client`-backed Transport. Safe by construction
    against the credential-exposure rules `BaseLiveProvider` already
    follows — this class never reads a `SecretReference` itself; it only
    ever forwards whatever headers `TransportRequest.headers` already
    contains (assembled by `execute()`, upstream of this class)."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client()
        self._owns_client = client is None

    def send(self, request: TransportRequest) -> TransportResponse:
        response = self._client.request(
            method=request.method,
            url=request.url,
            headers=request.headers,
            params=request.query_params or None,
            json=request.json_body,
            timeout=request.timeout_seconds,
        )
        return TransportResponse(
            status_code=response.status_code,
            body=_parse_body(response),
            headers=dict(response.headers),
            latency_ms=_elapsed_ms(response),
        )

    def close(self) -> None:
        """Only closes a client this instance created itself — a caller-
        supplied client (e.g. shared across transports, or a test's
        MockTransport-backed client) is the caller's to close."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "HttpxTransport":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


def _parse_body(response: httpx.Response) -> object:
    try:
        return response.json()
    except ValueError:
        return response.text


def _elapsed_ms(response: httpx.Response) -> float:
    # `.elapsed` is only populated after the real timing hooks fire on a
    # genuine network transport — a synthetic response (e.g. httpx's own
    # MockTransport, used by this package's tests) never sets it.
    try:
        return response.elapsed.total_seconds() * 1000
    except RuntimeError:
        return 0.0
