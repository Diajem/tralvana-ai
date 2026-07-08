from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class Error:
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


@dataclass
class Result(Generic[T]):
    success: bool
    value: T | None
    error: Error | None

    @classmethod
    def ok(cls, value: T) -> Result[T]:
        return cls(success=True, value=value, error=None)

    @classmethod
    def fail(cls, code: str, message: str, **details: Any) -> Result[T]:
        return cls(
            success=False,
            value=None,
            error=Error(code=code, message=message, details=details),
        )

    def unwrap(self) -> T:
        if not self.success or self.value is None:
            raise ValueError(f"Result is not ok: {self.error}")
        return self.value

    def __bool__(self) -> bool:
        return self.success
