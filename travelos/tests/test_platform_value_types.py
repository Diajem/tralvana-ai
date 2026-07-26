from datetime import datetime, timezone
from uuid import UUID

from travelos.shared.identifier import Identifier
from travelos.shared.pagination import Page, Pagination
from travelos.shared.timestamp import Timestamp


def test_generated_identifiers_are_valid_unique_uuids():
    first = Identifier.generate()
    second = Identifier.generate()

    assert UUID(first.value)
    assert UUID(second.value)
    assert first != second


def test_identifier_round_trip_equality_hash_and_repr():
    first = Identifier.from_string("traveller-123")
    second = Identifier("traveller-123")

    assert first == second
    assert first == "traveller-123"
    assert hash(first) == hash(second)
    assert str(first) == "traveller-123"
    assert repr(first) == "Identifier('traveller-123')"


def test_timestamp_now_is_timezone_aware_and_round_trips():
    timestamp = Timestamp.now()
    restored = Timestamp.from_iso(timestamp.isoformat())

    assert timestamp.value.tzinfo is not None
    assert timestamp.value.utcoffset() == timezone.utc.utcoffset(timestamp.value)
    assert restored.value == timestamp.value
    assert str(restored) == restored.isoformat()
    assert repr(restored) == f"Timestamp({restored.isoformat()!r})"


def test_timestamp_ordering():
    earlier = Timestamp(datetime(2026, 7, 26, 8, 0, tzinfo=timezone.utc))
    later = Timestamp(datetime(2026, 7, 26, 9, 0, tzinfo=timezone.utc))

    assert earlier < later
    assert earlier <= later
    assert earlier <= Timestamp(earlier.value)


def test_pagination_boundaries_and_page_numbers():
    first = Pagination(limit=20, offset=0, total=41)
    middle = Pagination(limit=20, offset=20, total=41)
    last = Pagination(limit=20, offset=40, total=41)

    assert first.has_more is True
    assert first.page_number == 1
    assert first.next_offset() == 20
    assert first.prev_offset() == 0
    assert middle.has_more is True
    assert middle.page_number == 2
    assert middle.prev_offset() == 0
    assert last.has_more is False
    assert last.page_number == 3
    assert last.prev_offset() == 20


def test_zero_limit_pagination_is_safe():
    pagination = Pagination(limit=0, offset=50, total=100)

    assert pagination.page_number == 1
    assert pagination.next_offset() == 50
    assert pagination.prev_offset() == 50


def test_page_factory_preserves_items_and_metadata():
    page = Page.of(["a", "b"], total=5, limit=2, offset=2)

    assert page.items == ["a", "b"]
    assert page.pagination == Pagination(limit=2, offset=2, total=5)
    assert page.pagination.has_more is True
