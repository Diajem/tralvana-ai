from datetime import date, timedelta

from ai.discovery.visa.visa_normalizer import VisaNormalizer


def _raw(**overrides) -> dict:
    base = {
        "passport_country": "United Kingdom", "destination_country": "Japan",
        "matched_type": "tier", "status": "VISA_NOT_REQUIRED", "visa_type": "None",
        "max_stay_days": 90, "processing_time": "Not applicable",
        "vaccination_requirements": [],
    }
    base.update(overrides)
    return base


class TestVisaNormalizer:
    def test_visa_not_required_status_sets_visa_required_false(self):
        normalizer = VisaNormalizer()
        result = normalizer.normalize(
            _raw(), nationality="British", transit_countries=[], transit_status=[],
            travel_purpose="TOURISM", intended_length_of_stay=14, passport_expiry_date=None,
        )
        assert result["visa_required"] is False
        assert result["travel_authorisation_required"] is False

    def test_visa_required_status_sets_visa_required_true(self):
        normalizer = VisaNormalizer()
        result = normalizer.normalize(
            _raw(status="VISA_REQUIRED"), nationality="British", transit_countries=[],
            transit_status=[], travel_purpose="TOURISM", intended_length_of_stay=14,
            passport_expiry_date=None,
        )
        assert result["visa_required"] is True
        assert result["travel_authorisation_required"] is False

    def test_eta_required_sets_travel_authorisation_required_true(self):
        normalizer = VisaNormalizer()
        result = normalizer.normalize(
            _raw(status="ETA_REQUIRED"), nationality="British", transit_countries=[],
            transit_status=[], travel_purpose="TOURISM", intended_length_of_stay=14,
            passport_expiry_date=None,
        )
        assert result["visa_required"] is False
        assert result["travel_authorisation_required"] is True

    def test_no_passport_expiry_date_gives_none_validity_months(self):
        normalizer = VisaNormalizer()
        result = normalizer.normalize(
            _raw(), nationality="British", transit_countries=[], transit_status=[],
            travel_purpose="TOURISM", intended_length_of_stay=14, passport_expiry_date=None,
        )
        assert result["passport_validity_months"] is None

    def test_passport_expiry_date_computes_validity_months(self):
        normalizer = VisaNormalizer()
        future_date = (date.today() + timedelta(days=365)).isoformat()
        result = normalizer.normalize(
            _raw(), nationality="British", transit_countries=[], transit_status=[],
            travel_purpose="TOURISM", intended_length_of_stay=14, passport_expiry_date=future_date,
        )
        assert 11.5 <= result["passport_validity_months"] <= 12.5

    def test_invalid_expiry_date_format_gives_none(self):
        normalizer = VisaNormalizer()
        result = normalizer.normalize(
            _raw(), nationality="British", transit_countries=[], transit_status=[],
            travel_purpose="TOURISM", intended_length_of_stay=14, passport_expiry_date="not-a-date",
        )
        assert result["passport_validity_months"] is None

    def test_visa_required_entry_requirements_include_visa(self):
        normalizer = VisaNormalizer()
        result = normalizer.normalize(
            _raw(status="VISA_REQUIRED"), nationality="British", transit_countries=[],
            transit_status=[], travel_purpose="TOURISM", intended_length_of_stay=14,
            passport_expiry_date=None,
        )
        assert any("visa" in r.lower() for r in result["entry_requirements"])

    def test_check_manually_entry_requirements_flag_uncertainty(self):
        normalizer = VisaNormalizer()
        result = normalizer.normalize(
            _raw(status="CHECK_MANUALLY"), nationality="British", transit_countries=[],
            transit_status=[], travel_purpose="TOURISM", intended_length_of_stay=14,
            passport_expiry_date=None,
        )
        assert any("not determined" in r.lower() for r in result["entry_requirements"])

    def test_travel_purpose_uppercased(self):
        normalizer = VisaNormalizer()
        result = normalizer.normalize(
            _raw(), nationality="British", transit_countries=[], transit_status=[],
            travel_purpose="tourism", intended_length_of_stay=14, passport_expiry_date=None,
        )
        assert result["travel_purpose"] == "TOURISM"

    def test_transit_countries_and_status_pass_through(self):
        normalizer = VisaNormalizer()
        transit_status = [{"country": "USA", "status": "VISA_REQUIRED", "requires_action": True}]
        result = normalizer.normalize(
            _raw(), nationality="British", transit_countries=["USA"], transit_status=transit_status,
            travel_purpose="TOURISM", intended_length_of_stay=14, passport_expiry_date=None,
        )
        assert result["transit_countries"] == ["USA"]
        assert result["transit_status"] == transit_status
