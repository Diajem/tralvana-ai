from ai.intelligence.knowledge.entities import Attraction, City, Museum, Restaurant
from ai.intelligence.knowledge.knowledge_graph import KnowledgeGraph
from ai.intelligence.knowledge.knowledge_service import KnowledgeService
from ai.intelligence.knowledge.relationships import Relationship, RelationshipType
from ai.planning.itinerary_builder import ItineraryBuilder


def _relationship(
    source_id: str,
    source_type: str,
    relationship_type: RelationshipType,
    target_id: str,
    target_type: str,
) -> Relationship:
    return Relationship(
        source_id=source_id,
        source_type=source_type,
        relationship_type=relationship_type,
        target_id=target_id,
        target_type=target_type,
    )


def _builder_with_city() -> tuple[ItineraryBuilder, KnowledgeGraph]:
    graph = KnowledgeGraph()
    graph.add_node(City("city_test", "Test City", "country_test"), "City")
    return ItineraryBuilder(KnowledgeService(graph)), graph


def test_build_queries_attractions_and_museums_without_inventing_restaurant_currency() -> None:
    builder, graph = _builder_with_city()
    graph.add_node(
        Attraction("attr_landmark", "Living Landmark", "city_test"),
        "Attraction",
    )
    graph.add_node(
        Museum("museum_history", "Current History Museum", "city_test"),
        "Museum",
    )
    graph.add_node(
        Restaurant("restaurant_local", "Local Table", "city_test"),
        "Restaurant",
    )
    graph.add_edge(
        _relationship(
            "attr_landmark",
            "Attraction",
            RelationshipType.NEAR,
            "city_test",
            "City",
        )
    )
    graph.add_edge(
        _relationship(
            "museum_history",
            "Museum",
            RelationshipType.LOCATED_IN,
            "city_test",
            "City",
        )
    )
    graph.add_edge(
        _relationship(
            "restaurant_local",
            "Restaurant",
            RelationshipType.BELONGS_TO,
            "city_test",
            "City",
        )
    )

    day_two = builder.build(
        destination="test city",
        duration_days=3,
        goal_type="GENERAL_TRAVEL",
        budget_style="balanced",
    )[1]

    assert day_two["morning"] == "Explore Living Landmark"
    assert day_two["afternoon"] == "Visit Current History Museum"
    assert day_two["evening"] == "Welcome dinner at a celebrated local restaurant"


def test_builder_reflects_graph_mutation_after_construction() -> None:
    builder, graph = _builder_with_city()

    before = builder.build(
        destination="Test City",
        duration_days=3,
        goal_type="GENERAL_TRAVEL",
        budget_style="balanced",
    )[1]
    assert before["morning"] == "Guided walking tour of the city centre"

    graph.add_node(
        Attraction("attr_new", "Newly Added Place", "city_test"),
        "Attraction",
    )
    graph.add_edge(
        _relationship(
            "attr_new",
            "Attraction",
            RelationshipType.NEAR,
            "city_test",
            "City",
        )
    )

    after = builder.build(
        destination="Test City",
        duration_days=3,
        goal_type="GENERAL_TRAVEL",
        budget_style="balanced",
    )[1]
    assert after["morning"] == "Explore Newly Added Place"


def test_wrong_relationship_type_is_not_used_for_enrichment() -> None:
    builder, graph = _builder_with_city()
    graph.add_node(
        Attraction("attr_wrong_edge", "Wrongly Connected Place", "city_test"),
        "Attraction",
    )
    graph.add_edge(
        _relationship(
            "attr_wrong_edge",
            "Attraction",
            RelationshipType.PART_OF,
            "city_test",
            "City",
        )
    )

    day_two = builder.build(
        destination="Test City",
        duration_days=3,
        goal_type="GENERAL_TRAVEL",
        budget_style="balanced",
    )[1]

    assert day_two["morning"] == "Guided walking tour of the city centre"
    assert "Wrongly Connected Place" not in str(day_two)


def test_unknown_destination_preserves_generic_templates() -> None:
    builder, _ = _builder_with_city()

    day_two = builder.build(
        destination="Unknown City",
        duration_days=3,
        goal_type="GENERAL_TRAVEL",
        budget_style="balanced",
    )[1]

    assert day_two["morning"] == "Guided walking tour of the city centre"
    assert day_two["afternoon"] == "Key landmarks and photo stops"
    assert day_two["evening"] == "Welcome dinner at a celebrated local restaurant"


def test_duplicate_relationships_do_not_duplicate_rotation_entries() -> None:
    builder, graph = _builder_with_city()
    graph.add_node(
        Attraction("attr_unique", "Only Once", "city_test"),
        "Attraction",
    )
    relationship = _relationship(
        "attr_unique",
        "Attraction",
        RelationshipType.NEAR,
        "city_test",
        "City",
    )
    graph.add_edge(relationship)
    graph.add_edge(relationship)

    days = builder.build(
        destination="Test City",
        duration_days=4,
        goal_type="GENERAL_TRAVEL",
        budget_style="balanced",
    )

    assert days[1]["morning"] == "Explore Only Once"
    assert days[2]["morning"] != "Explore Only Once"


def test_two_week_relaxation_plan_has_no_repeated_arrival_or_resort_beach_defaults() -> None:
    builder, _ = _builder_with_city()
    days = builder.build(
        destination="Dublin",
        duration_days=14,
        goal_type="RELAXATION",
        budget_style="balanced",
    )

    assert len(days) == 14
    assert days[0]["theme"] == "Arrival & Orientation"
    assert days[-1]["theme"] == "Departure Day"
    assert len({day["theme"] for day in days}) == 14
    plan_text = str(days).lower()
    assert "resort orientation" not in plan_text
    assert "beach relaxation" not in plan_text


def test_two_week_family_plan_is_destination_neutral_and_non_repetitive() -> None:
    builder, _ = _builder_with_city()
    days = builder.build(
        destination="Dublin",
        duration_days=14,
        goal_type="FAMILY_TRIP",
        budget_style="balanced",
    )

    assert len({day["theme"] for day in days}) == 14
    plan_text = str(days).lower()
    assert "arrival & kids' first day" not in plan_text
    assert "theme park day" not in plan_text
    assert "leisure & beach day" not in plan_text


def test_football_outline_never_invents_a_match_day() -> None:
    builder, _ = _builder_with_city()
    days = builder.build(
        destination="New York",
        duration_days=7,
        goal_type="FOOTBALL_TRAVEL",
        budget_style="balanced",
        interests=["soccer"],
    )

    plan_text = str(days).lower()
    assert "match day experience" not in plan_text
    assert "watch the match at the ground" not in plan_text
    assert "attend a confirmed fixture" in plan_text
