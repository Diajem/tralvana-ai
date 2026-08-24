"""Acceptance coverage for the five remote and mixed-status trip briefs."""


MANCHESTER = """Plan a 14 day trip to Manchester, UK for a family of 2, both Nigerian nationals (1 adult and 1 child, age 10). We'd like to fly from Lagos, Nigeria, from any convenient airport with a reliable connection to Manchester. We'd like family-friendly sightseeing, including football stadium tours (Old Trafford and/or Etihad Stadium), museums, and day trips outside the city. We would like to dine out together 4 times and stay in a family-friendly hotel close to the city centre. We would like package allowance and UK visa requirements. Maybe visit the Trafford Centre and take a day trip to the Lake District or Peak District. Traveling out on the 15th of September and spending 14 full days in the UK."""

CASTELMEZZANO = """Plan an 8 day trip to Castelmezzano, Italy for a couple, 2 adults, both American nationals. We would like to fly from Charlotte Douglas International Airport in North Carolina since we live in North Carolina, connecting through a major European hub. Focus on Basilicata, local ceramics, traditional crafts and small artisan workshops. We would like to dine out together 3 times, including one authentic family-run trattoria, and stay within walking distance of the town centre. We would like package allowance and Italian Schengen visa requirements. Maybe hike the Dolomiti Lucane trails and take a day trip to Pietrapertosa. Traveling out on the 22nd of May and spending 8 full days in Italy."""

BLOWING_ROCK = """Plan a 10 day trip to Blowing Rock, North Carolina for a family of 4, 2 adults and 2 children (ages 9 and 13), all Italian nationals. Fly from Naples International Airport since we live near Naples, connecting through a major US hub. The children want the Blue Ridge Parkway and hiking. Dine out 4 times, including a Southern barbecue restaurant, and stay in a family-friendly cabin just outside town. We want package allowance and US visa requirements including ESTA. Maybe a horseback riding day and an Appalachian heritage site. Traveling out on the 6th of July and spending 10 full days in North Carolina."""

RONDA = """Plan a 6 day trip to Ronda, Spain for 3 friends — 1 Italian national, 1 American national, and 1 Nigerian national currently residing in Milan on a long-term visa. Fly from Milan Malpensa Airport. Focus on the smaller Andalusian town. Dine out 3 times, including a traditional tapas bar, and stay near the old town. We want package allowance and each traveler's individual Schengen visa requirements. Visit Puente Nuevo bridge and El Tajo gorge, plus a day trip to a nearby white village. Traveling out on the 3rd of June and spending 6 full days in Spain."""

BEAUFORT = """Plan a 7 day trip to Beaufort, North Carolina for a couple, 2 adults, both Italian nationals. Fly from Rome Fiumicino Airport since we live in Rome, connecting through a major US hub and arriving near the North Carolina coast. We want a quiet coastal trip with a sailing or boat tour along the Crystal Coast. Dine out 3 times, including a fresh seafood restaurant by the waterfront, and stay in a boutique inn in the historic town. We want package allowance and US visa requirements including ESTA. Maybe a day trip to Cape Lookout National Seashore and a maritime history museum. Traveling out on the 12th of June and spending 7 full days in North Carolina."""


def _plan(client, message: str) -> dict:
    response = client.post("/planner/plan", json={"message": message})
    assert response.status_code == 200
    itinerary = response.json()["itinerary"]
    assert itinerary is not None
    return itinerary


def _visa_by_nationality(itinerary: dict) -> dict[str, dict]:
    return {
        item["nationality"]: item
        for item in itinerary["visa_summary"]["individual_assessments"]
    }


def _outline_text(itinerary: dict) -> str:
    return " ".join(
        str(value) for day in itinerary["daily_outline"] for value in day.values()
    ).casefold()


def test_manchester_nigerian_family_gets_visitor_visa_and_family_plan(client):
    itinerary = _plan(client, MANCHESTER)
    brief = itinerary["trip_brief"]
    assert brief["destination"] == "Manchester"
    assert brief["start_date"] == "2026-09-15"
    assert brief["end_date"] == "2026-09-29"
    assert brief["travellers"] == {
        "adults": 1, "children": 1, "infants": 0, "minor_ages": [10],
    }
    assert _visa_by_nationality(itinerary)["Nigerian"]["visa_type"] == "Standard Visitor Visa"
    outline = _outline_text(itinerary)
    assert "old trafford" in outline
    assert "etihad" in outline
    assert "lake district or peak district" in outline


def test_castelmezzano_preserves_remote_destination_and_us_visa_free_rule(client):
    itinerary = _plan(client, CASTELMEZZANO)
    brief = itinerary["trip_brief"]
    assert brief["destination"] == "Castelmezzano"
    assert brief["start_date"] == "2027-05-22"
    assert brief["end_date"] == "2027-05-30"
    assert _visa_by_nationality(itinerary)["American"]["visa_status"] == "VISA_NOT_REQUIRED"
    assert "connect through" not in " ".join(brief["requested_activities"]).casefold()
    assert brief["dining_preferences"] == ["Family-run trattoria"]
    outline = _outline_text(itinerary)
    assert "dolomiti lucane" in outline
    assert "pietrapertosa" in outline


def test_blowing_rock_italian_family_gets_esta(client):
    itinerary = _plan(client, BLOWING_ROCK)
    brief = itinerary["trip_brief"]
    assert brief["destination"] == "Blowing Rock"
    assert brief["start_date"] == "2027-07-06"
    assert brief["travellers"]["minor_ages"] == [9, 13]
    assert _visa_by_nationality(itinerary)["Italian"]["visa_type"] == "ESTA"
    outline = _outline_text(itinerary)
    assert "blue ridge parkway" in outline
    assert "horseback riding" in outline


def test_ronda_handles_each_passport_and_italian_long_stay_document(client):
    itinerary = _plan(client, RONDA)
    brief = itinerary["trip_brief"]
    assert brief["destination"] == "Ronda"
    assert brief["start_date"] == "2027-06-03"
    assert brief["nationalities"] == ["Italian", "American", "Nigerian"]
    assert brief["residency_documents"] == ["Nigerian: Italian long term visa"]
    assessments = _visa_by_nationality(itinerary)
    assert assessments["Italian"]["visa_type"] == "None (EU free movement)"
    assert assessments["American"]["visa_status"] == "VISA_NOT_REQUIRED"
    assert assessments["Nigerian"]["visa_status"] == "VISA_NOT_REQUIRED"
    assert "residence permit" in assessments["Nigerian"]["visa_type"]
    outline = _outline_text(itinerary)
    assert "puente nuevo and el tajo gorge" in outline
    assert "white village" in outline
    assert "spa treatment" not in outline


def test_beaufort_preserves_coastal_plan_and_italian_esta(client):
    itinerary = _plan(client, BEAUFORT)
    brief = itinerary["trip_brief"]
    assert brief["destination"] == "Beaufort"
    assert brief["start_date"] == "2027-06-12"
    assert brief["end_date"] == "2027-06-19"
    assert _visa_by_nationality(itinerary)["Italian"]["visa_type"] == "ESTA"
    outline = _outline_text(itinerary)
    assert "crystal coast" in outline
    assert "cape lookout national seashore" in outline
    assert "maritime history museum" in outline
