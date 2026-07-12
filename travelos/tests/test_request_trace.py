"""
Request tracing — internal request id, provider request id, provider
name, capability, start/end time, latency, and result status, logged via
the existing TravelLogger only (docs/PROVIDER_OBSERVABILITY.md). Never
traveller personal data, credentials, or a full provider payload.
"""

from __future__ import annotations

from travelos.intelligence_gateway.provider_status import Capability
from travelos.live_providers.tracing.request_trace import start_trace


class TestRequestTrace:
    def test_start_trace_assigns_an_internal_request_id(self):
        trace = start_trace("p", Capability.FLIGHTS)
        assert trace.internal_request_id != ""

    def test_each_trace_gets_a_unique_internal_request_id(self):
        t1 = start_trace("p", Capability.FLIGHTS)
        t2 = start_trace("p", Capability.FLIGHTS)
        assert t1.internal_request_id != t2.internal_request_id

    def test_started_at_set_immediately(self):
        trace = start_trace("p", Capability.FLIGHTS)
        assert trace.started_at != ""
        assert trace.ended_at is None

    def test_finish_sets_ended_at_latency_and_status(self):
        trace = start_trace("p", Capability.FLIGHTS)
        trace.finish(status="AVAILABLE")
        assert trace.ended_at is not None
        assert trace.latency_ms is not None
        assert trace.latency_ms >= 0
        assert trace.status == "AVAILABLE"

    def test_finish_can_record_a_provider_request_id(self):
        trace = start_trace("p", Capability.FLIGHTS)
        trace.finish(status="AVAILABLE", provider_request_id="vendor-req-42")
        assert trace.provider_request_id == "vendor-req-42"

    def test_provider_request_id_optional(self):
        trace = start_trace("p", Capability.FLIGHTS)
        trace.finish(status="error")
        assert trace.provider_request_id is None

    def test_provider_name_and_capability_recorded(self):
        trace = start_trace("mock_flight_provider", Capability.FLIGHTS)
        assert trace.provider_name == "mock_flight_provider"
        assert trace.capability == Capability.FLIGHTS
