"""Typed relationships connecting the deterministic ontology seed nodes."""

from ai.intelligence.ontology.seed_helpers import R, add_edge as _e


def _relationships(g) -> None:
    L = R.LOCATED_IN
    B = R.BELONGS_TO
    SV = R.SERVES
    PI = R.PLAYS_IN
    PA = R.PLAYS_AT
    OP = R.OPERATES_FROM
    UC = R.USES_CURRENCY
    SP = R.SPEAKS
    HR = R.HAS_REGION
    IR = R.IN_REGION
    HW = R.HAS_WEATHER
    HS = R.HAS_SEASON
    PT = R.PART_OF
    NR = R.NEAR
    CN = R.CONNECTS
    HO = R.HOSTS

    # City → Country
    for cty, ctry in [
        ("city_lagos", "country_ng"),
        ("city_abuja", "country_ng"),
        ("city_london", "country_gb"),
        ("city_paris", "country_fr"),
        ("city_dubai", "country_ae"),
        ("city_new_york", "country_us"),
        ("city_rome", "country_it"),
        ("city_barcelona", "country_es"),
        ("city_tokyo", "country_jp"),
        ("city_accra", "country_gh"),
        ("city_cape_town", "country_za"),
    ]:
        _e(g, cty, "City", L, ctry, "Country")

    # Airport → City
    for ap, cty in [
        ("airport_los", "city_lagos"),
        ("airport_abv", "city_abuja"),
        ("airport_lhr", "city_london"),
        ("airport_cdg", "city_paris"),
        ("airport_dxb", "city_dubai"),
        ("airport_jfk", "city_new_york"),
        ("airport_fco", "city_rome"),
        ("airport_bcn", "city_barcelona"),
        ("airport_nrt", "city_tokyo"),
        ("airport_acc", "city_accra"),
        ("airport_cpt", "city_cape_town"),
    ]:
        _e(g, ap, "Airport", SV, cty, "City")

    # RailStation → City
    for rs, cty in [
        ("rail_stpancras", "city_london"),
        ("rail_euston", "city_london"),
        ("rail_gdnord", "city_paris"),
        ("rail_termini", "city_rome"),
        ("rail_sants", "city_barcelona"),
        ("rail_shinjuku", "city_tokyo"),
    ]:
        _e(g, rs, "RailStation", CN, cty, "City")

    # Airline → Airport (hub)
    for al, ap in [
        ("airline_ba", "airport_lhr"),
        ("airline_af", "airport_cdg"),
        ("airline_ek", "airport_dxb"),
        ("airline_dl", "airport_jfk"),
        ("airline_az", "airport_fco"),
        ("airline_nh", "airport_nrt"),
        ("airline_w3", "airport_los"),
    ]:
        _e(g, al, "Airline", OP, ap, "Airport")

    # Hotel → City
    for h, cty in [
        ("hotel_eko", "city_lagos"),
        ("hotel_radisson_ng", "city_lagos"),
        ("hotel_ritz", "city_london"),
        ("hotel_premier_lon", "city_london"),
        ("hotel_le_meurice", "city_paris"),
        ("hotel_ibis_paris", "city_paris"),
        ("hotel_atlantis", "city_dubai"),
        ("hotel_premier_dxb", "city_dubai"),
        ("hotel_plaza", "city_new_york"),
        ("hotel_citizenm", "city_new_york"),
        ("hotel_cavalieri", "city_rome"),
        ("hotel_hotel_art", "city_rome"),
        ("hotel_arts", "city_barcelona"),
        ("hotel_catalonia", "city_barcelona"),
        ("hotel_palace_tok", "city_tokyo"),
        ("hotel_dormy", "city_tokyo"),
    ]:
        _e(g, h, "Hotel", L, cty, "City")

    # Restaurant → City + Restaurant → Cuisine
    rest_data = [
        ("rest_nok", "city_lagos", "cuisine_nigerian"),
        ("rest_sketch", "city_london", "cuisine_british"),
        ("rest_ledou", "city_paris", "cuisine_french"),
        ("rest_nobu_dxb", "city_dubai", "cuisine_japanese"),
        ("rest_eleven", "city_new_york", "cuisine_american"),
        ("rest_roscioli", "city_rome", "cuisine_italian"),
        ("rest_tickets", "city_barcelona", "cuisine_spanish"),
        ("rest_sushi_s", "city_tokyo", "cuisine_japanese"),
    ]
    for r_id, cty, cuis in rest_data:
        _e(g, r_id, "Restaurant", B, cty, "City")
        _e(g, r_id, "Restaurant", SV, cuis, "Cuisine")

    # FootballClub → City + FootballClub → SportsVenue
    for fc, cty, venue in [
        ("club_arsenal", "city_london", "venue_emirates"),
        ("club_chelsea", "city_london", "venue_stamford"),
        ("club_psg", "city_paris", "venue_parc_princes"),
        ("club_barca", "city_barcelona", "venue_camp_nou"),
        ("club_roma", "city_rome", "venue_olimpico"),
        ("club_juve", "city_rome", "venue_olimpico"),
        ("club_inter", "city_rome", "venue_san_siro"),
        ("club_fc_tokyo", "city_tokyo", "venue_ajinomoto"),
    ]:
        _e(g, fc, "FootballClub", PI, cty, "City")
        _e(g, fc, "FootballClub", PA, venue, "SportsVenue")

    # SportsVenue → City
    for v, cty in [
        ("venue_emirates", "city_london"),
        ("venue_stamford", "city_london"),
        ("venue_wembley", "city_london"),
        ("venue_parc_princes", "city_paris"),
        ("venue_camp_nou", "city_barcelona"),
        ("venue_olimpico", "city_rome"),
        ("venue_san_siro", "city_rome"),
        ("venue_ajinomoto", "city_tokyo"),
    ]:
        _e(g, cty, "City", HO, v, "SportsVenue")

    # Attraction → City
    for at, cty in [
        ("attr_vi", "city_lagos"),
        ("attr_olumo", "city_abuja"),
        ("attr_tower", "city_london"),
        ("attr_wembley", "city_london"),
        ("attr_eiffel", "city_paris"),
        ("attr_louvre_at", "city_paris"),
        ("attr_burj", "city_dubai"),
        ("attr_palm", "city_dubai"),
        ("attr_empire", "city_new_york"),
        ("attr_central", "city_new_york"),
        ("attr_colosseum", "city_rome"),
        ("attr_sagrada", "city_barcelona"),
        ("attr_senso", "city_tokyo"),
        ("attr_kakum", "city_accra"),
        ("attr_tafelberg", "city_cape_town"),
    ]:
        _e(g, at, "Attraction", NR, cty, "City")

    # Museum → City
    for m, cty in [
        ("museum_british", "city_london"),
        ("museum_tate", "city_london"),
        ("museum_louvre", "city_paris"),
        ("museum_orsay", "city_paris"),
        ("museum_vatican", "city_rome"),
        ("museum_prado", "city_barcelona"),
        ("museum_met", "city_new_york"),
        ("museum_ghana_nat", "city_accra"),
        ("museum_tokyo_nat", "city_tokyo"),
        ("museum_iziko", "city_cape_town"),
    ]:
        _e(g, m, "Museum", L, cty, "City")

    # Event → City
    for ev, cty in [
        ("evt_afrobeats", "city_lagos"),
        ("evt_notting", "city_london"),
        ("evt_fashion", "city_paris"),
        ("evt_expo_dxb", "city_dubai"),
        ("evt_marathon", "city_new_york"),
        ("evt_tomato", "city_barcelona"),
        ("evt_cherry", "city_tokyo"),
        ("evt_panafest", "city_accra"),
    ]:
        _e(g, ev, "Event", PT, cty, "City")

    # Transport → City
    for t, cty in [
        ("trans_tube", "city_london"),
        ("trans_rer", "city_paris"),
        ("trans_metro_dxb", "city_dubai"),
        ("trans_subway_ny", "city_new_york"),
        ("trans_metro_bcn", "city_barcelona"),
        ("trans_shinkansen", "city_tokyo"),
    ]:
        _e(g, t, "Transport", B, cty, "City")

    # Country → Currency
    for ctry, cur in [
        ("country_ng", "cur_ngn"),
        ("country_gb", "cur_gbp"),
        ("country_fr", "cur_eur"),
        ("country_ae", "cur_aed"),
        ("country_us", "cur_usd"),
        ("country_it", "cur_eur"),
        ("country_es", "cur_eur"),
        ("country_jp", "cur_jpy"),
        ("country_gh", "cur_ghs"),
        ("country_za", "cur_zar"),
    ]:
        _e(g, ctry, "Country", UC, cur, "Currency")

    # Country → Language
    for ctry, lang in [
        ("country_ng", "lang_yo"),
        ("country_ng", "lang_ha"),
        ("country_ng", "lang_en"),
        ("country_gb", "lang_en"),
        ("country_fr", "lang_fr"),
        ("country_ae", "lang_ar"),
        ("country_us", "lang_en"),
        ("country_it", "lang_it"),
        ("country_es", "lang_es"),
        ("country_jp", "lang_ja"),
        ("country_gh", "lang_en"),
        ("country_za", "lang_en"),
    ]:
        _e(g, ctry, "Country", SP, lang, "Language")

    # Country → Region + City → Region
    for ctry, reg in [
        ("country_ng", "region_lagos_st"),
        ("country_gb", "region_london"),
        ("country_fr", "region_idf"),
        ("country_it", "region_lazio"),
        ("country_es", "region_catalonia"),
        ("country_jp", "region_kanto"),
    ]:
        _e(g, ctry, "Country", HR, reg, "Region")

    for cty, reg in [
        ("city_lagos", "region_lagos_st"),
        ("city_london", "region_london"),
        ("city_paris", "region_idf"),
        ("city_rome", "region_lazio"),
        ("city_barcelona", "region_catalonia"),
        ("city_tokyo", "region_kanto"),
    ]:
        _e(g, cty, "City", IR, reg, "Region")

    # City → Weather
    for w, cty in [
        ("w_lag_1", "city_lagos"),
        ("w_lag_7", "city_lagos"),
        ("w_lag_12", "city_lagos"),
        ("w_lon_4", "city_london"),
        ("w_lon_7", "city_london"),
        ("w_lon_12", "city_london"),
        ("w_par_4", "city_paris"),
        ("w_par_7", "city_paris"),
        ("w_par_12", "city_paris"),
        ("w_dxb_1", "city_dubai"),
        ("w_dxb_7", "city_dubai"),
        ("w_dxb_11", "city_dubai"),
        ("w_ny_4", "city_new_york"),
        ("w_ny_7", "city_new_york"),
        ("w_ny_12", "city_new_york"),
        ("w_rom_4", "city_rome"),
        ("w_rom_7", "city_rome"),
        ("w_rom_10", "city_rome"),
        ("w_bcn_4", "city_barcelona"),
        ("w_bcn_7", "city_barcelona"),
        ("w_bcn_10", "city_barcelona"),
        ("w_tok_4", "city_tokyo"),
        ("w_tok_7", "city_tokyo"),
        ("w_tok_12", "city_tokyo"),
        ("w_cpt_1", "city_cape_town"),
        ("w_cpt_7", "city_cape_town"),
    ]:
        _e(g, cty, "City", HW, w, "Weather")

    # City → TravelSeason
    for season_id, city_ids in [
        (
            "season_eur_summer",
            ["city_london", "city_paris", "city_rome", "city_barcelona"],
        ),
        (
            "season_eur_spring",
            ["city_london", "city_paris", "city_rome", "city_barcelona"],
        ),
        ("season_eur_winter", ["city_london", "city_paris", "city_rome"]),
        ("season_dxb_cool", ["city_dubai"]),
        ("season_dxb_hot", ["city_dubai"]),
        ("season_ng_harmattan", ["city_lagos", "city_accra"]),
    ]:
        for cty in city_ids:
            _e(g, cty, "City", HS, season_id, "TravelSeason")
