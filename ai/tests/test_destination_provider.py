from ai.discovery.destinations.mock_destination_provider import MockDestinationProvider

_EXPECTED_CITIES = {
    "Tokyo", "Osaka", "Barcelona", "Paris", "London",
    "New York", "Lagos", "Accra", "Kingston", "Dubai",
}


class TestMockDestinationProvider:
    def test_includes_all_required_cities(self):
        provider = MockDestinationProvider()
        assert _EXPECTED_CITIES.issubset(set(provider.cities()))

    def test_catalogue_mode_returns_one_city_option_per_city(self):
        provider = MockDestinationProvider()
        result = provider.search(None)
        assert len(result) == len(provider.cities())
        assert all(r["place_type"] == "city" for r in result)

    def test_city_mode_excludes_the_city_level_entry(self):
        provider = MockDestinationProvider()
        result = provider.search("Tokyo")
        assert all(r["place_type"] != "city" for r in result)
        assert all(r["city"] == "Tokyo" for r in result)

    def test_city_mode_case_insensitive(self):
        provider = MockDestinationProvider()
        lower = provider.search("tokyo")
        upper = provider.search("TOKYO")
        assert len(lower) == len(upper) > 0

    def test_unknown_city_returns_empty(self):
        provider = MockDestinationProvider()
        assert provider.search("Atlantis") == []

    def test_deterministic_same_city_same_results(self):
        provider = MockDestinationProvider()
        first = provider.search("Barcelona")
        second = provider.search("Barcelona")
        assert [e["name"] for e in first] == [e["name"] for e in second]

    def test_every_city_has_at_least_three_sub_options(self):
        provider = MockDestinationProvider()
        for city in provider.cities():
            assert len(provider.search(city)) >= 3

    def test_entries_carry_city_base_attributes(self):
        provider = MockDestinationProvider()
        result = provider.search("Lagos")
        for entry in result:
            assert "safety_rating" in entry
            assert "budget_tier" in entry
            assert "country" in entry
            assert entry["country"] == "Nigeria"
