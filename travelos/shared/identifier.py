from __future__ import annotations

import uuid


class Identifier:
    """Typed UUID wrapper for all domain entity identifiers."""

    __slots__ = ("_value",)

    def __init__(self, value: str | None = None) -> None:
        self._value = value or str(uuid.uuid4())

    @classmethod
    def generate(cls) -> Identifier:
        return cls()

    @classmethod
    def from_string(cls, value: str) -> Identifier:
        return cls(value)

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"Identifier({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Identifier):
            return self._value == other._value
        return self._value == str(other)

    def __hash__(self) -> int:
        return hash(self._value)
