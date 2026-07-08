from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class Pagination:
    limit: int = 20
    offset: int = 0
    total: int = 0

    @property
    def has_more(self) -> bool:
        return (self.offset + self.limit) < self.total

    @property
    def page_number(self) -> int:
        return (self.offset // self.limit) + 1 if self.limit else 1

    def next_offset(self) -> int:
        return self.offset + self.limit

    def prev_offset(self) -> int:
        return max(0, self.offset - self.limit)


@dataclass
class Page(Generic[T]):
    items: list[T] = field(default_factory=list)
    pagination: Pagination = field(default_factory=Pagination)

    @classmethod
    def of(cls, items: list[T], total: int, limit: int = 20, offset: int = 0) -> Page[T]:
        return cls(
            items=items,
            pagination=Pagination(limit=limit, offset=offset, total=total),
        )
