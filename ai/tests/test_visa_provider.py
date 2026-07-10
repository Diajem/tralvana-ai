from ai.discovery.visa.mock_visa_provider import MockVisaProvider


class TestMockVisaProvider:
    def test_known_pair_returns_tier_match(self):
        provider = MockVisaProvider()
        result = provider.lookup("UK", "Japan")
        assert result["matched_type"] == "tier"
        assert result["status"] == "VISA_NOT_REQUIRED"

    def test_unknown_nationality_returns_check_manually(self):
        provider = MockVisaProvider()
        result = provider.lookup("Wakanda", "Japan")
        assert result["matched_type"] == "unknown"
        assert result["status"] == "CHECK_MANUALLY"

    def test_unknown_destination_returns_check_manually(self):
        provider = MockVisaProvider()
        result = provider.lookup("UK", "Atlantis")
        assert result["matched_type"] == "unknown"
        assert result["status"] == "CHECK_MANUALLY"

    def test_same_country_never_requires_a_visa(self):
        provider = MockVisaProvider()
        result = provider.lookup("Nigeria", "Nigeria")
        assert result["matched_type"] == "same_country"
        assert result["status"] == "VISA_NOT_REQUIRED"

    def test_common_travel_area_override_ireland_uk(self):
        provider = MockVisaProvider()
        result = provider.lookup("Ireland", "UK")
        assert result["matched_type"] == "override"
        assert result["status"] == "VISA_NOT_REQUIRED"

    def test_ecowas_override_ghana_nigeria(self):
        provider = MockVisaProvider()
        result = provider.lookup("Ghana", "Nigeria")
        assert result["matched_type"] == "override"
        assert result["status"] == "VISA_NOT_REQUIRED"

    def test_developing_tier_passport_needs_more_for_same_destination(self):
        provider = MockVisaProvider()
        strong = provider.lookup("UK", "USA")
        developing = provider.lookup("Nigeria", "USA")
        assert strong["status"] == "ETA_REQUIRED"
        assert developing["status"] == "VISA_REQUIRED"

    def test_iso2_code_resolves_same_as_country_name(self):
        provider = MockVisaProvider()
        by_code = provider.lookup("NG", "GB")
        by_name = provider.lookup("Nigeria", "United Kingdom")
        assert by_code["status"] == by_name["status"]

    def test_nationality_adjective_resolves_same_as_country_name(self):
        provider = MockVisaProvider()
        by_adjective = provider.lookup("Nigerian", "Spain")
        by_name = provider.lookup("Nigeria", "Spain")
        assert by_adjective["status"] == by_name["status"]

    def test_study_purpose_escalates_visa_free_to_required(self):
        provider = MockVisaProvider()
        tourism = provider.lookup("UK", "Japan", travel_purpose="TOURISM")
        study = provider.lookup("UK", "Japan", travel_purpose="STUDY")
        assert tourism["status"] == "VISA_NOT_REQUIRED"
        assert study["status"] == "VISA_REQUIRED"

    def test_work_purpose_escalates_eta_to_required(self):
        provider = MockVisaProvider()
        result = provider.lookup("UK", "USA", travel_purpose="WORK")
        assert result["status"] == "VISA_REQUIRED"

    def test_case_insensitive_lookup(self):
        provider = MockVisaProvider()
        lower = provider.lookup("uk", "japan")
        upper = provider.lookup("UK", "JAPAN")
        assert lower["status"] == upper["status"]

    def test_deterministic_same_inputs_same_result(self):
        provider = MockVisaProvider()
        first = provider.lookup("Nigeria", "UAE")
        second = provider.lookup("Nigeria", "UAE")
        assert first == second

    def test_nigeria_vaccination_requirement_present(self):
        provider = MockVisaProvider()
        result = provider.lookup("UK", "Nigeria")
        assert "Yellow Fever vaccination certificate" in result["vaccination_requirements"]

    def test_known_nationalities_and_destinations_cover_spec_list(self):
        provider = MockVisaProvider()
        nationalities = set(provider.known_nationalities())
        destinations = set(provider.known_destinations())
        assert {"UK", "IRELAND", "USA", "CANADA", "NIGERIA", "GHANA",
                "SOUTH AFRICA", "JAMAICA", "EU", "JAPAN"} == nationalities
        assert {"JAPAN", "USA", "UK", "IRELAND", "FRANCE", "SPAIN", "NIGERIA", "UAE"} == destinations
