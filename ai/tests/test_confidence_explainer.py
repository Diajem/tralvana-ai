"""Confidence bands and reduction reasons — docs/EXPLAINABILITY_ENGINE.md."""

from __future__ import annotations

from ai.explainability import confidence_explainer
from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus


class TestConfidenceBands:
    def test_very_high_band(self):
        assert confidence_explainer.band_label(0.95) == "Very high confidence"
        assert confidence_explainer.band_label(0.90) == "Very high confidence"

    def test_high_band(self):
        assert confidence_explainer.band_label(0.80) == "High confidence"
        assert confidence_explainer.band_label(0.75) == "High confidence"

    def test_moderate_band(self):
        assert confidence_explainer.band_label(0.65) == "Moderate confidence"
        assert confidence_explainer.band_label(0.60) == "Moderate confidence"

    def test_low_band(self):
        assert confidence_explainer.band_label(0.50) == "Low confidence"
        assert confidence_explainer.band_label(0.40) == "Low confidence"

    def test_very_low_band(self):
        assert confidence_explainer.band_label(0.39) == "Very low confidence"
        assert confidence_explainer.band_label(0.0) == "Very low confidence"

    def test_band_boundaries_are_inclusive_of_lower_bound(self):
        # 0.90 exactly is "Very high", 0.8999 is "High" — the band a value
        # falls into never depends on floating-point rounding surprises.
        assert confidence_explainer.band_label(0.8999) == "High confidence"


class TestConfidenceReductionReasons:
    def test_no_reasons_when_nothing_reduced_it(self):
        r = AgentResult(agent_name="x", status=AgentStatus.SUCCESS, confidence=1.0)
        text = confidence_explainer.explain(1.0, [r])
        assert text == "Very high confidence (1.00)."

    def test_partial_module_failure_named(self):
        r = AgentResult(agent_name="x", status=AgentStatus.SUCCESS, confidence=0.7)
        text = confidence_explainer.explain(0.7, [r], modules_failed=["weather"])
        assert "weather" in text
        assert "could not be completed" in text

    def test_conflicting_results_named(self):
        r = AgentResult(agent_name="x", status=AgentStatus.SUCCESS, confidence=0.7)
        text = confidence_explainer.explain(0.7, [r], conflicts=["a vs b"])
        assert "disagreed" in text

    def test_missing_traveller_information_category_detected(self):
        r = AgentResult(
            agent_name="x", status=AgentStatus.SUCCESS, confidence=0.6,
            assumptions=["No traveller profile linked — scoring uses default preferences only."],
        )
        text = confidence_explainer.explain(0.6, [r])
        assert "missing traveller information" in text

    def test_mock_data_category_detected(self):
        r = AgentResult(
            agent_name="x", status=AgentStatus.SUCCESS, confidence=0.6,
            assumptions=["Prices and schedules are deterministic mock data — no live inventory was queried."],
        )
        text = confidence_explainer.explain(0.6, [r])
        assert "mock or incomplete provider data" in text

    def test_unknown_destination_category_detected(self):
        r = AgentResult(
            agent_name="x", status=AgentStatus.SUCCESS, confidence=0.5,
            assumptions=["Destination not in the mock catalogue — using default assumptions."],
        )
        text = confidence_explainer.explain(0.5, [r])
        assert "unknown destination or rule" in text

    def test_generic_assumption_reason_when_uncategorized(self):
        r = AgentResult(
            agent_name="x", status=AgentStatus.SUCCESS, confidence=0.8,
            assumptions=["An assumption that doesn't match any known category."],
        )
        text = confidence_explainer.explain(0.8, [r])
        assert "assumptions were applied" in text

    def test_deterministic_output(self):
        r = AgentResult(agent_name="x", status=AgentStatus.SUCCESS, confidence=0.6, assumptions=["No profile."])
        first = confidence_explainer.explain(0.6, [r], modules_failed=["weather"], conflicts=["c"])
        second = confidence_explainer.explain(0.6, [r], modules_failed=["weather"], conflicts=["c"])
        assert first == second
