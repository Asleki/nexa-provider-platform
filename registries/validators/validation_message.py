"""
============================================================
Nexa Provider Platform
File: registries/validators/validation_message.py
Layer: Registry Validation Foundation
Milestone: NPP-M006.2 — Registry Foundation
============================================================

Purpose
-------
Defines the immutable message structure used by Registry
Foundation validators.

A registry validation message represents one finding discovered
while validating a registry definition, namespace definition,
identifier definition, numbering strategy, identifier reference,
or a future registry-domain object.

Responsibilities
----------------
This module is responsible for:

- defining registry validation severity values;
- defining one immutable registry validation finding;
- normalizing and validating message fields;
- exposing convenient severity helper properties;
- serializing and reconstructing validation messages;
- formatting concise human-readable validation output.

Non-Responsibilities
--------------------
This module does not:

- validate Registry Foundation models directly;
- collect multiple validation findings;
- determine whether a complete validation result is valid;
- raise aggregate validation exceptions;
- write logs or audit records;
- attach timestamps, actors, runtime identities, or correlation IDs;
- persist validation messages.

Those responsibilities belong to later Registry Validation,
Logging, Audit, Service, and Storage components.

Validation Message Flow
-----------------------
Registry Validator
        |
        v
RegistryValidationMessage
        |
        v
RegistryValidationResult
        |
        +-- errors
        +-- warnings
        +-- information
============================================================
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Final


"""
============================================================
SECTION 1 — Validation Message Limits
============================================================

The limits below protect the validation layer from accidental or
unreasonable message values while remaining generous enough for
normal platform diagnostics.
============================================================
"""

MAXIMUM_VALIDATION_CODE_LENGTH: Final[int] = 200

MAXIMUM_VALIDATION_FIELD_LENGTH: Final[int] = 500

MAXIMUM_VALIDATION_MESSAGE_LENGTH: Final[int] = 10_000

MAXIMUM_VALIDATION_SUGGESTION_LENGTH: Final[int] = 10_000


"""
============================================================
SECTION 2 — Validation Severity
============================================================

Every Registry validation finding has one severity.

ERROR
-----
The validated registry object or relationship is invalid.

A complete Registry validation result containing one or more
errors must be treated as invalid.

WARNING
-------
The validated object may be accepted, but the condition should be
reviewed before production use or identifier issuance.

INFORMATION
-----------
The validated object is acceptable, but a noteworthy registry
condition or policy should be reported to operators or calling
services.
============================================================
"""


class ValidationSeverity(str, Enum):
    """
    Severity assigned to one Registry validation message.
    """

    ERROR = "error"

    WARNING = "warning"

    INFORMATION = "information"

    @property
    def label(self) -> str:
        """
        Return a human-readable severity label.
        """

        return {
            ValidationSeverity.ERROR: "Error",
            ValidationSeverity.WARNING: "Warning",
            ValidationSeverity.INFORMATION: "Information",
        }[self]

    @property
    def is_error(self) -> bool:
        """
        Return True when this severity represents an error.
        """

        return self is ValidationSeverity.ERROR

    @property
    def is_warning(self) -> bool:
        """
        Return True when this severity represents a warning.
        """

        return self is ValidationSeverity.WARNING

    @property
    def is_information(self) -> bool:
        """
        Return True when this severity represents information.
        """

        return self is ValidationSeverity.INFORMATION

    @classmethod
    def from_value(
        cls,
        value: str | "ValidationSeverity",
    ) -> "ValidationSeverity":
        """
        Parse a validation severity from text or return an
        existing ValidationSeverity instance.
        """

        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "Validation severity must be text or a "
                "ValidationSeverity instance."
            )

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError(
                "Validation severity cannot be empty."
            )

        try:
            return cls(normalized)
        except ValueError as exc:
            supported = ", ".join(
                severity.value
                for severity in cls
            )

            raise ValueError(
                f"Unsupported validation severity {value!r}. "
                f"Supported severities: {supported}."
            ) from exc

    @classmethod
    def all(cls) -> tuple["ValidationSeverity", ...]:
        """
        Return every supported validation severity.
        """

        return tuple(cls)

    def __str__(self) -> str:
        """
        Return the canonical severity value.
        """

        return self.value


"""
============================================================
SECTION 3 — Registry Validation Message
============================================================

RegistryValidationMessage represents one immutable validation
finding.

Fields
------
severity
    Error, warning, or information.

code
    Stable machine-readable validation code.

field
    Name or path of the Registry field associated with the
    finding.

message
    Human-readable explanation of the finding.

suggestion
    Optional remediation or review guidance.

