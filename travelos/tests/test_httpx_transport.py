"""
HttpxTransport (T-037) — TransportRequest/TransportResponse translation
against httpx's own `MockTransport` (built into httpx, no new
dependency, no real socket ever opened). Never asserts on or uses a
real credential — the "Authorization" header value used below is a
fixed test fixture string, not a live token.
"""

from __future__ import annotations

import httpx
import pytest

from travelos.live_providers.httpx_transport import HttpxTransport
from travelos.live_providers.transport import TransportRequest


def _client_returning(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


class TestRequestTranslation:
    def test_method_url_headers_and_json_body_are_forwarded(self):
        captured: dict[str, httpx.Request] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["request"] = request
            return httpx.Response(200, json={"ok": True})

        transport = HttpxTransport(client=_client_returning(handler))
        transport.send(
            TransportRequest(
                method="POST",
                url="https://api.duffel.test/air/offer_requests",
                headers={"Authorization": "Bearer test-fixture-token", "Duffel-Version": "v2"},
                json_body={"data": {"slices": []}},
                timeout_seconds=5.0,
            )
        )

        sent = captured["request"]
        assert sent.method == "POST"
        assert str(sent.url) == "https://api.duffel.test/air/offer_requests"
        assert sent.headers["authorization"] == "Bearer test-fixture-token"
        assert sent.headers["duffel-version"] == "v2"

    def test_query_params_are_forwarded(self):
        captured: dict[str, httpx.Request] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["request"] = request
            return httpx.Response(200, json={})

        transport = HttpxTransport(client=_client_returning(handler))
        transport.send(
            TransportRequest(
                method="GET",
                url="https://api.example.test/search",
                query_params={"origin": "LHR", "destination": "JFK"},
            )
        )

        sent = captured["request"]
        assert sent.url.params["origin"] == "LHR"
        assert sent.url.params["destination"] == "JFK"

    def test_empty_query_params_omit_the_params_kwarg_cleanly(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={})

        transport = HttpxTransport(client=_client_returning(handler))
        # Would raise if HttpxTransport mishandled an empty dict.
        result = transport.send(TransportRequest(method="GET", url="https://api.example.test/ping"))
        assert result.status_code == 200


class TestResponseTranslation:
    def test_json_body_is_parsed(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"data": {"offers": []}})

        transport = HttpxTransport(client=_client_returning(handler))
        result = transport.send(TransportRequest(method="GET", url="https://api.example.test/x"))
        assert result.status_code == 200
        assert result.body == {"data": {"offers": []}}

    def test_non_json_body_falls_back_to_text(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="not json")

        transport = HttpxTransport(client=_client_returning(handler))
        result = transport.send(TransportRequest(method="GET", url="https://api.example.test/x"))
        assert result.body == "not json"

    def test_status_code_and_headers_are_carried_through(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(422, json={"errors": []}, headers={"X-Request-Id": "abc-123"})

        transport = HttpxTransport(client=_client_returning(handler))
        result = transport.send(TransportRequest(method="POST", url="https://api.example.test/x"))
        assert result.status_code == 422
        assert result.headers["x-request-id"] == "abc-123"

    def test_latency_ms_is_non_negative(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={})

        transport = HttpxTransport(client=_client_returning(handler))
        result = transport.send(TransportRequest(method="GET", url="https://api.example.test/x"))
        assert result.latency_ms >= 0


class TestClientLifecycle:
    def test_close_closes_a_self_owned_client(self):
        transport = HttpxTransport()
        transport.close()
        with pytest.raises(RuntimeError):
            transport._client.request("GET", "https://api.example.test/x")

    def test_close_never_closes_a_caller_supplied_client(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={})

        client = _client_returning(handler)
        transport = HttpxTransport(client=client)
        transport.close()
        # Caller-supplied client must still work — HttpxTransport doesn't own it.
        response = client.request("GET", "https://api.example.test/x")
        assert response.status_code == 200


class TestNeverExposesCredentials:
    def test_response_object_never_echoes_the_request_authorization_header(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"ok": True})

        transport = HttpxTransport(client=_client_returning(handler))
        result = transport.send(
            TransportRequest(
                method="GET",
                url="https://api.example.test/x",
                headers={"Authorization": "Bearer test-fixture-token"},
            )
        )
        assert "test-fixture-token" not in str(result.headers)
        assert "test-fixture-token" not in str(result.body)
