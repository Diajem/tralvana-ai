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

    def test_natural_holiday_phrase_is_a_plan_trip(self, classifier):
        result = classifier.classify("Please plan a 15-day holiday to New York")
        assert result.intent == Intent.PLAN_TRIP
        assert result.entities["destination"] == "New York"
        assert result.entities["duration_days"] == "15"

    def test_full_planner_brief_with_weather_information_stays_plan_trip(self, classifier):
        result = classifier.classify(
            "Plan a 7-day trip to New York for 2 adults, travelling from Manchester "
            "from 15 September 2026 to 22 September 2026. Both travellers are Irish "
            "citizens. We want weather information and eSIM options."
        )

        assert result.intent == Intent.PLAN_TRIP
        assert result.entities["destination"] == "New York"
        assert result.entities["start_date"] == "2026-09-15"
        assert result.entities["end_date"] == "2026-09-22"

    def test_extracts_jamaica_multi_stay_birthday_and_separate_companion(self, classifier):
        result = classifier.classify(
            "I would like to travel to Jamaica from either London or Manchester "
            "on the 10th of October 2026. I would like to stay in St Mary Parish "
            "near the family. I would like to party with friends on my birthday, "
            "which is the 12th of October, so I would like to stay at the RIU Hotels "
            "in Oshi Rius until the 13th of October. On the 13th I will check out of "
            "the RIU Hotel and would like you to book a budget-friendly hotel for me "
            "for the rest of the trip. My return date to the UK would be the 22nd of "
            "October. I will be meeting my girlfriend, who is travelling from the US "
            "to meet me in Jamaica, and we would also like to visit a few places of "
            "interest within St Mary Parish."
        )

        assert result.intent == Intent.PLAN_TRIP
        assert result.entities["destination"] == "Jamaica"
        assert result.entities["origin"] == "London"
        assert result.entities["departure_options"] == "London,Manchester"
        assert result.entities["start_date"] == "2026-10-10"
        assert result.entities["end_date"] == "2026-10-22"
        assert result.entities["duration_days"] == "12"
        assert result.entities["local_areas"] == "St Mary Parish,Ocho Rios"
        assert result.entities["stay_1_property"] == "RIU Hotel"
        assert result.entities["stay_1_area"] == "Ocho Rios"
        assert result.entities["stay_1_end_date"] == "2026-10-13"
        assert result.entities["stay_2_style"] == "Budget-friendly hotel"
        assert result.entities["stay_2_area"] == "St Mary Parish"
        assert result.entities["stay_2_start_date"] == "2026-10-13"
        assert result.entities["stay_2_end_date"] == "2026-10-22"
        assert result.entities["special_occasion"] == "Birthday"
        assert result.entities["special_occasion_date"] == "2026-10-12"
        assert result.entities["companion_relationship"] == "Girlfriend"
        assert result.entities["companion_origin"] == "United States"
        assert "local attractions" in result.entities["interests"]

    def test_extracts_amsterdam_friends_shared_hotel_and_requested_match(self, classifier):
        result = classifier.classify(
            "Me and my 2 friends are going to Amsterdam for a week from New York; "
            "we would like to stay in the same hotel and would love to see many "
            "tourist attractions in Amsterdam. We would like to visit Ajax stadium "
            "and also would like a ticket to Ajax vs feynold game. We would like to "
            "travel on the 10th of August from New York to Amsterdam for 15 days."
        )

        assert result.intent == Intent.PLAN_TRIP
        assert result.entities["origin"] == "New York"
        assert result.entities["destination"] == "Amsterdam"
        assert result.entities["adults"] == "3"
        assert result.entities["duration_days"] == "15"
        assert result.entities["departure_day"] == "10"
        assert result.entities["date_hint"] == "10 August"
        assert result.entities["date_precision"] == "DAY_WITHOUT_YEAR"
        assert result.entities["shared_hotel"] == "true"
        assert result.entities["requested_event"] == "Ajax vs Feyenoord"
        assert result.entities["ticket_requested"] == "true"
        assert "major attractions" in result.entities["interests"]
        assert "Ajax stadium" in result.entities["interests"]
        assert "soccer" in result.entities["interests"]
        assert result.entities["duration_conflict"] == (
            "Both 7 days and 15 days were supplied; using the later 15-day request."
        )

    def test_modify_trip_intent(self, classifier):
        result = classifier.classify("I need to change my trip")
        assert result.intent == Intent.MODIFY_TRIP
        assert "destination" not in result.entities

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

    def test_flight_search_intent(self, classifier):
        result = classifier.classify("recommend flights to Tokyo")
        assert result.intent == Intent.FLIGHT_SEARCH

    def test_flight_search_find_flights_variant(self, classifier):
        result = classifier.classify("find flights to Paris")
        assert result.intent == Intent.FLIGHT_SEARCH

    def test_fly_to_stays_plan_trip_not_flight_search(self, classifier):
        # "fly to" is a PLAN_TRIP trigger; must not collide with FLIGHT_SEARCH patterns.
        result = classifier.classify("I need to fly to Barcelona next month")
        assert result.intent == Intent.PLAN_TRIP

    def test_change_my_flight_stays_modify_trip(self, classifier):
        # "change my flight" is a MODIFY_TRIP trigger; must not collide with FLIGHT_SEARCH.
        result = classifier.classify("I want to change my flight")
        assert result.intent == Intent.MODIFY_TRIP

    def test_accommodation_search_intent(self, classifier):
        result = classifier.classify("find hotels in Tokyo")
        assert result.intent == Intent.ACCOMMODATION_SEARCH

    def test_accommodation_search_where_to_stay_variant(self, classifier):
        result = classifier.classify("where to stay in Lisbon")
        assert result.intent == Intent.ACCOMMODATION_SEARCH

    def test_different_hotel_stays_modify_trip_not_accommodation_search(self, classifier):
        # "different hotel" is a MODIFY_TRIP trigger; must not collide with ACCOMMODATION_SEARCH.
        result = classifier.classify("I need a different hotel")
        assert result.intent == Intent.MODIFY_TRIP

    def test_affordable_hotels_stays_budget_advice(self, classifier):
        # "affordable hotels" is a BUDGET_ADVICE trigger; must not collide with ACCOMMODATION_SEARCH.
        result = classifier.classify("affordable hotels in Paris")
        assert result.intent == Intent.BUDGET_ADVICE

    def test_destination_discovery_intent(self, classifier):
        result = classifier.classify("where should i go")
        assert result.intent == Intent.DESTINATION_DISCOVERY

    def test_destination_discovery_things_to_do_variant(self, classifier):
        result = classifier.classify("things to do in Tokyo")
        assert result.intent == Intent.DESTINATION_DISCOVERY

    def test_tell_me_about_stays_destination_question(self, classifier):
        # "tell me about" is a DESTINATION_QUESTION trigger; must not collide with DESTINATION_DISCOVERY.
        result = classifier.classify("Tell me about Tokyo")
        assert result.intent == Intent.DESTINATION_QUESTION

    def test_travel_tips_stays_travel_advice_not_destination_discovery(self, classifier):
        # Bare "recommend"/"suggest" live under TRAVEL_ADVICE; DESTINATION_DISCOVERY
        # must be checked first so its own specific phrases win, without swallowing
        # unrelated "recommend"/"suggest" uses elsewhere.
        result = classifier.classify("What are the best travel tips for Japan?")
        assert result.intent == Intent.TRAVEL_ADVICE

    def test_budget_analysis_intent(self, classifier):
        result = classifier.classify("compare budget options for Tokyo")
        assert result.intent == Intent.BUDGET_ANALYSIS

    def test_budget_analysis_recommend_a_budget_variant(self, classifier):
        result = classifier.classify("recommend a budget for my trip")
        assert result.intent == Intent.BUDGET_ANALYSIS

    def test_visa_check_do_i_need_a_visa(self, classifier):
        result = classifier.classify("Do I need a visa?")
        assert result.intent == Intent.VISA_CHECK

    def test_visa_check_recognises_the_united_states(self, classifier):
        result = classifier.classify(
            "Do Irish citizens need a visa for the United States?"
        )
        assert result.intent == Intent.VISA_CHECK
        assert result.entities["nationality"] == "Irish"
        assert result.entities["destination"] == "United States"

    def test_visa_check_can_i_enter(self, classifier):
        result = classifier.classify("Can I enter Japan?")
        assert result.intent == Intent.VISA_CHECK
        assert result.entities.get("destination") == "Japan"

    def test_visa_check_passport_work(self, classifier):
        result = classifier.classify("Will my Irish passport work?")
        assert result.intent == Intent.VISA_CHECK
        assert result.entities.get("nationality") == "Irish"

    def test_visa_check_nationality_and_destination_fallback(self, classifier):
        # No explicit visa keyword — inferred from stating both nationality
        # and a destination, which has no other clear intent in this layer.
        result = classifier.classify("I am Nigerian travelling to Spain.")
        assert result.intent == Intent.VISA_CHECK
        assert result.entities.get("nationality") == "Nigerian"
        assert result.entities.get("destination") == "Spain"

    def test_visa_requirements_for_now_routes_to_visa_check(self, classifier):
        # Reclaimed from DESTINATION_QUESTION — a new, more specific intent.
        result = classifier.classify("visa requirements for Japan")
        assert result.intent == Intent.VISA_CHECK

    def test_nationality_alone_without_destination_does_not_trigger_visa_check(self, classifier):
        result = classifier.classify("I am Nigerian")
        assert result.intent == Intent.GENERAL_CONVERSATION

    def test_weather_analysis_good_time_to_visit(self, classifier):
        result = classifier.classify("Is July a good time to visit Japan?")
        assert result.intent == Intent.WEATHER_ANALYSIS
        assert result.entities.get("destination") == "Japan"
        assert result.entities.get("month") == "7"

    def test_weather_analysis_when_should_i_visit(self, classifier):
        result = classifier.classify("When should I visit Spain?")
        assert result.intent == Intent.WEATHER_ANALYSIS
        assert result.entities.get("destination") == "Spain"

    def test_weather_analysis_will_it_rain(self, classifier):
        result = classifier.classify("Will it rain in Jamaica in September?")
        assert result.intent == Intent.WEATHER_ANALYSIS
        assert result.entities.get("destination") == "Jamaica"
        assert result.entities.get("month") == "9"

    def test_weather_analysis_hurricane_season(self, classifier):
        result = classifier.classify("Should I avoid hurricane season?")
        assert result.intent == Intent.WEATHER_ANALYSIS

    def test_weather_in_now_routes_to_weather_analysis(self, classifier):
        # Reclaimed from DESTINATION_QUESTION — a new, more specific intent.
        result = classifier.classify("weather in Tokyo")
        assert result.intent == Intent.WEATHER_ANALYSIS

    def test_natural_weather_question_routes_to_weather_analysis(self, classifier):
        result = classifier.classify(
            "What is the weather like in Barcelona in November?"
        )
        assert result.intent == Intent.WEATHER_ANALYSIS
        assert result.entities.get("destination") == "Barcelona"
        assert result.entities.get("month") == "11"

    def test_best_time_to_visit_now_routes_to_weather_analysis(self, classifier):
        # Reclaimed from TRAVEL_ADVICE — a new, more specific intent.
        result = classifier.classify("best time to visit Barcelona")
        assert result.intent == Intent.WEATHER_ANALYSIS

    def test_rain_word_does_not_falsely_match_in_marker(self, classifier):
        # Regression: "rain" contains "in " as a substring; the destination
        # marker search must not match inside it.
        result = classifier.classify("will it rain in london")
        assert result.entities.get("destination") == "London"

    def test_how_expensive_stays_budget_advice_not_budget_analysis(self, classifier):
        # "how expensive" is a BUDGET_ADVICE trigger; must not collide with
        # BUDGET_ANALYSIS's more specific tier-comparison phrasing.
        result = classifier.classify("how expensive is Tokyo")
        assert result.intent == Intent.BUDGET_ADVICE


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

    def test_extracts_date_hint_from_explicit_date_range(self, classifier):
        result = classifier.classify(
            "We want to travel from 10 August to 17 August 2026"
        )
        assert result.entities.get("date_hint") == "10 august to 17 august 2026"

    def test_extracts_detailed_group_trip_facts(self, classifier):
        result = classifier.classify(
            "We are travelling from Leeds, we are British and Nigerian, and we like "
            "beaches, culture, food and music."
        )
        assert result.entities["origin"] == "Leeds"
        assert result.entities["nationality"] == "British"
        assert result.entities["nationalities"] == "British,Nigerian"
        assert result.entities["interests"] == "beaches,culture,food,music"

    def test_origin_stops_at_a_second_from_for_date_range(self, classifier):
        result = classifier.classify(
            "Plan a holiday to Montego Bay from Leeds from 4 October 2026 "
            "to 11 October 2026 for 2 British adults."
        )
        assert result.entities["origin"] == "Leeds"

    def test_extracts_nationality_from_both_travellers_phrase(self, classifier):
        result = classifier.classify(
            "Plan a trip to New York. Both travellers are Irish citizens."
        )
        assert result.entities["nationality"] == "Irish"

    def test_extracts_exact_dates_duration_and_adult_count(self, classifier):
        result = classifier.classify(
            "We want to travel from 10 August to 17 August 2026 with 2 adults"
        )
        assert result.entities["start_date"] == "2026-08-10"
        assert result.entities["end_date"] == "2026-08-17"
        assert result.entities["duration_days"] == "7"
        assert result.entities["adults"] == "2"

    def test_extracts_full_new_york_holiday_details(self, classifier):
        result = classifier.classify(
            "Plan a 15-day holiday to New York with my partner from 7 August "
            "to 22 August 2026. We are travelling from Leeds but do not mind "
            "flying from Manchester or London. We are both British nationals. "
            "We love to dine out and stay in an average hotel. She loves fashion "
            "and I like soccer and places of significant interest."
        )
        assert result.entities["destination"] == "New York"
        assert result.entities["origin"] == "Manchester"
        assert result.entities["home_origin"] == "Leeds"
        assert result.entities["departure_options"] == "Manchester,London"
        assert result.entities["nationality"] == "British"
        assert result.entities["adults"] == "2"
        assert result.entities["start_date"] == "2026-08-07"
        assert result.entities["end_date"] == "2026-08-22"
        assert result.entities["duration_days"] == "15"
        assert result.entities["accommodation_type"] == "HOTEL"
        assert {"dining", "fashion", "soccer", "major attractions"}.issubset(
            set(result.entities["interests"].split(","))
        )

    def test_extracts_count_and_nationality_from_described_adults(self, classifier):
        result = classifier.classify(
            "Plan a 15 day trip to New York from Manchester on 7 August 2026 "
            "for 2 British adults."
        )

        assert result.entities["adults"] == "2"
        assert result.entities["nationality"] == "British"

    def test_extracts_two_week_dublin_trip_without_treating_name_as_nationality(
        self, classifier
    ):
        result = classifier.classify(
            "I am Desmond. Plan a relaxing holiday to Dublin from Bradford "
            "on 17 August 2026 for two weeks with 2 adults and 2 children."
        )
        assert result.entities["destination"] == "Dublin"
        assert result.entities["origin"] == "Bradford"
        assert result.entities["duration_days"] == "14"
        assert result.entities["start_date"] == "2026-08-17"
        assert result.entities["end_date"] == "2026-08-31"
        assert result.entities["adults"] == "2"
        assert result.entities["children"] == "2"
        assert "nationality" not in result.entities

    @pytest.mark.parametrize(
        ("phrase", "expected_days"),
        [
            ("four days", "4"),
            ("14 days", "14"),
            ("two weeks", "14"),
            ("a fortnight", "14"),
        ],
    )
    def test_extracts_duration_variants(self, classifier, phrase, expected_days):
        result = classifier.classify(
            f"Plan a trip to Dublin in August for {phrase}"
        )
        assert result.entities["duration_days"] == expected_days

    def test_no_destination_when_not_present(self, classifier):
        # "Hello there" has no location markers
        result = classifier.classify("Hello there")
        assert "destination" not in result.entities or not result.entities["destination"]

    def test_skips_short_destination_words(self, classifier):
        result = classifier.classify("Travel to me")
        assert result.entities.get("destination") is None

    def test_flight_search_extracts_destination(self, classifier):
        result = classifier.classify("find flights to Singapore")
        assert result.entities.get("destination") == "Singapore"

    def test_accommodation_search_extracts_destination(self, classifier):
        result = classifier.classify("find hotels in Singapore")
        assert result.entities.get("destination") == "Singapore"

    def test_place_to_stay_does_not_extract_stay_as_destination(self, classifier):
        # "to stay" must not be misread as "destination: Stay" via the generic "to " marker.
        result = classifier.classify("find me a place to stay")
        assert result.entities.get("destination") is None

    def test_destination_discovery_extracts_destination(self, classifier):
        result = classifier.classify("things to do in Singapore")
        assert result.entities.get("destination") == "Singapore"
