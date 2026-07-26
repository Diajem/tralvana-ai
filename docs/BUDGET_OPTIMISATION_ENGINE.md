# Budget Optimisation Engine — T-033

T-033 allocates one shared USD budget across multiple proposed trips. It builds
on T-018 Budget Intelligence; it does not create a second price vocabulary or
claim live costs.

## API

`POST /budget/optimise`

Each trip supplies:

- a unique `trip_reference`;
- destination, duration, adults, and children;
- priority from 1 (lowest) to 5 (highest);
- a preferred budget style; and
- the minimum acceptable style.

The five styles are the existing Budget Intelligence tiers:
`backpacker`, `budget`, `balanced`, `comfort`, and `luxury`.

The portfolio contains 1–10 trips and one `portfolio_budget_usd` cap.

## Optimisation contract

For each trip, the engine generates the existing five estimated Budget
Intelligence candidates and considers only styles from the declared minimum up
to the preferred style.

The deterministic optimiser:

1. retains every preferred tier when the cap allows;
2. never upgrades above a preferred tier simply to consume spare budget;
3. never downgrades below a declared minimum;
4. weights preference retention more strongly for higher-priority trips;
5. chooses the strongest combined preference fit within the cap; and
6. returns an explicit minimum-tier plan and exact shortfall when no feasible
   allocation exists.

The search uses a pruned Pareto frontier of cost and weighted preference
utility. It is exhaustive over the surviving non-dominated states and capped
at ten trips by the public schema.

## Response

The response reconciles:

- preferred, minimum, optimised, remaining, saving, and shortfall totals;
- the selected tier and cost breakdown for every trip;
- whether each trip changed and why;
- estimated-cost confidence;
- assumptions, risks, next actions, and a summary; and
- `data_source: ESTIMATED_REGIONAL_RATES`.

An infeasible response is still HTTP 200 because the optimisation ran
successfully; `feasible: false` and `shortfall_usd` describe the business
outcome. Invalid inputs remain HTTP 422.

## One cost model

`ai/discovery/budget/budget_cost_model.py` now owns the canonical regional
daily, cabin/haul flight, style, and child-factor inputs. Both
`MockBudgetProvider` and the legacy `BudgetEstimator` consume it.

`BudgetEstimator` still returns its established trip-planner response shape and
still uses Knowledge Graph reasoning when available. Its old independent
global fallback tables are removed; the fallback now passes through the same
provider-shaped record and `BudgetNormalizer` used by Budget Intelligence.

## Grounding

This engine does not:

- query live flight or accommodation inventory;
- convert currencies;
- predict exchange rates, taxes, or fees;
- book, reserve, or charge anything; or
- silently relax a minimum tier.

Every output repeats the estimated-source limitation and asks the traveller to
replace estimates with live quotes before booking.
