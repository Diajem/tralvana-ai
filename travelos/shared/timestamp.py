from __future__ import annotations

from datetime import datetime, timezone


class Timestamp:
    """UTC timestamp wrapper used across all domain events and entities."""

    __slots__ = ("_value",)

    def __init__(self, value: datetime | None = None) -> None:
        self._value = value or datetime.now(timezone.utc)

    @classmethod
    def now(cls) -> Timestamp:
        return cls()

    @classmethod
    def from_iso(cls, value: str) -> Timestamp:
        return cls(datetime.fromisoformat(value))

    @property
    def value(self) -> datetime:
        return self._value

    def isoformat(self) -> str:
        return self._value.isoformat()

    def __str__(self) -> str:
        return self.isoformat()

    def __repr__(self) -> str:
        return f"Timestamp({self.isoformat()!r})"

    def __lt__(self, other: Timestamp) -> bool:
        return self._value < other._value

    def __le__(self, other: Timestamp) -> bool:
        return self._value <= other._value
