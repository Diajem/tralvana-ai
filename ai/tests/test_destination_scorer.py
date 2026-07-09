from ai.discovery.destinations.destination_scorer import DestinationScorer


def _destination(**overrides) -> dict:
    base = {
        "city": "Testville", "country": "Testland", "region": "Testregion",
        "neighbourhood": "Test Area", "destination_type": "NEIGHBOURHOOD",
        "name": "Test Place", "description": "A test place.",
        "best_for": ["testing"],
        "distance_from_centre": 2.0,
        "transport_access_score": 0.7,
        "food_score": 0.6,
        "culture_score": 0.5,
        "football_score": 0.2,
        "nightlife_score": 0.3,
        "family_score": 0.5,
        "safety_score": 0.8,
        "budget_score": 0.6,
        "season_score": 0.6,
        "_tags": ["food"],
        "_popularity": 5,
    }
    base.update(overrides)
    return base


class TestDestinationScorer:
    def test_match_score_in_range(self):
        scorer = DestinationScorer()
        result = scorer.score(_destination(), preferences={})
        assert 0.0 <= result["match_score"] <= 1.0

    def test_deterministic_same_inputs_same_score(self):
        scorer = DestinationScorer()
        d = _destination()
        prefs = {"interests": ["food"]}
        r1 = scorer.score(d, prefs)
        r2 = scorer.score(d, prefs)
        assert r1["match_score"] == r2["match_score"]

    def test_matching_interest_scores_higher_interest_fit(self):
        scorer = DestinationScorer()
        food_focused = scorer.score(_destination(food_score=0.9), {"interests": ["food"]})
        no_interests = scorer.score(_destination(food_score=0.9), {"interests": []})
        assert food_focused["breakdown"]["interest_fit"] >= no_interests["breakdown"]["interest_fit"]

    def test_unmapped_interest_uses_neutral_score(self):
        scorer = DestinationScorer()
        result = scorer.score(_destination(), {"interests": ["romance"]})
        assert result["breakdown"]["interest_fit"] == 0.6

    def test_backpacker_budget_style_uses_budget_score_directly(self):
        scorer = DestinationScorer()
        result = scorer.score(_destination(budget_score=0.9), {"budget_style": "backpacker"})
        assert result["breakdown"]["budget_fit"] == 0.9

    def test_luxury_budget_style_softens_budget_penalty(self):
        scorer = DestinationScorer()
        result = scorer.score(_destination(budget_score=0.1), {"budget_style": "luxury"})
        assert result["breakdown"]["budget_fit"] == 0.7

    def test_children_present_uses_family_score_directly(self):
        scorer = DestinationScorer()
        result = scorer.score(_destination(family_score=0.9), {"has_children": True})
        assert result["breakdown"]["family_fit"] == 0.9

    def test_no_children_uses_neutral_family_fit(self):
        scorer = DestinationScorer()
        result = scorer.score(_destination(family_score=0.9), {"has_children": False})
        assert result["breakdown"]["family_fit"] == 0.6

    def test_photography_tag_gives_maximum_photography_fit(self):
        scorer = DestinationScorer()
        result = scorer.score(_destination(_tags=["photography"]), {})
        assert result["breakdown"]["photography_fit"] == 1.0

    def test_dna_sport_focus_boosts_high_football_score(self):
        scorer = DestinationScorer()
        dna = {"traits": {"sport_focus": 0.8}}
        d = _destination(football_score=0.8)
        with_dna = scorer.score(d, {}, dna=dna)
        without_dna = scorer.score(d, {}, dna=None)
        assert with_dna["match_score"] >= without_dna["match_score"]
        assert len(with_dna["dna_notes"]) > 0

    def test_goal_type_football_travel_boosts_football_relevant_destination(self):
        scorer = DestinationScorer()
        d = _destination(football_score=0.8)
        with_goal = scorer.score(d, {}, goal_type="FOOTBALL_TRAVEL")
        without_goal = scorer.score(d, {}, goal_type=None)
        assert with_goal["match_score"] >= without_goal["match_score"]

    def test_persona_scores_present_for_all_seven_personas(self):
        scorer = DestinationScorer()
        result = scorer.score(_destination(), preferences={})
        assert set(result["persona_scores"].keys()) == {
            "food", "football", "culture", "family", "budget", "photography", "hidden_gem",
        }

    def test_hidden_gem_score_inverse_of_popularity(self):
        scorer = DestinationScorer()
        obscure = scorer.score(_destination(_popularity=1), {})
        famous = scorer.score(_destination(_popularity=10), {})
        assert obscure["persona_scores"]["hidden_gem"] > famous["persona_scores"]["hidden_gem"]
