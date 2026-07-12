"""
Usage metrics — request/success/failure/rate-limit counts, latency, and
optional cost reporting (docs/PROVIDER_OBSERVABILITY.md). No price is
ever invented here — estimated_cost_usd only accumulates a value a
caller explicitly passes.
"""

from __future__ import annotations

from travelos.live_providers.metrics.provider_metrics import ProviderMetricsTracker


class TestUsageCounts:
    def test_no_snapshot_before_any_activity(self):
        tracker = ProviderMetricsTracker()
        assert tracker.snapshot_for("unknown") is None

    def test_record_success_increments_request_and_success_counts(self):
        tracker = ProviderMetricsTracker()
        tracker.record_success("p", latency_ms=10.0)
        snap = tracker.snapshot_for("p")
        assert snap.request_count == 1
        assert snap.success_count == 1
        assert snap.failure_count == 0

    def test_record_failure_increments_request_and_failure_counts(self):
        tracker = ProviderMetricsTracker()
        tracker.record_failure("p")
        snap = tracker.snapshot_for("p")
        assert snap.request_count == 1
        assert snap.failure_count == 1
        assert snap.success_count == 0

    def test_record_rate_limited_increments_request_and_rate_limited_counts(self):
        tracker = ProviderMetricsTracker()
        tracker.record_rate_limited("p")
        snap = tracker.snapshot_for("p")
        assert snap.request_count == 1
        assert snap.rate_limited_count == 1

    def test_counts_accumulate_across_multiple_calls(self):
        tracker = ProviderMetricsTracker()
        tracker.record_success("p", latency_ms=10.0)
        tracker.record_success("p", latency_ms=20.0)
        tracker.record_failure("p")
        snap = tracker.snapshot_for("p")
        assert snap.request_count == 3
        assert snap.success_count == 2
        assert snap.failure_count == 1

    def test_providers_tracked_independently(self):
        tracker = ProviderMetricsTracker()
        tracker.record_success("a", latency_ms=1.0)
        tracker.record_failure("b")
        assert tracker.snapshot_for("a").success_count == 1
        assert tracker.snapshot_for("b").failure_count == 1


class TestLatency:
    def test_last_latency_reflects_most_recent_call(self):
        tracker = ProviderMetricsTracker()
        tracker.record_success("p", latency_ms=10.0)
        tracker.record_success("p", latency_ms=99.0)
        assert tracker.snapshot_for("p").last_latency_ms == 99.0

    def test_average_latency_only_over_successes(self):
        tracker = ProviderMetricsTracker()
        tracker.record_success("p", latency_ms=10.0)
        tracker.record_success("p", latency_ms=30.0)
        tracker.record_failure("p")
        assert tracker.snapshot_for("p").average_latency_ms == 20.0

    def test_average_latency_zero_when_no_successes(self):
        tracker = ProviderMetricsTracker()
        tracker.record_failure("p")
        assert tracker.snapshot_for("p").average_latency_ms == 0.0


class TestCostReporting:
    def test_no_cost_by_default(self):
        tracker = ProviderMetricsTracker()
        tracker.record_success("p", latency_ms=10.0)
        assert tracker.snapshot_for("p").estimated_cost_usd == 0.0

    def test_cost_accumulates_only_when_explicitly_reported(self):
        tracker = ProviderMetricsTracker()
        tracker.record_success("p", latency_ms=10.0, cost_usd=0.02)
        tracker.record_success("p", latency_ms=10.0, cost_usd=0.03)
        assert tracker.snapshot_for("p").estimated_cost_usd == 0.05

    def test_failures_never_report_cost(self):
        tracker = ProviderMetricsTracker()
        tracker.record_failure("p")
        assert tracker.snapshot_for("p").estimated_cost_usd == 0.0


class TestReset:
    def test_reset_clears_all_snapshots(self):
        tracker = ProviderMetricsTracker()
        tracker.record_success("p", latency_ms=10.0)
        tracker.reset()
        assert tracker.snapshot_for("p") is None
