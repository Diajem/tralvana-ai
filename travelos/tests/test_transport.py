"""FakeTransport — deterministic, in-memory, never a real network call."""

from __future__ import annotations

from travelos.live_providers.transport import FakeTransport, TransportRequest, TransportResponse


def _request(**overrides) -> TransportRequest:
    defaults = dict(method="GET", url="https://example.invalid/x")
    defaults.update(overrides)
    return TransportRequest(**defaults)


class TestFakeTransport:
    def test_default_responder_returns_200(self):
        transport = FakeTransport()
        response = transport.send(_request())
        assert response.status_code == 200

    def test_records_every_sent_request(self):
        transport = FakeTransport()
        transport.send(_request(url="https://example.invalid/a"))
        transport.send(_request(url="https://example.invalid/b"))
        assert len(transport.sent_requests) == 2
        assert transport.sent_requests[0].url == "https://example.invalid/a"
        assert transport.sent_requests[1].url == "https://example.invalid/b"

    def test_always_returning_ignores_request_content(self):
        transport = FakeTransport.always_returning(status_code=503, body={"error": "down"})
        r1 = transport.send(_request(method="GET"))
        r2 = transport.send(_request(method="POST", json_body={"a": 1}))
        assert r1.status_code == 503
        assert r2.status_code == 503
        assert r1.body == {"error": "down"}

    def test_custom_responder_receives_the_request(self):
        captured = []

        def responder(request: TransportRequest) -> TransportResponse:
            captured.append(request)
            return TransportResponse(status_code=200, body={"echo": request.query_params})

        transport = FakeTransport(responder=responder)
        response = transport.send(_request(query_params={"q": "1"}))
        assert captured[0].query_params == {"q": "1"}
        assert response.body == {"echo": {"q": "1"}}

    def test_supports_get_and_post_methods(self):
        transport = FakeTransport()
        get_response = transport.send(_request(method="GET"))
        post_response = transport.send(_request(method="POST", json_body={"a": 1}))
        assert get_response.status_code == 200
        assert post_response.status_code == 200

    def test_headers_and_timeout_preserved_on_the_request(self):
        transport = FakeTransport()
        transport.send(_request(headers={"X-Test": "1"}, timeout_seconds=5.0))
        sent = transport.sent_requests[0]
        assert sent.headers == {"X-Test": "1"}
        assert sent.timeout_seconds == 5.0

    def test_no_real_network_call_is_possible(self):
        # There is no socket/requests/httpx call anywhere in FakeTransport —
        # this is a structural guarantee, not a runtime one, verified here
        # by confirming a request to an unroutable .invalid host still
        # "succeeds" instantly (a real transport would raise a DNS error).
        import time
        transport = FakeTransport()
        start = time.monotonic()
        response = transport.send(_request(url="https://this-host-does-not-exist.invalid/x"))
        elapsed = time.monotonic() - start
        assert response.status_code == 200
        assert elapsed < 0.1  # a real DNS lookup/timeout would take far longer
