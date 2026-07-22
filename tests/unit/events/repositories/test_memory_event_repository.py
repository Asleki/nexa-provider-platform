"""
============================================================
Nexa Provider Platform
File: tests/unit/events/repositories/test_memory_event_repository.py
Layer: Shared Event Repository Tests
Milestone: NPP-M006.3.11 — Event Repository Unit Tests
============================================================

Unit tests for MemoryEventRepository.

The suite verifies constructor behavior, deterministic storage,
duplicate protection, retrieval, listing, existence checks,
counting, deletion, clearing, result contracts, metadata, and
preservation of immutable EventEnvelope objects.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

import pytest

from shared.events.event_context import EventContext
from shared.events.event_envelope import EventEnvelope
from shared.events.event_interface import EventInterface
from shared.events.repositories.event_repository_errors import (
    EventDuplicateError,
    EventIdentifierError,
    EventInvalidError,
    EventNotFoundError,
)
from shared.events.repositories.event_repository_result import (
    EventRepositoryResult,
)
from shared.events.repositories.event_repository_types import (
    EventRepositoryOperation,
    EventRepositoryType,
)
from shared.events.repositories.memory_event_repository import (
    MemoryEventRepository,
)


class StubEvent(EventInterface):
    """Minimal immutable-style EventInterface implementation for tests."""

    def __init__(
        self,
        event_id: str,
        *,
        event_type: str = "TEST_EVENT",
        value: int = 1,
    ) -> None:
        self._event_id = event_id
        self._event_type = event_type
        self._event_version = 1
        self._occurred_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self._metadata = MappingProxyType({"test": True})
        self._payload = MappingProxyType({"value": value})

    @property
    def event_id(self) -> str:
        return self._event_id

    @property
    def event_type(self) -> str:
        return self._event_type

    @property
    def event_version(self) -> int:
        return self._event_version

    @property
    def occurred_at(self) -> datetime:
        return self._occurred_at

    @property
    def metadata(self) -> Mapping[str, Any]:
        return self._metadata

    @property
    def payload(self) -> Mapping[str, Any]:
        return self._payload

    def validate(self) -> None:
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "event_version": self.event_version,
            "occurred_at": self.occurred_at.isoformat(),
            "metadata": dict(self.metadata),
            "payload": dict(self.payload),
        }

    def serialize(self) -> str:
        return str(self.to_dict())


def make_envelope(
    event_id: str,
    *,
    event_type: str = "TEST_EVENT",
    value: int = 1,
) -> EventEnvelope:
    """Create a valid EventEnvelope for repository tests."""

    return EventEnvelope(
        event=StubEvent(
            event_id,
            event_type=event_type,
            value=value,
        ),
        context=EventContext(),
    )


@pytest.fixture
def repository() -> MemoryEventRepository:
    return MemoryEventRepository("primary-events")


@pytest.fixture
def envelope_one() -> EventEnvelope:
    return make_envelope("evt-001", value=1)


@pytest.fixture
def envelope_two() -> EventEnvelope:
    return make_envelope("evt-002", value=2)


@pytest.fixture
def envelope_three() -> EventEnvelope:
    return make_envelope("evt-003", value=3)


def test_constructor_uses_default_repository_name() -> None:
    repository = MemoryEventRepository()

    assert repository.repository_name == "memory_event_repository"


def test_constructor_normalizes_repository_name() -> None:
    repository = MemoryEventRepository("  primary-events  ")

    assert repository.repository_name == "primary-events"


def test_constructor_exposes_memory_repository_type(
    repository: MemoryEventRepository,
) -> None:
    assert repository.repository_type == EventRepositoryType.MEMORY.value


def test_new_repository_is_empty(
    repository: MemoryEventRepository,
) -> None:
    count_result = repository.count()
    list_result = repository.list_all()

    assert count_result.count == 0
    assert list_result.envelopes == ()
    assert list_result.count == 0


def test_store_returns_successful_repository_result(
    repository: MemoryEventRepository,
    envelope_one: EventEnvelope,
) -> None:
    result = repository.store(envelope_one)

    assert isinstance(result, EventRepositoryResult)
    assert result.success is True
    assert result.failed is False
    assert result.operation is EventRepositoryOperation.STORE
    assert result.repository == "primary-events"
    assert result.event_id == "evt-001"
    assert result.envelope is envelope_one
    assert result.events_affected == 1
    assert result.count == 1
    assert result.message == "Event envelope stored."


def test_store_adds_envelope_to_repository(
    repository: MemoryEventRepository,
    envelope_one: EventEnvelope,
) -> None:
    repository.store(envelope_one)

    assert repository.count().count == 1
    assert repository.exists("evt-001").metadata["exists"] is True


def test_store_preserves_original_envelope_identity(
    repository: MemoryEventRepository,
    envelope_one: EventEnvelope,
) -> None:
    repository.store(envelope_one)

    result = repository.get("evt-001")

    assert result.envelope is envelope_one


def test_store_includes_repository_type_metadata(
    repository: MemoryEventRepository,
    envelope_one: EventEnvelope,
) -> None:
    result = repository.store(envelope_one)

    assert result.metadata["repository_type"] == EventRepositoryType.MEMORY.value


def test_store_rejects_duplicate_event_identifier(
    repository: MemoryEventRepository,
    envelope_one: EventEnvelope,
) -> None:
    repository.store(envelope_one)

    with pytest.raises(EventDuplicateError) as exc_info:
        repository.store(envelope_one)

    error = exc_info.value
    assert error.operation == EventRepositoryOperation.STORE.value
    assert error.repository == "primary-events"
    assert error.event_id == "evt-001"
    assert error.repository_type == EventRepositoryType.MEMORY.value
    assert repository.count().count == 1


def test_store_rejects_non_envelope_value(
    repository: MemoryEventRepository,
) -> None:
    with pytest.raises(EventInvalidError):
        repository.store({"event_id": "evt-001"})  # type: ignore[arg-type]


def test_store_rejects_non_normalized_event_identifier(
    repository: MemoryEventRepository,
) -> None:
    envelope = make_envelope("  evt-001  ")

    with pytest.raises(EventInvalidError):
        repository.store(envelope)

    assert repository.count().count == 0


def test_get_returns_existing_envelope(
    repository: MemoryEventRepository,
    envelope_one: EventEnvelope,
) -> None:
    repository.store(envelope_one)

    result = repository.get("evt-001")

    assert result.success is True
    assert result.operation is EventRepositoryOperation.READ
    assert result.repository == "primary-events"
    assert result.event_id == "evt-001"
    assert result.envelope is envelope_one
    assert result.events_affected == 1
    assert result.metadata["repository_type"] == EventRepositoryType.MEMORY.value


def test_get_normalizes_lookup_identifier(
    repository: MemoryEventRepository,
    envelope_one: EventEnvelope,
) -> None:
    repository.store(envelope_one)

    result = repository.get("  evt-001  ")

    assert result.event_id == "evt-001"
    assert result.envelope is envelope_one


def test_get_raises_not_found_for_missing_event(
    repository: MemoryEventRepository,
) -> None:
    with pytest.raises(EventNotFoundError) as exc_info:
        repository.get("evt-missing")

    error = exc_info.value
    assert error.operation == EventRepositoryOperation.READ.value
    assert error.repository == "primary-events"
    assert error.event_id == "evt-missing"
    assert error.repository_type == EventRepositoryType.MEMORY.value


@pytest.mark.parametrize("event_id", [None, 123, object()])
def test_get_rejects_non_string_identifier(
    repository: MemoryEventRepository,
    event_id: object,
) -> None:
    with pytest.raises(EventIdentifierError):
        repository.get(event_id)  # type: ignore[arg-type]


def test_list_all_returns_empty_tuple_for_empty_repository(
    repository: MemoryEventRepository,
) -> None:
    result = repository.list_all()

    assert result.operation is EventRepositoryOperation.LIST
    assert result.envelopes == ()
    assert result.events_affected == 0
    assert result.count == 0


def test_list_all_preserves_insertion_order(
    repository: MemoryEventRepository,
    envelope_one: EventEnvelope,
    envelope_two: EventEnvelope,
    envelope_three: EventEnvelope,
) -> None:
    repository.store(envelope_two)
    repository.store(envelope_one)
    repository.store(envelope_three)

    result = repository.list_all()

    assert result.envelopes == (
        envelope_two,
        envelope_one,
        envelope_three,
    )
    assert result.count == 3


def test_list_all_returns_immutable_tuple(
    repository: MemoryEventRepository,
    envelope_one: EventEnvelope,
) -> None:
    repository.store(envelope_one)

    result = repository.list_all()

    assert isinstance(result.envelopes, tuple)

    with pytest.raises(AttributeError):
        result.envelopes.append(envelope_one)  # type: ignore[attr-defined]


def test_exists_returns_true_for_stored_event(
    repository: MemoryEventRepository,
    envelope_one: EventEnvelope,
) -> None:
    repository.store(envelope_one)

    result = repository.exists("evt-001")

    assert result.operation is EventRepositoryOperation.EXISTS
    assert result.event_id == "evt-001"
    assert result.events_affected == 1
    assert result.count == 1
    assert result.metadata["exists"] is True
    assert result.metadata["repository_type"] == EventRepositoryType.MEMORY.value


def test_exists_returns_false_for_missing_event(
    repository: MemoryEventRepository,
) -> None:
    result = repository.exists("evt-missing")

    assert result.operation is EventRepositoryOperation.EXISTS
    assert result.event_id == "evt-missing"
    assert result.events_affected == 0
    assert result.count == 0
    assert result.metadata["exists"] is False


def test_count_tracks_repository_size(
    repository: MemoryEventRepository,
    envelope_one: EventEnvelope,
    envelope_two: EventEnvelope,
) -> None:
    assert repository.count().count == 0

    repository.store(envelope_one)
    assert repository.count().count == 1

    repository.store(envelope_two)
    assert repository.count().count == 2

    repository.delete("evt-001")
    assert repository.count().count == 1


def test_count_result_contains_count_metadata(
    repository: MemoryEventRepository,
    envelope_one: EventEnvelope,
) -> None:
    repository.store(envelope_one)

    result = repository.count()

    assert result.operation is EventRepositoryOperation.COUNT
    assert result.events_affected == 1
    assert result.metadata["count"] == 1
    assert result.metadata["repository_type"] == EventRepositoryType.MEMORY.value


def test_delete_removes_existing_event(
    repository: MemoryEventRepository,
    envelope_one: EventEnvelope,
) -> None:
    repository.store(envelope_one)

    result = repository.delete("evt-001")

    assert result.success is True
    assert result.operation is EventRepositoryOperation.DELETE
    assert result.event_id == "evt-001"
    assert result.events_affected == 1
    assert result.metadata["repository_type"] == EventRepositoryType.MEMORY.value
    assert repository.exists("evt-001").metadata["exists"] is False
    assert repository.count().count == 0


def test_delete_normalizes_identifier(
    repository: MemoryEventRepository,
    envelope_one: EventEnvelope,
) -> None:
    repository.store(envelope_one)

    result = repository.delete("  evt-001  ")

    assert result.event_id == "evt-001"


def test_delete_raises_not_found_for_missing_event(
    repository: MemoryEventRepository,
) -> None:
    with pytest.raises(EventNotFoundError) as exc_info:
        repository.delete("evt-missing")

    error = exc_info.value
    assert error.operation == EventRepositoryOperation.DELETE.value
    assert error.event_id == "evt-missing"


def test_delete_cannot_remove_same_event_twice(
    repository: MemoryEventRepository,
    envelope_one: EventEnvelope,
) -> None:
    repository.store(envelope_one)
    repository.delete("evt-001")

    with pytest.raises(EventNotFoundError):
        repository.delete("evt-001")


def test_clear_removes_all_events_and_reports_removed_count(
    repository: MemoryEventRepository,
    envelope_one: EventEnvelope,
    envelope_two: EventEnvelope,
    envelope_three: EventEnvelope,
) -> None:
    repository.store(envelope_one)
    repository.store(envelope_two)
    repository.store(envelope_three)

    result = repository.clear()

    assert result.success is True
    assert result.operation is EventRepositoryOperation.CLEAR
    assert result.events_affected == 3
    assert result.count == 3
    assert result.metadata["events_removed"] == 3
    assert result.metadata["repository_type"] == EventRepositoryType.MEMORY.value
    assert repository.count().count == 0
    assert repository.list_all().envelopes == ()


def test_clear_empty_repository_is_successful(
    repository: MemoryEventRepository,
) -> None:
    result = repository.clear()

    assert result.success is True
    assert result.operation is EventRepositoryOperation.CLEAR
    assert result.events_affected == 0
    assert result.metadata["events_removed"] == 0


def test_repository_can_store_same_identifier_after_delete(
    repository: MemoryEventRepository,
    envelope_one: EventEnvelope,
) -> None:
    repository.store(envelope_one)
    repository.delete("evt-001")

    replacement = make_envelope("evt-001", value=99)
    result = repository.store(replacement)

    assert result.envelope is replacement
    assert repository.get("evt-001").envelope is replacement


def test_repository_can_store_same_identifier_after_clear(
    repository: MemoryEventRepository,
    envelope_one: EventEnvelope,
) -> None:
    repository.store(envelope_one)
    repository.clear()

    replacement = make_envelope("evt-001", value=99)
    repository.store(replacement)

    assert repository.count().count == 1
    assert repository.get("evt-001").envelope is replacement


def test_repository_identity_properties_are_read_only(
    repository: MemoryEventRepository,
) -> None:
    with pytest.raises(AttributeError):
        repository.repository_name = "changed"  # type: ignore[misc]

    with pytest.raises(AttributeError):
        repository.repository_type = "changed"  # type: ignore[misc]
