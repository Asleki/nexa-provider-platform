"""
============================================================
Nexa Provider Platform
File: shared/events/repositories/event_repository_errors.py
Layer: Shared Event Repository
Milestone: NPP-M006.3.4 — Event Repository Errors
============================================================

Defines the exception hierarchy used by the Shared Event
Repository Foundation.
"""

from __future__ import annotations

from typing import Any

from .event_repository_types import EventRepositoryOperation

EVENT_REPOSITORY_ERROR_PREFIX = "NPP-EVENT-REPOSITORY"


def _normalize_operation(
    operation: EventRepositoryOperation | str | None,
) -> str | None:
    if operation is None:
        return None
    if isinstance(operation, EventRepositoryOperation):
        return operation.value
    value = str(operation).strip()
    return value or None


class EventRepositoryError(RuntimeError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-001"

    def __init__(
        self,
        message: str,
        *,
        operation: EventRepositoryOperation | str | None = None,
        repository: str | None = None,
        event_id: str | None = None,
        repository_type: str | None = None,
        cause: BaseException | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        msg = str(message).strip() or self.__class__.__name__
        super().__init__(msg)
        self.message = msg
        self.operation = _normalize_operation(operation)
        self.repository = repository.strip() if isinstance(repository, str) and repository.strip() else None
        self.event_id = event_id.strip() if isinstance(event_id, str) and event_id.strip() else None
        self.repository_type = repository_type.strip() if isinstance(repository_type, str) and repository_type.strip() else None
        self.cause = cause
        self.metadata = dict(metadata or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "operation": self.operation,
            "repository": self.repository,
            "event_id": self.event_id,
            "repository_type": self.repository_type,
            "cause": self.cause.__class__.__name__ if self.cause else None,
            "metadata": dict(self.metadata),
        }


class EventRepositoryConfigurationError(EventRepositoryError, ValueError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-002"


class EventRepositoryInitializationError(EventRepositoryError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-003"


class EventRepositoryOperationError(EventRepositoryError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-010"


class EventStoreError(EventRepositoryOperationError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-011"


class EventReadError(EventRepositoryOperationError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-012"


class EventDeleteError(EventRepositoryOperationError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-013"


class EventListError(EventRepositoryOperationError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-014"


class EventExistsError(EventRepositoryOperationError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-015"


class EventCountError(EventRepositoryOperationError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-016"


class EventClearError(EventRepositoryOperationError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-017"


class EventRecordError(EventRepositoryError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-020"


class EventNotFoundError(EventRecordError, LookupError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-021"


class EventDuplicateError(EventRecordError, ValueError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-022"


class EventInvalidError(EventRecordError, ValueError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-023"


class EventIdentifierError(EventRecordError, ValueError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-024"


class EventRegistrationError(EventRepositoryError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-030"


class EventAlreadyRegisteredError(EventRegistrationError, ValueError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-031"


class EventNotRegisteredError(EventRegistrationError, LookupError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-032"


class EventFactoryError(EventRepositoryError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-040"


class EventUnsupportedOperationError(EventRepositoryOperationError, NotImplementedError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-050"


class EventStorageError(EventRepositoryOperationError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-060"


class EventDataCorruptionError(EventStorageError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-061"


class EventSchemaError(EventStorageError, ValueError):
    error_code = f"{EVENT_REPOSITORY_ERROR_PREFIX}-062"


__all__ = [
    "EVENT_REPOSITORY_ERROR_PREFIX",
    "EventRepositoryError",
    "EventRepositoryConfigurationError",
    "EventRepositoryInitializationError",
    "EventRepositoryOperationError",
    "EventStoreError",
    "EventReadError",
    "EventDeleteError",
    "EventListError",
    "EventExistsError",
    "EventCountError",
    "EventClearError",
    "EventRecordError",
    "EventNotFoundError",
    "EventDuplicateError",
    "EventInvalidError",
    "EventIdentifierError",
    "EventRegistrationError",
    "EventAlreadyRegisteredError",
    "EventNotRegisteredError",
    "EventFactoryError",
    "EventUnsupportedOperationError",
    "EventStorageError",
    "EventDataCorruptionError",
    "EventSchemaError",
]
