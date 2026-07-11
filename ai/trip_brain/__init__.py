"""
Trip Brain — the Coordinator in docs/ORCHESTRATION_PATTERN.md.

Orchestrates the six Discovery Layer modules (Flight, Accommodation,
Destination, Budget, Visa, Weather & Safety Intelligence) behind one
traveller-facing response for broad requests (Intent.PLAN_TRIP).

Trip Brain is an orchestration layer, not a seventh Discovery module — it
calls each module's existing public service method
(`*_from_conversation()`), never a Provider or Repository directly.

See docs/TRIP_BRAIN_ARCHITECTURE.md and docs/ADR/ADR-017-trip-brain.md.
"""

from ai.trip_brain.coordinator import TripBrain, trip_brain

__all__ = ["TripBrain", "trip_brain"]
