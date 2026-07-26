"""Currency, language, country, region, and city seed data."""

from ai.intelligence.knowledge.entities import City, Country, Currency, Language, Region
from ai.intelligence.ontology.seed_helpers import add_node as _n


def _currencies(g) -> None:
    for c in [
        Currency("cur_ngn", "NGN", "Nigerian Naira", "₦", ["NG"]),
        Currency("cur_gbp", "GBP", "British Pound", "£", ["GB"]),
        Currency("cur_eur", "EUR", "Euro", "€", ["FR", "IT", "ES", "NL", "DE"]),
        Currency("cur_aed", "AED", "UAE Dirham", "د.إ", ["AE"]),
        Currency("cur_usd", "USD", "US Dollar", "$", ["US"]),
        Currency("cur_jpy", "JPY", "Japanese Yen", "¥", ["JP"]),
        Currency("cur_ghs", "GHS", "Ghanaian Cedi", "₵", ["GH"]),
        Currency("cur_zar", "ZAR", "South African Rand", "R", ["ZA"]),
    ]:
        _n(g, c, "Currency")


def _languages(g) -> None:
    for lang in [
        Language("lang_en", "English", "en", "English", 1500),
        Language("lang_fr", "French", "fr", "Français", 321),
        Language("lang_ar", "Arabic", "ar", "العربية", 310),
        Language("lang_it", "Italian", "it", "Italiano", 67),
        Language("lang_es", "Spanish", "es", "Español", 559),
        Language("lang_ja", "Japanese", "ja", "日本語", 125),
        Language("lang_yo", "Yoruba", "yo", "Yorùbá", 46),
        Language("lang_ha", "Hausa", "ha", "Hausa", 77),
    ]:
        _n(g, lang, "Language")


def _countries(g) -> None:
    for c in [
        Country(
            "country_ng",
            "Nigeria",
            "NG",
            "Africa",
            "city_lagos",
            ["yo", "ha", "en"],
            "NGN",
            "medium",
        ),
        Country(
            "country_gb",
            "United Kingdom",
            "GB",
            "Europe",
            "city_london",
            ["en"],
            "GBP",
            "low",
        ),
        Country(
            "country_fr", "France", "FR", "Europe", "city_paris", ["fr"], "EUR", "low"
        ),
        Country(
            "country_ae", "UAE", "AE", "Asia", "city_dubai", ["ar", "en"], "AED", "low"
        ),
        Country(
            "country_us",
            "United States",
            "US",
            "Americas",
            "city_new_york",
            ["en"],
            "USD",
            "low",
        ),
        Country(
            "country_it", "Italy", "IT", "Europe", "city_rome", ["it"], "EUR", "low"
        ),
        Country(
            "country_es",
            "Spain",
            "ES",
            "Europe",
            "city_barcelona",
            ["es"],
            "EUR",
            "low",
        ),
        Country(
            "country_jp", "Japan", "JP", "Asia", "city_tokyo", ["ja"], "JPY", "low"
        ),
        Country(
            "country_gh", "Ghana", "GH", "Africa", "city_accra", ["en"], "GHS", "low"
        ),
        Country(
            "country_za",
            "South Africa",
            "ZA",
            "Africa",
            "city_cape_town",
            ["en", "af", "zu"],
            "ZAR",
            "medium",
        ),
    ]:
        _n(g, c, "Country")


def _regions(g) -> None:
    for r in [
        Region(
            "region_lagos_st",
            "Lagos State",
            "country_ng",
            "state",
            ["coastal", "urban"],
        ),
        Region(
            "region_london",
            "Greater London",
            "country_gb",
            "county",
            ["urban", "diverse"],
        ),
        Region(
            "region_idf",
            "Île-de-France",
            "country_fr",
            "province",
            ["urban", "cultural"],
        ),
        Region(
            "region_lazio", "Lazio", "country_it", "province", ["historic", "cultural"]
        ),
        Region(
            "region_catalonia",
            "Catalonia",
            "country_es",
            "province",
            ["beach", "culture", "sport"],
        ),
        Region(
            "region_kanto",
            "Kantō Region",
            "country_jp",
            "district",
            ["urban", "tech", "food"],
        ),
    ]:
        _n(g, r, "Region")


def _cities(g) -> None:
    for c in [
        City(
            "city_lagos",
            "Lagos",
            "country_ng",
            "region_lagos_st",
            "Africa/Lagos",
            15_000_000,
            ["coastal", "urban", "business", "nightlife"],
        ),
        City(
            "city_abuja",
            "Abuja",
            "country_ng",
            None,
            "Africa/Lagos",
            3_600_000,
            ["urban", "business", "modern"],
        ),
        City(
            "city_london",
            "London",
            "country_gb",
            "region_london",
            "Europe/London",
            9_000_000,
            ["urban", "historic", "cultural", "business"],
        ),
        City(
            "city_paris",
            "Paris",
            "country_fr",
            "region_idf",
            "Europe/Paris",
            2_100_000,
            ["romantic", "cultural", "fashion", "food"],
        ),
        City(
            "city_dubai",
            "Dubai",
            "country_ae",
            None,
            "Asia/Dubai",
            3_300_000,
            ["luxury", "urban", "beach", "modern"],
        ),
        City(
            "city_new_york",
            "New York",
            "country_us",
            None,
            "America/New_York",
            8_300_000,
            ["urban", "cultural", "business", "food"],
        ),
        City(
            "city_rome",
            "Rome",
            "country_it",
            "region_lazio",
            "Europe/Rome",
            2_800_000,
            ["historic", "cultural", "food", "art"],
        ),
        City(
            "city_barcelona",
            "Barcelona",
            "country_es",
            "region_catalonia",
            "Europe/Madrid",
            1_600_000,
            ["beach", "urban", "food", "nightlife", "sport"],
        ),
        City(
            "city_tokyo",
            "Tokyo",
            "country_jp",
            "region_kanto",
            "Asia/Tokyo",
            14_000_000,
            ["urban", "technology", "food", "cultural"],
        ),
        City(
            "city_accra",
            "Accra",
            "country_gh",
            None,
            "Africa/Accra",
            2_300_000,
            ["coastal", "urban", "business", "cultural"],
        ),
        City(
            "city_cape_town",
            "Cape Town",
            "country_za",
            None,
            "Africa/Johannesburg",
            4_600_000,
            ["coastal", "nature", "beach", "mountain"],
        ),
    ]:
        _n(g, c, "City")
