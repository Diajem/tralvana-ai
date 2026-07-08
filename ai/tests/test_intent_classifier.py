import pytest

from ai.concierge.intent_classifier import Intent, IntentClassifier


@pytest.fixture
def classifier() -> IntentClassifier:
    return IntentClassifier()


class TestIntentClassification:
    def test_plan_trip_intent(self, classifier):
        result = classifier.classify("I want to plan a trip to Tokyo")
        assert result.intent == Intent.PLAN_TRIP
        assert result.confidence > 0

    def test_plan_trip_fly_variant(self, classifier):
        result = classifier.classify("I need to fly to Barcelona next month")
        assert result.intent == Intent.PLAN_TRIP

    def test_modify_trip_intent(self, classifier):
        result = classifier.classify("I need to change my trip")
        assert result.intent == Intent.MODIFY_TRIP

    def test_view_profile_intent(self, classifier):
        result = classifier.classify("Show me my profile")
        assert result.intent == Intent.VIEW_PROFILE

    def test_update_preferences_intent(self, classifier):
        result = classifier.classify("I prefer window seats")
        assert result.intent == Intent.UPDATE_PREFERENCES

    def test_destination_question_intent(self, classifier):
        result = classifier.classify("Tell me about Tokyo")
        assert result.intent == Intent.DESTINATION_QUESTION

    def test_travel_advice_intent(self, classifier):
        # "travel tips" matches TRAVEL_ADVICE; "visit" alone would match PLAN_TRIP first
        result = classifier.classify("What are the best travel tips for Japan?")
        assert result.intent == Intent.TRAVEL_ADVICE

    def test_budget_advice_intent(self, classifier):
        # "how expensive" matches BUDGET_ADVICE; "cost to travel to" would match PLAN_TRIP first
        result = classifier.classify("How expensive is Dubai?")
        assert result.intent == Intent.BUDGET_ADVICE

    def test_general_conversation_fallback(self, classifier):
        result = classifier.classify("Hello there")
        assert result.intent == Intent.GENERAL_CONVERSATION
        assert result.confidence == 1.0

    def test_case_insensitive(self, classifier):
        lower = classifier.classify("i want to travel to paris")
        upper = classifier.classify("I WANT TO TRAVEL TO PARIS")
        assert lower.intent == upper.intent


class TestEntityExtraction:
    def test_extracts_destination(self, classifier):
        # "I'm going to Tokyo" → extractor finds "to Tokyo" directly
        result = classifier.classify("I'm going to Tokyo")
        assert result.entities.get("destination") == "Tokyo"

    def test_extracts_date_hint_month(self, classifier):
        result = classifier.classify("I want to go to Paris in october")
        assert result.entities.get("date_hint") == "in october"

    def test_extracts_date_hint_next_month(self, classifier):
        result = classifier.classify("I want to visit London next month")
        assert result.entities.get("date_hint") == "next month"

    def test_no_destination_when_not_present(self, classifier):
        # "Hello there" has no location markers
        result = classifier.classify("Hello there")
        assert "destination" not in result.entities or not result.entities["destination"]

    def test_skips_short_destination_words(self, classifier):
        result = classifier.classify("Travel to me")
        assert result.entities.get("destination") is None