The object intentionally contains no timestamp, runtime identity,
actor, correlation identity, validator name, or mutable metadata.
Those concerns belong to Logging and Audit records.
============================================================
"""


@dataclass(frozen=True, slots=True)
class RegistryValidationMessage:
    """
    Immutable Registry Foundation validation finding.
    """

    severity: ValidationSeverity

    code: str

    field: str

    message: str

    suggestion: str | None = None

    def __post_init__(self) -> None:
        """
        Normalize and validate message values.
        """

        object.__setattr__(
            self,
            "severity",
            ValidationSeverity.from_value(self.severity),
        )

        normalized_code = self._normalize_required_text(
            value=self.code,
            field_name="code",
            maximum_length=MAXIMUM_VALIDATION_CODE_LENGTH,
        )

        normalized_field = self._normalize_required_text(
            value=self.field,
            field_name="field",
            maximum_length=MAXIMUM_VALIDATION_FIELD_LENGTH,
        )

        normalized_message = self._normalize_required_text(
            value=self.message,
            field_name="message",
            maximum_length=MAXIMUM_VALIDATION_MESSAGE_LENGTH,
        )

        object.__setattr__(
            self,
            "code",
            normalized_code,
        )

        object.__setattr__(
            self,
            "field",
            normalized_field,
        )

        object.__setattr__(
            self,
            "message",
            normalized_message,
        )

        normalized_suggestion = self._normalize_optional_text(
            value=self.suggestion,
            field_name="suggestion",
            maximum_length=MAXIMUM_VALIDATION_SUGGESTION_LENGTH,
        )

        object.__setattr__(
            self,
            "suggestion",
            normalized_suggestion,
        )

    @property
    def is_error(self) -> bool:
        """
        Return True when this message is an error.
        """

        return self.severity.is_error

    @property
    def is_warning(self) -> bool:
        """
        Return True when this message is a warning.
        """

        return self.severity.is_warning

    @property
    def is_information(self) -> bool:
        """
        Return True when this message is informational.
        """

        return self.severity.is_information

    @property
    def has_suggestion(self) -> bool:
        """
        Return True when remediation guidance is present.
        """

        return self.suggestion is not None

    def to_dict(self) -> dict[str, str | None]:
        """
        Serialize this validation message.
        """

        return {
            "severity": self.severity.value,
            "code": self.code,
            "field": self.field,
            "message": self.message,
            "suggestion": self.suggestion,
        }

    @classmethod
    def from_dict(
        cls,
        values: Mapping[str, object],
    ) -> "RegistryValidationMessage":
        """
        Construct a validation message from a mapping.

        Unknown fields are rejected so malformed serialized input
        cannot be silently accepted.
        """

        if not isinstance(values, Mapping):
            raise TypeError(
                "values must be a mapping."
            )

        supported_fields = {
            "severity",
            "code",
            "field",
            "message",
            "suggestion",
        }

        unknown_fields = (
            set(values.keys())
            - supported_fields
        )

        if unknown_fields:
            joined_fields = ", ".join(
                sorted(str(field_name) for field_name in unknown_fields)
            )

            raise ValueError(
                "Unsupported Registry validation message "
                f"field{'s' if len(unknown_fields) != 1 else ''}: "
                f"{joined_fields}."
            )

        required_fields = {
            "severity",
            "code",
            "field",
            "message",
        }

        missing_fields = (
            required_fields
            - set(values.keys())
        )

        if missing_fields:
            joined_fields = ", ".join(
                sorted(missing_fields)
            )

            raise ValueError(
                "Missing required Registry validation message "
                f"field{'s' if len(missing_fields) != 1 else ''}: "
                f"{joined_fields}."
            )

        severity = values["severity"]
        code = values["code"]
        field_name = values["field"]
        message = values["message"]
        suggestion = values.get("suggestion")

        return cls(
            severity=ValidationSeverity.from_value(severity),
            code=cls._require_text_value(
                code,
                field_name="code",
            ),
            field=cls._require_text_value(
                field_name,
                field_name="field",
            ),
            message=cls._require_text_value(
                message,
                field_name="message",
            ),
            suggestion=cls._optional_text_value(
                suggestion,
                field_name="suggestion",
            ),
        )

    def format(self) -> str:
        """
        Return a compact human-readable message.
        """

        formatted = (
            f"[{self.severity.label}] "
            f"{self.code} "
            f"({self.field}): "
            f"{self.message}"
        )

        if self.suggestion is not None:
            formatted = (
                f"{formatted} "
                f"Suggestion: {self.suggestion}"
            )

        return formatted

    @staticmethod
    def _normalize_required_text(
        *,
        value: object,
        field_name: str,
        maximum_length: int,
    ) -> str:
        """
        Validate and normalize one required text value.
        """

        if not isinstance(value, str):
            raise TypeError(
                f"Validation message {field_name} must be text."
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"Validation message {field_name} cannot be empty."
            )

        if len(normalized) > maximum_length:
            raise ValueError(
                f"Validation message {field_name} cannot exceed "
                f"{maximum_length} characters."
            )

        return normalized

    @staticmethod
    def _normalize_optional_text(
        *,
        value: object,
        field_name: str,
        maximum_length: int,
    ) -> str | None:
        """
        Validate and normalize one optional text value.
        """

        if value is None:
            return None

        if not isinstance(value, str):
            raise TypeError(
                f"Validation message {field_name} must be text "
                "or None."
            )

        normalized = value.strip()

        if not normalized:
            return None

        if len(normalized) > maximum_length:
            raise ValueError(
                f"Validation message {field_name} cannot exceed "
                f"{maximum_length} characters."
            )

        return normalized

    @staticmethod
    def _require_text_value(
        value: object,
        *,
        field_name: str,
    ) -> str:
        """
        Confirm a deserialized required value is text.
        """

        if not isinstance(value, str):
            raise TypeError(
                f"Serialized validation message {field_name} "
                "must be text."
            )

        return value

    @staticmethod
    def _optional_text_value(
        value: object,
        *,
        field_name: str,
    ) -> str | None:
        """
        Confirm a deserialized optional value is text or None.
        """

        if value is None:
            return None

        if not isinstance(value, str):
            raise TypeError(
                f"Serialized validation message {field_name} "
                "must be text or None."
            )

        return value


__all__ = [
    "MAXIMUM_VALIDATION_CODE_LENGTH",
    "MAXIMUM_VALIDATION_FIELD_LENGTH",
    "MAXIMUM_VALIDATION_MESSAGE_LENGTH",
    "MAXIMUM_VALIDATION_SUGGESTION_LENGTH",
    "RegistryValidationMessage",
    "ValidationSeverity",
]
