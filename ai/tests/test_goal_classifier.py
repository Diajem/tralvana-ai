from ai.goals.goal_classifier import GoalClassifier


def test_staying_near_family_does_not_imply_children_are_travelling() -> None:
    classifier = GoalClassifier()

    assert classifier.classify_from_text(
        "I would like to stay in St Mary Parish near the family."
    ) == "GENERAL_TRAVEL"


def test_explicit_family_party_still_selects_family_trip() -> None:
    classifier = GoalClassifier()

    assert classifier.classify_from_text(
        "Plan a family holiday to Jamaica with my children."
    ) == "FAMILY_TRIP"


def test_meeting_a_girlfriend_does_not_imply_business_travel() -> None:
    classifier = GoalClassifier()

    assert classifier.classify_from_text(
        "I will be meeting my girlfriend, who is travelling from the US."
    ) == "GENERAL_TRAVEL"


def test_explicit_client_meeting_still_selects_business_travel() -> None:
    classifier = GoalClassifier()

    assert classifier.classify_from_text(
        "I have a client meeting and conference in Kingston."
    ) == "BUSINESS_TRAVEL"


def test_rest_of_the_trip_does_not_imply_a_relaxation_goal() -> None:
    classifier = GoalClassifier()

    assert classifier.classify_from_text(
        "Book a budget-friendly hotel for the rest of the trip."
    ) == "GENERAL_TRAVEL"


def test_explicit_rest_and_relaxation_still_selects_relaxation() -> None:
    classifier = GoalClassifier()

    assert classifier.classify_from_text(
        "I want a spa holiday for rest and relaxation."
    ) == "RELAXATION"


def test_couple_with_restaurant_request_is_not_forced_into_romance_or_food() -> None:
    classifier = GoalClassifier()

    assert classifier.classify_from_text(
        "A couple want Japanese culture and one Michelin-starred restaurant."
    ) == "GENERAL_TRAVEL"


def test_children_take_priority_over_a_parent_football_interest() -> None:
    classifier = GoalClassifier()

    assert classifier.classify_from_text(
        "Plan a family holiday with two children and a Camp Nou stadium visit."
    ) == "FAMILY_TRIP"


def test_explicit_food_tour_still_selects_food_goal() -> None:
    classifier = GoalClassifier()

    assert classifier.classify_from_text(
        "Plan a street food tour and culinary holiday."
    ) == "FOOD_TOUR"
