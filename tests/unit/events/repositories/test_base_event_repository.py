"""
============================================================
Nexa Provider Platform
File: tests/shared/events/repositories/test_base_event_repository.py
Layer: Shared Event Repository Tests
Milestone: NPP-M006.3.11 — Event Repository Unit Tests
============================================================

Unit tests for BaseEventRepository.

The suite verifies repository identity, constructor validation,
event-identifier validation, EventEnvelope validation, exception
context, and preservation of immutable envelopes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

import pytest

from shared.events.event_context import EventContext
from shared.events.event_envelope import EventEnvelope
from shared.events.event_interface import EventInterface
from shared.events.repositories.base_event_repository import BaseEventRepository
from shared.events.repositories.event_repository_errors import (
    EventIdentifierError,
    EventInvalidError,
    EventRepositoryConfigurationError,
)
from shared.events.repositories.event_repository_types import (
    EventRepositoryOperation,
    EventRepositoryType,
)


class StubEvent(EventInterface):
    """Minimal EventInterface implementation used by repository tests."""

    def __init__(self, event_id: str = "evt-001") -> None:
        self._event_id = event_id
        self._event_type = "TEST_EVENT"
        self._event_version = 1
        self._occurred_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self._metadata = MappingProxyType({"test": True})
        self._payload = MappingProxyType({"value": 1})

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


class ConcreteBaseEventRepository(BaseEventRepository):
    """Concrete test double satisfying the abstract repository contract."""

    def store(self, envelope: EventEnvelope):
        raise NotImplementedError

    def get(self, event_id: str):
        raise NotImplementedError

    def list_all(self):
        raise NotImplementedError

    def exists(self, event_id: str):
        raise NotImplementedError

    def count(self):
        raise NotImplementedError

    def delete(self, event_id: str):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError


@pytest.fixture
def repository() -> ConcreteBaseEventRepository:
    return ConcreteBaseEventRepository("primary-events")


@pytest.fixture
def valid_envelope() -> EventEnvelope:
    return EventEnvelope(
        event=StubEvent("evt-001"),
        context=EventContext(),
    )


def test_constructor_normalizes_repository_name() -> None:
    repository = ConcreteBaseEventRepository("  primary-events  ")

    assert repository.repository_name == "primary-events"


def test_constructor_uses_memory_repository_type_by_default() -> None:
    repository = ConcreteBaseEventRepository("primary-events")

    assert repository.repository_type == EventRepositoryType.MEMORY.value


@pytest.mark.parametrize("repository_type", list(EventRepositoryType))
def test_constructor_exposes_serialized_repository_type(
    repository_type: EventRepositoryType,
) -> None:
    repository = ConcreteBaseEventRepository(
        "primary-events",
        repository_type=repository_type,
    )

    assert repository.repository_type == repository_type.value


@pytest.mark.parametrize("repository_name", [None, 42, object()])
def test_constructor_rejects_non_string_repository_name(
    repository_name: object,
) -> None:
    with pytest.raises(EventRepositoryConfigurationError) as exc_info:
        ConcreteBaseEventRepository(repository_name)  # type: ignore[arg-type]

    error = exc_info.value
    assert error.message == "repository_name must be a string."
    assert error.error_code.endswith("-002")


@pytest.mark.parametrize("repository_name", ["", " ", "\t", "\n"])
def test_constructor_rejects_empty_repository_name(
    repository_name: str,
) -> None:
    with pytest.raises(EventRepositoryConfigurationError) as exc_info:
        ConcreteBaseEventRepository(repository_name)

    error = exc_info.value
    assert error.message == "repository_name must not be empty."
    assert error.error_code.endswith("-002")


@pytest.mark.parametrize("repository_type", ["memory", None, 1])
def test_constructor_rejects_invalid_repository_type(
    repository_type: object,
) -> None:
    with pytest.raises(EventRepositoryConfigurationError) as exc_info:
        ConcreteBaseEventRepository(
            "primary-events",
            repository_type=repository_type,  # type: ignore[arg-type]
        )

    error = exc_info.value
    assert error.message == "repository_type must be an EventRepositoryType."
    assert error.repository == "primary-events"
    assert error.metadata["received_type"] == type(repository_type).__name__


def test_validate_event_id_returns_normalized_identifier(
    repository: ConcreteBaseEventRepository,
) -> None:
    result = repository.validate_event_id("  evt-001  ")

    assert result == "evt-001"


@pytest.mark.parametrize("event_id", [None, 123, object()])
def test_validate_event_id_rejects_missing_or_non_string_identifier(
    repository: ConcreteBaseEventRepository,
    event_id: object,
) -> None:
    with pytest.raises(EventIdentifierError) as exc_info:
        repository.validate_event_id(
            event_id,
            operation=EventRepositoryOperation.READ,
        )

    error = exc_info.value
    assert error.operation == EventRepositoryOperation.READ.value
    assert error.repository == "primary-events"
    assert error.repository_type == EventRepositoryType.MEMORY.value


@pytest.mark.parametrize("event_id", ["", " ", "\t", "\n"])
def test_validate_event_id_rejects_empty_identifier(
    repository: ConcreteBaseEventRepository,
    event_id: str,
) -> None:
    with pytest.raises(EventIdentifierError) as exc_info:
        repository.validate_event_id(event_id)

    assert exc_info.value.message == "event_id must not be empty."


def test_validate_event_id_reports_received_type_for_non_string_value(
    repository: ConcreteBaseEventRepository,
) -> None:
    with pytest.raises(EventIdentifierError) as exc_info:
        repository.validate_event_id(99)

    assert exc_info.value.metadata == {"received_type": "int"}


def test_validate_envelope_returns_original_envelope(
    repository: ConcreteBaseEventRepository,
    valid_envelope: EventEnvelope,
) -> None:
    result = repository.validate_envelope(valid_envelope)

    assert result is valid_envelope


def test_validate_envelope_uses_store_operation_by_default(
    repository: ConcreteBaseEventRepository,
) -> None:
    with pytest.raises(EventInvalidError) as exc_info:
        repository.validate_envelope(object())

    assert exc_info.value.operation == EventRepositoryOperation.STORE.value


def test_validate_envelope_rejects_non_envelope_value(
    repository: ConcreteBaseEventRepository,
) -> None:
    with pytest.raises(EventInvalidError) as exc_info:
        repository.validate_envelope(
            {"event_id": "evt-001"},
            operation=EventRepositoryOperation.READ,
        )

    error = exc_info.value
    assert error.message == "envelope must be an EventEnvelope."
    assert error.operation == EventRepositoryOperation.READ.value
    assert error.repository == "primary-events"
    assert error.repository_type == EventRepositoryType.MEMORY.value
    assert error.metadata == {"received_type": "dict"}


@pytest.mark.parametrize("event_id", ["", " ", "\t"])
def test_validate_envelope_wraps_invalid_event_identifier(
    repository: ConcreteBaseEventRepository,
    event_id: str,
) -> None:
    envelope = EventEnvelope(
        event=StubEvent(event_id),
        context=EventContext(),
    )

    with pytest.raises(EventInvalidError) as exc_info:
        repository.validate_envelope(envelope)

    error = exc_info.value
    assert error.message == "EventEnvelope contains an invalid event_id."
    assert isinstance(error.cause, EventIdentifierError)
    assert error.__cause__ is error.cause


def test_validate_envelope_rejects_non_normalized_event_identifier(
    repository: ConcreteBaseEventRepository,
) -> None:
    envelope = EventEnvelope(
        event=StubEvent("  evt-001  "),
        context=EventContext(),
    )

    with pytest.raises(EventInvalidError) as exc_info:
        repository.validate_envelope(
            envelope,
            operation=EventRepositoryOperation.STORE,
        )

    error = exc_info.value
    assert error.message == "EventEnvelope event_id must already be normalized."
    assert error.event_id == "evt-001"
    assert error.metadata == {"original_event_id": "  evt-001  "}


def test_repository_identity_properties_are_read_only(
    repository: ConcreteBaseEventRepository,
) -> None:
    with pytest.raises(AttributeError):
        repository.repository_name = "changed"  # type: ignore[misc]

    with pytest.raises(AttributeError):
        repository.repository_type = "changed"  # type: ignore[misc]
