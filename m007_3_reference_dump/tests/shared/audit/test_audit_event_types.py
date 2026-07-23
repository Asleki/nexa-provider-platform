"""Tests for shared.audit.audit_event_types."""

from __future__ import annotations

from enum import Enum

import pytest

from shared.audit.audit_event_types import AuditEventType


EXPECTED_VALUES = {
    "RECORDED": "audit.recorded",
    "VALIDATED": "audit.validated",
    "EXPORTED": "audit.exported",
    "ARCHIVED": "audit.archived",
    "PURGED": "audit.purged",
}


def test_audit_event_type_is_string_enum() -> None:
    assert issubclass(AuditEventType, str)
    assert issubclass(AuditEventType, Enum)


@pytest.mark.parametrize(("name", "value"), EXPECTED_VALUES.items())
def test_audit_event_type_members(name: str, value: str) -> None:
    member = AuditEventType[name]

    assert member.value == value
    assert str(member) == value
    assert member == value


def test_audit_event_type_members_are_complete_and_unique() -> None:
    assert {member.name: member.value for member in AuditEventType} == EXPECTED_VALUES
    assert len({member.value for member in AuditEventType}) == len(EXPECTED_VALUES)


def test_public_exports() -> None:
    namespace: dict[str, object] = {}
    exec("from shared.audit.audit_event_types import *", namespace)

    assert namespace["AuditEventType"] is AuditEventType
