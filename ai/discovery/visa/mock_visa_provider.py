from __future__ import annotations

from typing import Any

# Passport "strength tier" — a deliberately broad-brush, illustrative
# simplification (mock data, not real government policy; see
# docs/VISA_INTELLIGENCE_ENGINE.md). "strong" passports get the more
# generous default policy at each destination; "developing" passports get
# the more restrictive one. Real visa policy has far more nuance than a
# two-tier split — this is a deterministic demo dataset, not legal advice.
_PASSPORT_TIER: dict[str, str] = {
    "UK": "strong", "IRELAND": "strong", "USA": "strong", "CANADA": "strong",
    "JAPAN": "strong", "EU": "strong",
    "NIGERIA": "developing", "GHANA": "developing",
    "SOUTH AFRICA": "developing", "JAMAICA": "developing",
}

# Common aliases, ISO 3166-1 alpha-2 codes, and natural-language nationality
# adjectives -> canonical keys used above and in _DESTINATION_POLICY below.
# Traveller profiles typically store nationality as an ISO-2 code (see
# ai/memory/traveller_profile_schema.md); free-text conversation input
# typically uses the adjective form ("Nigerian", "Irish") rather than the
# country name — both need to resolve to the same canonical key.
_ALIASES: dict[str, str] = {
    "GB": "UK", "UNITED KINGDOM": "UK", "GREAT BRITAIN": "UK", "BRITISH": "UK",
    "IE": "IRELAND", "IRISH": "IRELAND",
    "US": "USA", "UNITED STATES": "USA", "UNITED STATES OF AMERICA": "USA", "AMERICAN": "USA",
    "CA": "CANADA", "CANADIAN": "CANADA",
    "NG": "NIGERIA", "NIGERIAN": "NIGERIA",
    "GH": "GHANA", "GHANAIAN": "GHANA",
    "ZA": "SOUTH AFRICA", "RSA": "SOUTH AFRICA", "SOUTH AFRICAN": "SOUTH AFRICA",
    "JM": "JAMAICA", "JAMAICAN": "JAMAICA",
    "JP": "JAPAN", "JAPANESE": "JAPAN",
    "FR": "FRANCE", "FRENCH": "FRANCE",
    "ES": "SPAIN", "SPANISH": "SPAIN",
    "AE": "UAE", "UNITED ARAB EMIRATES": "UAE", "EMIRATI": "UAE",
}

_DESTINATIONS = {"JAPAN", "USA", "UK", "IRELAND", "FRANCE", "SPAIN", "NIGERIA", "UAE"}

# Canonical key -> display name, for countries where straight .title() would
# be wrong (acronyms) or where the mock dataset uses a generic label.
_DISPLAY_NAME: dict[str, str] = {
    "UK": "United Kingdom", "USA": "United States", "UAE": "United Arab Emirates",
    "EU": "EU (generic)",
}

# Purposes a short-stay visa-free/ETA/e-Visa waiver typically covers.
# Study/work are not covered by any tourism-oriented waiver in this mock
# dataset — they always require a proper visa, regardless of passport tier.
_WAIVER_ELIGIBLE_PURPOSES = {"TOURISM", "BUSINESS", "TRANSIT", "FAMILY_VISIT"}

# destination -> tier -> base policy. Formula-derived from tier + destination
# rather than hand-authored per nationality pair (80 combinations), the same
# "formula, not 540 hand-tuned numbers" approach Destination Intelligence
# used for its objective scores (ADR-013). Kept simple: two tiers per
# destination, not per-nationality figures.
_DESTINATION_POLICY: dict[str, dict[str, dict[str, Any]]] = {
    "JAPAN": {
        "strong": {
            "status": "VISA_NOT_REQUIRED", "visa_type": "None", "max_stay_days": 90,
            "processing_time": "Not applicable",
        },
        "developing": {
            "status": "VISA_REQUIRED", "visa_type": "Temporary Visitor Visa", "max_stay_days": 90,
            "processing_time": "5-10 business days",
        },
    },
    "USA": {
        "strong": {
            "status": "ETA_REQUIRED", "visa_type": "ESTA", "max_stay_days": 90,
            "processing_time": "Immediate to 72 hours",
        },
        "developing": {
            "status": "VISA_REQUIRED", "visa_type": "B1/B2 Visa", "max_stay_days": 180,
            "processing_time": "Several weeks, in-person interview required",
        },
    },
    "UK": {
        "strong": {
            "status": "ETA_REQUIRED", "visa_type": "UK Electronic Travel Authorisation", "max_stay_days": 180,
            "processing_time": "Up to 3 business days",
        },
        "developing": {
            "status": "VISA_REQUIRED", "visa_type": "Standard Visitor Visa", "max_stay_days": 180,
            "processing_time": "Around 3 weeks",
        },
    },
    "IRELAND": {
        "strong": {
            "status": "VISA_NOT_REQUIRED", "visa_type": "None", "max_stay_days": 90,
            "processing_time": "Not applicable",
        },
        "developing": {
            "status": "VISA_REQUIRED", "visa_type": "Irish Visit Visa", "max_stay_days": 90,
            "processing_time": "Around 4 weeks",
        },
    },
    "FRANCE": {
        "strong": {
            "status": "VISA_NOT_REQUIRED", "visa_type": "None", "max_stay_days": 90,
            "processing_time": "Not applicable",
        },
        "developing": {
            "status": "VISA_REQUIRED", "visa_type": "Schengen Short-Stay Visa", "max_stay_days": 90,
            "processing_time": "Around 15 business days",
        },
    },
    "SPAIN": {
        "strong": {
            "status": "VISA_NOT_REQUIRED", "visa_type": "None", "max_stay_days": 90,
            "processing_time": "Not applicable",
        },
        "developing": {
            "status": "VISA_REQUIRED", "visa_type": "Schengen Short-Stay Visa", "max_stay_days": 90,
            "processing_time": "Around 15 business days",
        },
    },
    "NIGERIA": {
        "strong": {
            "status": "EVISA_AVAILABLE", "visa_type": "Nigeria e-Visa", "max_stay_days": 90,
            "processing_time": "3-5 business days",
        },
        "developing": {
            "status": "VISA_REQUIRED", "visa_type": "Tourist Visa", "max_stay_days": 90,
            "processing_time": "Around 2 weeks",
        },
    },
    "UAE": {
        "strong": {
            "status": "VISA_NOT_REQUIRED", "visa_type": "Visa on Arrival", "max_stay_days": 30,
            "processing_time": "On arrival",
        },
        "developing": {
            "status": "EVISA_AVAILABLE", "visa_type": "UAE e-Visa", "max_stay_days": 30,
            "processing_time": "3-5 business days",
        },
    },
}

