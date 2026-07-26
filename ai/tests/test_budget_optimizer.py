from ai.discovery.budget.budget_cost_model import raw_budget_candidate
from ai.discovery.budget.budget_normalizer import budget_normalizer
from ai.discovery.budget.budget_optimizer import BudgetOptimizer
from ai.planning.budget_estimator import BudgetEstimator


def _trip(
    reference,
    destination,
    *,
    duration_days=7,
    adults=2,
    children=0,
    priority=3,
    preferred_style="comfort",
    minimum_style="budget",
):
    return {
        "trip_reference": reference,
        "destination": destination,
        "duration_days": duration_days,
        "adults": adults,
        "children": children,
        "priority": priority,
        "preferred_style": preferred_style,
        "minimum_style": minimum_style,
    }


def test_generous_cap_retains_every_preferred_tier():
    output = BudgetOptimizer().optimise(
        portfolio_budget_usd=50_000,
        trips=[
            _trip("new-york", "New York"),
            _trip("paris", "Paris", preferred_style="balanced"),
        ],
    )

    assert output["feasible"] is True
    assert [item["selected_style"] for item in output["allocations"]] == [
        "comfort",
        "balanced",
    ]
    assert all(item["changed"] is False for item in output["allocations"])
    assert output["optimised_total_usd"] == output["preferred_total_usd"]
    assert output["savings_usd"] == 0


def test_shared_cap_downgrades_lower_priority_trip_first_when_possible():
    output = BudgetOptimizer().optimise(
        portfolio_budget_usd=16_000,
        trips=[
            _trip(
                "new-york",
                "New York",
                duration_days=15,
                priority=5,
                minimum_style="balanced",
            ),
            _trip("paris", "Paris", priority=1),
        ],
    )
    by_reference = {
        item["trip_reference"]: item for item in output["allocations"]
    }

    assert output["feasible"] is True
    assert by_reference["new-york"]["selected_style"] == "comfort"
    assert by_reference["paris"]["selected_style"] == "budget"
    assert by_reference["paris"]["changed"] is True
    assert output["optimised_total_usd"] <= 16_000


def test_optimizer_never_drops_below_minimum_or_upgrades_above_preferred():
    output = BudgetOptimizer().optimise(
        portfolio_budget_usd=100_000,
        trips=[
            _trip(
                "accra",
                "Accra",
                preferred_style="balanced",
                minimum_style="balanced",
            )
        ],
    )

    allocation = output["allocations"][0]
    assert allocation["selected_style"] == "balanced"
    assert allocation["minimum_style"] == "balanced"
    assert allocation["preferred_style"] == "balanced"


def test_infeasible_cap_returns_minimum_plan_and_exact_shortfall():
    output = BudgetOptimizer().optimise(
        portfolio_budget_usd=1_000,
        trips=[
            _trip("new-york", "New York", minimum_style="balanced"),
            _trip("paris", "Paris", minimum_style="budget"),
        ],
    )

    assert output["feasible"] is False
    assert [item["selected_style"] for item in output["allocations"]] == [
        "balanced",
        "budget",
    ]
    assert output["optimised_total_usd"] == output["minimum_total_usd"]
    assert output["shortfall_usd"] == output["minimum_total_usd"] - 1_000
    assert output["remaining_budget_usd"] == 0
    assert "cannot fund" in output["risks"][-1]


def test_savings_and_totals_reconcile_exactly():
    output = BudgetOptimizer().optimise(
        portfolio_budget_usd=10_000,
        trips=[
            _trip(
                "new-york",
                "New York",
                duration_days=15,
                priority=5,
                minimum_style="balanced",
            ),
            _trip("paris", "Paris", priority=2),
        ],
    )

    assert output["optimised_total_usd"] == sum(
        item["selected_cost_usd"] for item in output["allocations"]
    )
    assert output["savings_usd"] == (
        output["preferred_total_usd"] - output["optimised_total_usd"]
    )
    assert output["remaining_budget_usd"] == (
        output["portfolio_budget_usd"] - output["optimised_total_usd"]
    )


def test_allocation_exposes_estimated_source_breakdown_and_tradeoff():
    output = BudgetOptimizer().optimise(
        portfolio_budget_usd=3_000,
        trips=[_trip("tokyo", "Tokyo", preferred_style="luxury")],
    )
    allocation = output["allocations"][0]

    assert output["data_source"] == "ESTIMATED_REGIONAL_RATES"
    assert allocation["data_source"] == "ESTIMATED_REGIONAL_RATES"
    assert sum(allocation["cost_breakdown"].values()) == allocation[
        "selected_cost_usd"
    ]
    assert allocation["tradeoff"]
    assert 0.0 <= output["estimate_confidence"] <= 0.7
    assert "No live" in output["assumptions"][-1]


def test_children_affect_cost_through_existing_cost_model():
    optimizer = BudgetOptimizer()
    without_child = optimizer.optimise(
        portfolio_budget_usd=100_000,
        trips=[_trip("lagos", "Lagos", children=0)],
    )
    with_child = optimizer.optimise(
        portfolio_budget_usd=100_000,
        trips=[_trip("lagos", "Lagos", children=1)],
    )

    assert with_child["optimised_total_usd"] > without_child[
        "optimised_total_usd"
    ]


def test_unknown_destination_uses_same_global_band_deterministically():
    optimizer = BudgetOptimizer()
    request = {
        "portfolio_budget_usd": 20_000,
        "trips": [_trip("unknown", "Atlantis")],
    }

    assert optimizer.optimise(**request) == optimizer.optimise(**request)


def test_legacy_estimator_fallback_uses_canonical_budget_cost_model():
    estimator = BudgetEstimator()
    result = estimator.estimate(
        destination="Atlantis",
        duration_days=8,
        budget_style="balanced",
        cabin_class="business",
        adults=2,
    )
    canonical = budget_normalizer.normalize(
        raw_budget_candidate(
            destination="Atlantis",
            budget_style="balanced",
            cabin_class="business",
            duration_days=8,
            adults=2,
            children=0,
        )
    )

    assert result["source"] == "budget_intelligence_cost_model"
    assert result["total_estimate_usd"] == canonical["total_cost_usd"]
    assert result["flights_usd"] == canonical["flight_cost_usd"]
    assert result["accommodation_usd"] == canonical["accommodation_usd"]
    assert "No live" in result["notes"][2]


def test_optimizer_does_not_mutate_trip_inputs():
    trips = [_trip("paris", "Paris")]
    before = [dict(trips[0])]

    BudgetOptimizer().optimise(
        portfolio_budget_usd=10_000,
        trips=trips,
    )

    assert trips == before
