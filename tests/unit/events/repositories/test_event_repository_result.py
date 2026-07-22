"""
============================================================
Nexa Provider Platform
File: tests/unit/events/repositories/test_event_repository_result.py
Layer: Shared Event Repository Tests
Milestone: NPP-M006.3.10 — Event Repository Result
============================================================

Unit tests for the immutable EventRepositoryResult contract,
including validation, normalization, serialization, derived
properties, metadata freezing, and operation-specific factories.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import MappingProxyType
from unittest.mock import Mock

import pytest

from shared.events.event_envelope import EventEnvelope
from shared.events.repositories.event_repository_result import (
    EventRepositoryResult,
)
from shared.events.repositories.event_repository_types import (
    EventRepositoryOperation,
)


def make_envelope(
    event_id: str = "evt-001",
    *,
    payload: dict | None = None,
) -> EventEnvelope:
    """
    Create an EventEnvelope-compatible test double.

    Mock(spec=EventEnvelope) reports EventEnvelope as its runtime
    class for isinstance checks while allowing us to control the
    event_id and serialized representation required by this suite.
    """

    envelope = Mock(spec=EventEnvelope)
    envelope.event_id = event_id
    envelope.to_dict.return_value = payload or {
        "event": {
            "event_id": event_id,
            "event_type": "TEST_EVENT",
        },
        "context": {
            "runtime_mode": "simulation",
        },
    }
    return envelope


def make_result(**overrides) -> EventRepositoryResult:
    """Create a valid repository result with optional overrides."""

    values = {
        "success": True,
        "operation": EventRepositoryOperation.STORE,
        "repository": "memory",
        "event_id": None,
        "envelope": None,
        "envelopes": (),
        "events_affected": 0,
        "message": "",
        "metadata": {},
    }
    values.update(overrides)
    return EventRepositoryResult(**values)


def test_constructor_preserves_valid_values():
    envelope = make_envelope()
    result = make_result(
        event_id="evt-001",
        envelope=envelope,
        events_affected=1,
        message="Stored",
        metadata={"source": "unit_test"},
    )

    assert result.success is True
    assert result.operation is EventRepositoryOperation.STORE
    assert result.repository == "memory"
    assert result.event_id == "evt-001"
    assert result.envelope is envelope
    assert result.envelopes == ()
    assert result.events_affected == 1
    assert result.message == "Stored"
    assert result.metadata == {"source": "unit_test"}


@pytest.mark.parametrize("invalid_value", [1, 0, "true", None])
def test_success_requires_actual_bool(invalid_value):
    with pytest.raises(TypeError, match="success must be a boolean"):
        make_result(success=invalid_value)


@pytest.mark.parametrize(
    "invalid_value",
    [
        EventRepositoryOperation.STORE.value,
        "STORE",
        None,
        object(),
    ],
)
def test_operation_requires_repository_operation_enum(invalid_value):
    with pytest.raises(
        TypeError,
        match="operation must be an EventRepositoryOperation",
    ):
        make_result(operation=invalid_value)


@pytest.mark.parametrize("invalid_value", [None, 123, object()])
def test_repository_requires_string(invalid_value):
    with pytest.raises(TypeError, match="repository must be a string"):
        make_result(repository=invalid_value)


@pytest.mark.parametrize("raw_value", ["", " ", "\n\t"])
def test_repository_must_not_be_empty(raw_value):
    with pytest.raises(ValueError, match="repository must not be empty"):
        make_result(repository=raw_value)


def test_repository_is_trimmed():
    result = make_result(repository="  memory  ")

    assert result.repository == "memory"


@pytest.mark.parametrize("invalid_value", [123, object(), True])
def test_event_id_requires_string_when_provided(invalid_value):
    with pytest.raises(
        TypeError,
        match="event_id must be a string when provided",
    ):
        make_result(event_id=invalid_value)


@pytest.mark.parametrize("raw_value", ["", " ", "\n\t"])
def test_event_id_must_not_be_empty_when_provided(raw_value):
    with pytest.raises(
        ValueError,
        match="event_id must not be empty when provided",
    ):
        make_result(event_id=raw_value)


def test_event_id_is_trimmed():
    result = make_result(event_id="  evt-001  ")

    assert result.event_id == "evt-001"


@pytest.mark.parametrize("invalid_value", [object(), {}, "envelope", 1])
def test_envelope_requires_event_envelope_when_provided(invalid_value):
    with pytest.raises(
        TypeError,
        match="envelope must be an EventEnvelope when provided",
    ):
        make_result(envelope=invalid_value)


def test_matching_event_id_and_envelope_are_accepted():
    envelope = make_envelope("evt-001")

    result = make_result(
        event_id="evt-001",
        envelope=envelope,
    )

    assert result.event_id == envelope.event_id


def test_event_id_must_match_envelope_event_id():
    envelope = make_envelope("evt-envelope")

    with pytest.raises(
        ValueError,
        match=r"event_id must match envelope\.event_id",
    ):
        make_result(
            event_id="evt-result",
            envelope=envelope,
        )


def test_envelope_without_explicit_event_id_is_accepted():
    envelope = make_envelope("evt-001")

    result = make_result(envelope=envelope)

    assert result.event_id is None
    assert result.envelope is envelope


def test_envelopes_accept_list_and_freeze_to_tuple():
    first = make_envelope("evt-001")
    second = make_envelope("evt-002")

    result = make_result(envelopes=[first, second])

    assert result.envelopes == (first, second)
    assert isinstance(result.envelopes, tuple)


def test_envelopes_accept_generator_and_freeze_to_tuple():
    first = make_envelope("evt-001")
    second = make_envelope("evt-002")

    result = make_result(
        envelopes=(item for item in (first, second))
    )

    assert result.envelopes == (first, second)


def test_envelopes_reject_non_event_envelope_member():
    valid = make_envelope()

    with pytest.raises(
        TypeError,
        match="envelopes must contain only EventEnvelope objects",
    ):
        make_result(envelopes=(valid, object()))


def test_non_iterable_envelopes_raise_type_error():
    with pytest.raises(TypeError):
        make_result(envelopes=123)


@pytest.mark.parametrize("invalid_value", [1.5, "1", None, object()])
def test_events_affected_requires_integer(invalid_value):
    with pytest.raises(
        TypeError,
        match="events_affected must be an integer",
    ):
        make_result(events_affected=invalid_value)


@pytest.mark.parametrize("invalid_value", [True, False])
def test_events_affected_rejects_boolean(invalid_value):
    with pytest.raises(
        TypeError,
        match="events_affected must be an integer",
    ):
        make_result(events_affected=invalid_value)


@pytest.mark.parametrize("invalid_value", [-1, -100])
def test_events_affected_must_not_be_negative(invalid_value):
    with pytest.raises(
        ValueError,
        match="events_affected must not be negative",
    ):
        make_result(events_affected=invalid_value)


@pytest.mark.parametrize("valid_value", [0, 1, 50])
def test_events_affected_accepts_non_negative_integer(valid_value):
    result = make_result(events_affected=valid_value)

    assert result.events_affected == valid_value


@pytest.mark.parametrize("invalid_value", [None, 123, object()])
def test_message_requires_string(invalid_value):
    with pytest.raises(TypeError, match="message must be a string"):
        make_result(message=invalid_value)


def test_message_is_trimmed():
    result = make_result(message="  Stored successfully.  ")

    assert result.message == "Stored successfully."


@pytest.mark.parametrize(
    "invalid_value",
    [
        [("source", "test")],
        "metadata",
        123,
        object(),
    ],
)
def test_metadata_requires_mapping(invalid_value):
    with pytest.raises(TypeError, match="metadata must be a mapping"):
        make_result(metadata=invalid_value)


def test_metadata_is_copied_and_frozen():
    source = {"source": "original"}

    result = make_result(metadata=source)
    source["source"] = "changed"

    assert result.metadata == {"source": "original"}
    assert isinstance(result.metadata, MappingProxyType)

    with pytest.raises(TypeError):
        result.metadata["source"] = "mutated"


def test_result_dataclass_is_frozen():
    result = make_result()

    with pytest.raises(FrozenInstanceError):
        result.message = "Changed"


def test_result_uses_slots():
    result = make_result()

    assert not hasattr(result, "__dict__")


@pytest.mark.parametrize(
    "success, expected_failed",
    [
        (True, False),
        (False, True),
    ],
)
def test_failed_is_inverse_of_success(success, expected_failed):
    result = make_result(success=success)

    assert result.failed is expected_failed


def test_count_for_list_operation_uses_number_of_envelopes():
    envelopes = (
        make_envelope("evt-001"),
        make_envelope("evt-002"),
    )
    result = make_result(
        operation=EventRepositoryOperation.LIST,
        envelopes=envelopes,
        events_affected=99,
    )

    assert result.count == 2


@pytest.mark.parametrize(
    "operation",
    [
        EventRepositoryOperation.STORE,
        EventRepositoryOperation.READ,
        EventRepositoryOperation.DELETE,
        EventRepositoryOperation.EXISTS,
        EventRepositoryOperation.COUNT,
        EventRepositoryOperation.CLEAR,
    ],
)
def test_count_for_non_list_operation_uses_events_affected(operation):
    result = make_result(
        operation=operation,
        events_affected=7,
    )

    assert result.count == 7


def test_to_dict_returns_complete_plain_dictionary():
    envelope = make_envelope(
        "evt-001",
        payload={
            "event": {"event_id": "evt-001"},
            "context": {"runtime_mode": "simulation"},
        },
    )
    listed = make_envelope(
        "evt-002",
        payload={
            "event": {"event_id": "evt-002"},
            "context": {"runtime_mode": "simulation"},
        },
    )
    result = make_result(
        event_id="evt-001",
        envelope=envelope,
        envelopes=(listed,),
        events_affected=1,
        message="Complete",
        metadata={"source": "unit_test"},
    )

    serialized = result.to_dict()

    assert serialized == {
        "success": True,
        "operation": EventRepositoryOperation.STORE.value,
        "repository": "memory",
        "event_id": "evt-001",
        "envelope": {
            "event": {"event_id": "evt-001"},
            "context": {"runtime_mode": "simulation"},
        },
        "envelopes": [
            {
                "event": {"event_id": "evt-002"},
                "context": {"runtime_mode": "simulation"},
            }
        ],
        "events_affected": 1,
        "message": "Complete",
        "metadata": {"source": "unit_test"},
    }


def test_to_dict_serializes_absent_envelope_as_none():
    serialized = make_result().to_dict()

    assert serialized["envelope"] is None
    assert serialized["envelopes"] == []


def test_to_dict_returns_independent_metadata_dictionary():
    result = make_result(metadata={"source": "unit_test"})

    serialized = result.to_dict()
    serialized["metadata"]["source"] = "changed"

    assert result.metadata["source"] == "unit_test"


def test_to_dict_calls_each_envelope_serializer():
    first = make_envelope("evt-001")
    second = make_envelope("evt-002")
    result = make_result(
        envelope=first,
        envelopes=(first, second),
    )

    result.to_dict()

    assert first.to_dict.call_count == 2
    second.to_dict.assert_called_once_with()


def test_stored_factory_creates_store_result():
    envelope = make_envelope("evt-001")

    result = EventRepositoryResult.stored(
        repository="memory",
        envelope=envelope,
    )

    assert result.success is True
    assert result.failed is False
    assert result.operation is EventRepositoryOperation.STORE
    assert result.repository == "memory"
    assert result.event_id == "evt-001"
    assert result.envelope is envelope
    assert result.events_affected == 1
    assert result.count == 1
    assert result.message == "Event envelope stored."


def test_stored_factory_accepts_custom_message_and_metadata():
    envelope = make_envelope()

    result = EventRepositoryResult.stored(
        repository="memory",
        envelope=envelope,
        message="Custom store message.",
        metadata={"source": "test"},
    )

    assert result.message == "Custom store message."
    assert result.metadata == {"source": "test"}


def test_found_factory_creates_read_result():
    envelope = make_envelope("evt-001")

    result = EventRepositoryResult.found(
        repository="memory",
        envelope=envelope,
    )

    assert result.operation is EventRepositoryOperation.READ
    assert result.event_id == "evt-001"
    assert result.envelope is envelope
    assert result.events_affected == 1
    assert result.message == "Event envelope found."


def test_found_factory_accepts_custom_message_and_metadata():
    envelope = make_envelope()

    result = EventRepositoryResult.found(
        repository="memory",
        envelope=envelope,
        message="Custom read message.",
        metadata={"cache": "hit"},
    )

    assert result.message == "Custom read message."
    assert result.metadata == {"cache": "hit"}


def test_deleted_factory_creates_delete_result():
    result = EventRepositoryResult.deleted(
        repository="memory",
        event_id="evt-001",
    )

    assert result.operation is EventRepositoryOperation.DELETE
    assert result.event_id == "evt-001"
    assert result.envelope is None
    assert result.events_affected == 1
    assert result.message == "Event envelope deleted."


def test_deleted_factory_normalizes_values():
    result = EventRepositoryResult.deleted(
        repository="  memory  ",
        event_id="  evt-001  ",
        message="  Deleted.  ",
        metadata={"reason": "test"},
    )

    assert result.repository == "memory"
    assert result.event_id == "evt-001"
    assert result.message == "Deleted."
    assert result.metadata == {"reason": "test"}


def test_listed_factory_creates_list_result():
    first = make_envelope("evt-001")
    second = make_envelope("evt-002")

    result = EventRepositoryResult.listed(
        repository="memory",
        envelopes=(first, second),
    )

    assert result.operation is EventRepositoryOperation.LIST
    assert result.envelopes == (first, second)
    assert result.events_affected == 2
    assert result.count == 2
    assert result.message == "Event envelopes listed."


def test_listed_factory_accepts_list_and_freezes_it():
    first = make_envelope("evt-001")
    source = [first]

    result = EventRepositoryResult.listed(
        repository="memory",
        envelopes=source,
    )
    source.clear()

    assert result.envelopes == (first,)


def test_listed_factory_handles_empty_collection():
    result = EventRepositoryResult.listed(
        repository="memory",
        envelopes=(),
    )

    assert result.envelopes == ()
    assert result.events_affected == 0
    assert result.count == 0


@pytest.mark.parametrize(
    "exists, expected_affected, expected_message",
    [
        (True, 1, "Event envelope exists."),
        (False, 0, "Event envelope does not exist."),
    ],
)
def test_existence_checked_factory(
    exists,
    expected_affected,
    expected_message,
):
    result = EventRepositoryResult.existence_checked(
        repository="memory",
        event_id="evt-001",
        exists=exists,
    )

    assert result.operation is EventRepositoryOperation.EXISTS
    assert result.event_id == "evt-001"
    assert result.events_affected == expected_affected
    assert result.message == expected_message
    assert result.metadata["exists"] is exists


@pytest.mark.parametrize("invalid_value", [1, 0, "true", None])
def test_existence_checked_requires_actual_bool(invalid_value):
    with pytest.raises(TypeError, match="exists must be a boolean"):
        EventRepositoryResult.existence_checked(
            repository="memory",
            event_id="evt-001",
            exists=invalid_value,
        )


def test_existence_checked_overrides_existing_exists_metadata():
    result = EventRepositoryResult.existence_checked(
        repository="memory",
        event_id="evt-001",
        exists=True,
        metadata={
            "exists": False,
            "source": "unit_test",
        },
    )

    assert result.metadata == {
        "exists": True,
        "source": "unit_test",
    }


@pytest.mark.parametrize("count", [0, 1, 50])
def test_counted_factory_creates_count_result(count):
    result = EventRepositoryResult.counted(
        repository="memory",
        count=count,
    )

    assert result.operation is EventRepositoryOperation.COUNT
    assert result.events_affected == count
    assert result.count == count
    assert result.message == "Event envelopes counted."
    assert result.metadata["count"] == count


@pytest.mark.parametrize("invalid_value", [True, False, 1.5, "1", None])
def test_counted_factory_requires_integer(invalid_value):
    with pytest.raises(TypeError, match="count must be an integer"):
        EventRepositoryResult.counted(
            repository="memory",
            count=invalid_value,
        )


def test_counted_factory_rejects_negative_count():
    with pytest.raises(ValueError, match="count must not be negative"):
        EventRepositoryResult.counted(
            repository="memory",
            count=-1,
        )


def test_counted_factory_overrides_existing_count_metadata():
    result = EventRepositoryResult.counted(
        repository="memory",
        count=4,
        metadata={
            "count": 99,
            "source": "unit_test",
        },
    )

    assert result.metadata == {
        "count": 4,
        "source": "unit_test",
    }


@pytest.mark.parametrize("events_removed", [0, 1, 50])
def test_cleared_factory_creates_clear_result(events_removed):
    result = EventRepositoryResult.cleared(
        repository="memory",
        events_removed=events_removed,
    )

    assert result.operation is EventRepositoryOperation.CLEAR
    assert result.events_affected == events_removed
    assert result.count == events_removed
    assert result.message == "Event repository cleared."
    assert result.metadata["events_removed"] == events_removed


@pytest.mark.parametrize("invalid_value", [True, False, 1.5, "1", None])
def test_cleared_factory_requires_integer(invalid_value):
    with pytest.raises(
        TypeError,
        match="events_removed must be an integer",
    ):
        EventRepositoryResult.cleared(
            repository="memory",
            events_removed=invalid_value,
        )


def test_cleared_factory_rejects_negative_events_removed():
    with pytest.raises(
        ValueError,
        match="events_removed must not be negative",
    ):
        EventRepositoryResult.cleared(
            repository="memory",
            events_removed=-1,
        )


def test_cleared_factory_overrides_existing_metadata_value():
    result = EventRepositoryResult.cleared(
        repository="memory",
        events_removed=3,
        metadata={
            "events_removed": 99,
            "source": "unit_test",
        },
    )

    assert result.metadata == {
        "events_removed": 3,
        "source": "unit_test",
    }


@pytest.mark.parametrize(
    "factory_name, kwargs",
    [
        (
            "stored",
            {
                "repository": "memory",
                "envelope": make_envelope("evt-store"),
            },
        ),
        (
            "found",
            {
                "repository": "memory",
                "envelope": make_envelope("evt-read"),
            },
        ),
        (
            "deleted",
            {
                "repository": "memory",
                "event_id": "evt-delete",
            },
        ),
        (
            "listed",
            {
                "repository": "memory",
                "envelopes": (),
            },
        ),
        (
            "existence_checked",
            {
                "repository": "memory",
                "event_id": "evt-exists",
                "exists": False,
            },
        ),
        (
            "counted",
            {
                "repository": "memory",
                "count": 0,
            },
        ),
        (
            "cleared",
            {
                "repository": "memory",
                "events_removed": 0,
            },
        ),
    ],
)
def test_all_factories_return_successful_results(factory_name, kwargs):
    factory = getattr(EventRepositoryResult, factory_name)

    result = factory(**kwargs)

    assert isinstance(result, EventRepositoryResult)
    assert result.success is True
    assert result.failed is False


def test_factory_metadata_input_is_not_mutated():
    metadata = {"source": "unit_test"}

    result = EventRepositoryResult.counted(
        repository="memory",
        count=3,
        metadata=metadata,
    )

    assert metadata == {"source": "unit_test"}
    assert result.metadata == {
        "source": "unit_test",
        "count": 3,
    }


def test_module_exports_only_result_contract():
    import shared.events.repositories.event_repository_result as module

    assert module.__all__ == [
        "EventRepositoryResult",
    ]
