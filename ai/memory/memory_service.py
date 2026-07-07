from typing import Any


class MemoryService:
    """In-process profile cache for the agent layer.

    The API layer calls store_profile() after creating a profile so that
    agents can retrieve it without a DB round-trip. Replaced by a persistent
    adapter in Sprint 2.
    """

    def __init__(self) -> None:
        self._profiles: dict[str, dict[str, Any]] = {}

    def store_profile(self, traveller_id: str, profile: dict[str, Any]) -> None:
        self._profiles[traveller_id] = profile

    def retrieve_profile(self, traveller_id: str) -> dict[str, Any] | None:
        return self._profiles.get(traveller_id)

    def clear(self, traveller_id: str) -> None:
        self._profiles.pop(traveller_id, None)

    def profile_count(self) -> int:
        return len(self._profiles)


# Module-level singleton shared with the orchestrator.
memory_service = MemoryService()
