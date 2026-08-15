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
