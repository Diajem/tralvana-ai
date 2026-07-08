import pytest

from ai.intelligence.traveller_dna.dna_classifier import TravellerDNAInferenceService


@pytest.fixture
def service() -> TravellerDNAInferenceService:
    return TravellerDNAInferenceService()


class TestDNAInference:
    def test_infer_returns_dna_object(self, service, football_profile):
        dna = service.infer(football_profile)
        assert dna is not None
        assert dna.primary_type
        assert dna.traveller_id == "test-traveller-001"

    def test_confidence_is_bounded(self, service, football_profile):
        dna = service.infer(football_profile)
        assert 0.0 <= dna.confidence <= 1.0

    def test_secondary_types_is_list(self, service, football_profile):
        dna = service.infer(football_profile)
        assert isinstance(dna.secondary_types, list)

    def test_traits_are_bounded(self, service, football_profile):
        dna = service.infer(football_profile)
        for trait_name, score in dna.traits.items():
            assert 0.0 <= score <= 1.0, f"Trait {trait_name} out of bounds: {score}"

    def test_inferred_at_is_set(self, service, football_profile):
        dna = service.infer(football_profile)
        assert dna.inferred_at

    def test_luxury_profile_gets_luxury_orientation(self, service, luxury_profile):
        dna = service.infer(luxury_profile)
        assert dna.traits.get("luxury_orientation", 0) > 0

    def test_luxury_profile_primary_dna(self, service, luxury_profile):
        dna = service.infer(luxury_profile)
        assert dna.primary_type  # has some type
        assert dna.confidence > 0

    def test_football_profile_has_sport_trait(self, service, football_profile):
        dna = service.infer(football_profile)
        # sport interest contributes to adventure_seeking
        assert dna.traits.get("adventure_seeking", 0) > 0

    def test_empty_profile_still_returns_dna(self, service):
        dna = service.infer({})
        assert dna is not None
        assert dna.primary_type

    def test_describe_returns_string(self, service):
        desc = service.describe("Food Traveller")
        assert isinstance(desc, str)
        assert len(desc) > 0

    def test_describe_unknown_type_returns_fallback(self, service):
        desc = service.describe("Unknown DNA Type")
        assert "not found" in desc.lower() or len(desc) > 0