# Specific (passport, destination) overrides checked before the tier lookup
# — regional agreements that a two-tier default can't express. Common
# Travel Area (UK<->Ireland) and ECOWAS free movement (Ghana->Nigeria) are
# real, well-known examples chosen for illustrative variety.
_OVERRIDES: dict[tuple[str, str], dict[str, Any]] = {
    ("IRELAND", "UK"): {
        "status": "VISA_NOT_REQUIRED", "visa_type": "None (Common Travel Area)",
        "max_stay_days": None, "processing_time": "Not applicable",
    },
    ("UK", "IRELAND"): {
        "status": "VISA_NOT_REQUIRED", "visa_type": "None (Common Travel Area)",
        "max_stay_days": None, "processing_time": "Not applicable",
    },
    ("GHANA", "NIGERIA"): {
        "status": "VISA_NOT_REQUIRED", "visa_type": "None (ECOWAS free movement)",
        "max_stay_days": None, "processing_time": "Not applicable",
    },
}

# Illustrative vaccination requirement — Nigeria's Yellow Fever certificate
# requirement is real and well-known; kept as the sole populated example
# rather than hand-authoring health rules for every destination.
_VACCINATION_REQUIREMENTS: dict[str, list[str]] = {
    "NIGERIA": ["Yellow Fever vaccination certificate"],
}


class MockVisaProvider:
    """
    Deterministic mock visa-rule lookup — no external calls, no Timatic, no
    government API. Same interface a real provider would implement:
    lookup(passport_country, destination_country, travel_purpose) -> dict.
    Swapping in a real immigration data feed later means implementing this
    method against that API and passing the instance to
    VisaIntelligence(provider=...) — nothing downstream changes.

    This is explainable travel-planning intelligence, not legal advice —
    see docs/VISA_INTELLIGENCE_ENGINE.md.
    """

    def lookup(
        self,
        passport_country: str,
        destination_country: str,
        travel_purpose: str = "TOURISM",
    ) -> dict[str, Any]:
        passport = self._normalize(passport_country)
        destination = self._normalize(destination_country)

        if passport and destination and passport == destination:
            return self._result(
                passport, destination, "same_country",
                status="VISA_NOT_REQUIRED", visa_type="None (returning to own country)",
                max_stay_days=None, processing_time="Not applicable",
            )

        if passport and destination and (passport, destination) in _OVERRIDES:
            rule = _OVERRIDES[(passport, destination)]
            return self._result(passport, destination, "override", **rule)

        tier = _PASSPORT_TIER.get(passport) if passport else None
        policy = _DESTINATION_POLICY.get(destination) if destination else None

        if not tier or not policy:
            return self._result(
                passport or passport_country, destination or destination_country, "unknown",
                status="CHECK_MANUALLY", visa_type="Unknown",
                max_stay_days=None, processing_time="Unknown",
            )

        rule = dict(policy[tier])

        # A tourism/business/transit waiver does not cover study or work —
        # those always require a proper visa in this mock dataset.
        if travel_purpose.upper() in ("STUDY", "WORK") and rule["status"] != "VISA_REQUIRED":
            rule = {
                **rule,
                "status": "VISA_REQUIRED",
                "visa_type": f"{travel_purpose.title()} Visa",
                "processing_time": "Several weeks — consulate assessment required",
            }

        return self._result(passport, destination, "tier", **rule)

    def known_nationalities(self) -> list[str]:
        return sorted(_PASSPORT_TIER.keys())

    def known_destinations(self) -> list[str]:
        return sorted(_DESTINATIONS)

    # ------------------------------------------------------------------

    def _normalize(self, country: str | None) -> str | None:
        if not country:
            return None
        key = country.strip().upper()
        return _ALIASES.get(key, key)

    def _display(self, key: str) -> str:
        return _DISPLAY_NAME.get(key, key.title())

    def _result(
        self,
        passport_country: str,
        destination_country: str,
        matched_type: str,
        *,
        status: str,
        visa_type: str,
        max_stay_days: int | None,
        processing_time: str,
    ) -> dict[str, Any]:
        return {
            "passport_country": self._display(passport_country),
            "destination_country": self._display(destination_country),
            "matched_type": matched_type,
            "status": status,
            "visa_type": visa_type,
            "max_stay_days": max_stay_days,
            "processing_time": processing_time,
            "vaccination_requirements": list(_VACCINATION_REQUIREMENTS.get(destination_country, [])),
        }


mock_visa_provider = MockVisaProvider()
