from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from travelos.shared.pagination import Page, Pagination

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Contract for all TravelOS repositories.

    Concrete implementations swap the backing store (in-memory â†’ PostgreSQL)
    without changing callers.
    """

    @abstractmethod
    def save(self, entity: T) -> T:
        """Persist or update an entity. Returns the saved entity."""

    @abstractmethod
    def get(self, entity_id: str) -> T | None:
        """Retrieve an entity by ID. Returns None if not found."""

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID. Returns True if deleted, False if not found."""

    @abstractmethod
    def list_all(self) -> list[T]:
        """Return all entities (no pagination). Use with caution on large stores."""

    def list_page(self, pagination: Pagination) -> Page[T]:
        """Paginated list. Default implementation slices list_all()."""
        all_items = self.list_all()
        total = len(all_items)
        sliced = all_items[pagination.offset: pagination.offset + pagination.limit]
        return Page.of(sliced, total=total, limit=pagination.limit, offset=pagination.offset)

    def exists(self, entity_id: str) -> bool:
        return self.get(entity_id) is not None
