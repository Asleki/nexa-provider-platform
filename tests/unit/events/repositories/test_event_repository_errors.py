from __future__ import annotations

import pytest

from shared.events.repositories.event_repository_errors import *
from shared.events.repositories.event_repository_types import EventRepositoryOperation


def test_error_prefix():
    assert EVENT_REPOSITORY_ERROR_PREFIX == "NPP-EVENT-REPOSITORY"


def test_default_message_falls_back_to_class_name():
    err = EventRepositoryError("   ")
    assert err.message == "EventRepositoryError"


def test_message_trimmed():
    err = EventRepositoryError("  hello  ")
    assert str(err) == "hello"


def test_operation_enum_normalized():
    err = EventRepositoryError("x", operation=EventRepositoryOperation.READ)
    assert err.operation == EventRepositoryOperation.READ.value


def test_operation_string_normalized():
    err = EventRepositoryError("x", operation=" READ ")
    assert err.operation == "READ"


def test_blank_operation_becomes_none():
    err = EventRepositoryError("x", operation=" ")
    assert err.operation is None


def test_optional_fields_trim():
    err = EventRepositoryError("x", repository=" repo ", event_id=" id ", repository_type=" mem ")
    assert err.repository == "repo"
    assert err.event_id == "id"
    assert err.repository_type == "mem"


def test_blank_optional_fields_none():
    err = EventRepositoryError("x", repository=" ", event_id="", repository_type=" ")
    assert err.repository is None
    assert err.event_id is None
    assert err.repository_type is None


def test_cause_and_metadata():
    c = ValueError("bad")
    m = {"a":1}
    err = EventRepositoryError("x", cause=c, metadata=m)
    m["a"]=2
    assert err.cause is c
    assert err.metadata == {"a":1}


def test_to_dict():
    err = EventRepositoryError("x", cause=RuntimeError(), metadata={"k":"v"})
    d = err.to_dict()
    assert d["error"]=="EventRepositoryError"
    assert d["cause"]=="RuntimeError"
    assert d["metadata"]=={"k":"v"}


@pytest.mark.parametrize("cls,parent",[
(EventRepositoryConfigurationError,ValueError),
(EventNotFoundError,LookupError),
(EventDuplicateError,ValueError),
(EventInvalidError,ValueError),
(EventIdentifierError,ValueError),
(EventAlreadyRegisteredError,ValueError),
(EventNotRegisteredError,LookupError),
(EventUnsupportedOperationError,NotImplementedError),
])
def test_specialized_inheritance(cls,parent):
    e=cls("x")
    assert isinstance(e,parent)
    assert isinstance(e,EventRepositoryError)


def test_error_codes_unique():
    classes=[EventRepositoryError,EventRepositoryConfigurationError,EventRepositoryInitializationError,
    EventRepositoryOperationError,EventStoreError,EventReadError,EventDeleteError,EventListError,
    EventExistsError,EventCountError,EventClearError,EventRecordError,EventNotFoundError,
    EventDuplicateError,EventInvalidError,EventIdentifierError,EventRegistrationError,
    EventAlreadyRegisteredError,EventNotRegisteredError,EventFactoryError,
    EventUnsupportedOperationError,EventStorageError,EventDataCorruptionError,EventSchemaError]
    codes=[c.error_code for c in classes]
    assert len(codes)==len(set(codes))


def test_all_exports():
    import shared.events.repositories.event_repository_errors as m
    assert "EventRepositoryError" in m.__all__
    assert "EventSchemaError" in m.__all__
