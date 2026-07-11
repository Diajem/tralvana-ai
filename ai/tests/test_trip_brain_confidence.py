from ai.trip_brain.confidence import aggregate_confidence


class TestAggregateConfidence:
    def test_no_selected_modules_returns_zero(self):
        assert aggregate_confidence({}, {}, []) == 0.0

    def test_all_succeeded_no_penalty(self):
        confidences = {"flight": 0.8, "weather": 0.6}
        weights = {"flight": 1.0, "weather": 1.0}
        result = aggregate_confidence(confidences, weights, ["flight", "weather"])
        assert result == 0.7  # simple average, weights equal, full completion

    def test_weighted_average_favours_higher_weight_module(self):
        confidences = {"flight": 0.9, "budget": 0.3}
        weights = {"flight": 1.0, "budget": 0.7}
        result = aggregate_confidence(confidences, weights, ["flight", "budget"])
        expected = round((0.9 * 1.0 + 0.3 * 0.7) / 1.7, 2)
        assert result == expected

    def test_partial_completion_applies_penalty(self):
        confidences = {"flight": 0.8, "weather": 0.6}
        weights = {"flight": 1.0, "weather": 1.0}
        # weather failed — only flight succeeded
        result = aggregate_confidence(confidences, weights, ["flight"])
        # base = 0.8 (only flight contributes), penalty = 1/2
        assert result == round(0.8 * 0.5, 2)

    def test_total_failure_returns_zero(self):
        confidences = {"flight": 0.8, "weather": 0.6}
        weights = {"flight": 1.0, "weather": 1.0}
        result = aggregate_confidence(confidences, weights, [])
        assert result == 0.0

    def test_fully_succeeded_three_module_request_not_penalized(self):
        confidences = {"flight": 0.8, "weather": 0.6, "visa": 0.9}
        weights = {"flight": 1.0, "weather": 1.0, "visa": 0.7}
        result = aggregate_confidence(confidences, weights, ["flight", "weather", "visa"])
        base = (0.8 * 1.0 + 0.6 * 1.0 + 0.9 * 0.7) / (1.0 + 1.0 + 0.7)
        assert result == round(base, 2)
