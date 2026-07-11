"""Per-provider rate limiting — remaining quota, reset time — docs/CACHING_AND_FAILOVER.md."""

from __future__ import annotations

import time

from travelos.intelligence_gateway.rate_limit_policy import RateLimitTracker


class TestUnconfiguredProvider:
    def test_unconfigured_provider_always_allowed(self):
        tracker = RateLimitTracker()
        assert tracker.check("no_limit_provider") is True

    def test_unconfigured_provider_has_no_status(self):
        tracker = RateLimitTracker()
        assert tracker.status_for("no_limit_provider") is None


class TestConfiguredLimits:
    def test_calls_allowed_up_to_the_limit(self):
        tracker = RateLimitTracker()
        tracker.configure("p", limit=2, window_seconds=60)
        assert tracker.check("p") is True
        tracker.record_call("p")
        assert tracker.check("p") is True
        tracker.record_call("p")
        assert tracker.check("p") is False

    def test_remaining_quota_decrements_per_call(self):
        tracker = RateLimitTracker()
        tracker.configure("p", limit=3, window_seconds=60)
        tracker.record_call("p")
        state = tracker.status_for("p")
        assert state.remaining == 2

    def test_record_call_past_zero_does_not_go_negative(self):
        tracker = RateLimitTracker()
        tracker.configure("p", limit=1, window_seconds=60)
        tracker.record_call("p")
        tracker.record_call("p")  # already exhausted
        assert tracker.status_for("p").remaining == 0

    def test_reset_time_is_in_the_future_when_configured(self):
        tracker = RateLimitTracker()
        tracker.configure("p", limit=5, window_seconds=60)
        state = tracker.status_for("p")
        assert state.reset_at is not None


class TestWindowReset:
    def test_quota_replenishes_after_window_elapses(self):
        tracker = RateLimitTracker()
        tracker.configure("p", limit=1, window_seconds=0.01)
        tracker.record_call("p")
        assert tracker.check("p") is False
        time.sleep(0.02)
        assert tracker.check("p") is True

    def test_reconfigure_clears_prior_state(self):
        tracker = RateLimitTracker()
        tracker.configure("p", limit=1, window_seconds=60)
        tracker.record_call("p")
        assert tracker.check("p") is False
        tracker.configure("p", limit=5, window_seconds=60)
        assert tracker.check("p") is True


class TestReset:
    def test_reset_clears_all_provider_state(self):
        tracker = RateLimitTracker()
        tracker.configure("p", limit=1, window_seconds=60)
        tracker.record_call("p")
        tracker.reset()
        assert tracker.check("p") is True
