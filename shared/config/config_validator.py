"""
============================================================
Nexa Provider Platform
File: shared/config/config_validator.py
Layer: Shared Configuration Foundation
Milestone: NPP-M003 — Configuration Engine
============================================================

Purpose
-------
Validates immutable ConfigurationSchema instances before they
are consumed by other Nexa Provider Platform engines.

The Configuration Validator is responsible for:

- Required-value validation
- Type validation
- Range validation
- Environment-policy validation
- Directory-path validation
- Timezone validation
- Text-encoding validation
- Metadata validation
- Cross-field consistency validation
- Structured error, warning, and information reporting

The validator does not:

- Read environment variables
- Read configuration files
- Merge configuration sources
- Modify ConfigurationSchema instances
- Create platform directories
- Initialize runtime services
- Write logs

Those responsibilities belong to other Configuration Engine
components.

Validation Flow
---------------
ConfigurationSchema
        |
        v
ConfigurationValidator.validate()
        |
        v
ConfigurationValidationResult
        |
        +-- errors
        +-- warnings
        +-- information
        |
        v
ConfigurationValidator.validate_or_raise()
        |
        v
ConfigurationValidationError when invalid
============================================================
"""

from __future__ import annotations

import codecs
import json
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Final
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .config_schema import ConfigurationSchema
from .environment import Environment


"""
============================================================
SECTION 1 — Validation Limits and Patterns
============================================================

This block defines shared limits used throughout configuration
validation.

Centralizing these values prevents individual validation methods
from applying inconsistent rules.

The limits are intentionally conservative. They are large enough
for normal platform use while protecting the configuration layer
from unreasonable or accidental values.
============================================================
"""

MINIMUM_LOG_FILE_SIZE_MB: Final[int] = 1

MAXIMUM_LOG_FILE_SIZE_MB: Final[int] = 10_240

MINIMUM_RETAINED_LOG_FILES: Final[int] = 1

MAXIMUM_RETAINED_LOG_FILES: Final[int] = 10_000

MINIMUM_WORKER_THREADS: Final[int] = 1

MAXIMUM_WORKER_THREADS: Final[int] = 1_024

MAXIMUM_APPLICATION_NAME_LENGTH: Final[int] = 200

MAXIMUM_APPLICATION_VERSION_LENGTH: Final[int] = 100

MAXIMUM_TIMEZONE_LENGTH: Final[int] = 200

MAXIMUM_ENCODING_LENGTH: Final[int] = 100

MAXIMUM_PATH_LENGTH: Final[int] = 4_096

MAXIMUM_METADATA_DEPTH: Final[int] = 20

MAXIMUM_METADATA_ITEMS: Final[int] = 10_000

MAXIMUM_METADATA_KEY_LENGTH: Final[int] = 500

MAXIMUM_METADATA_STRING_LENGTH: Final[int] = 100_000

APPLICATION_VERSION_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[0-9A-Za-z][0-9A-Za-z.+_-]*$"
)

CONTROL_CHARACTER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]"
)


"""
============================================================
SECTION 2 — Validation Severity
============================================================

Every validation finding has one severity.

ERROR
-----
The configuration is invalid.

The platform should not start with unresolved validation errors.

WARNING
-------
The configuration can technically be accepted, but the value
or combination should be reviewed.

INFORMATION
-----------
The configuration is valid, but an environment behavior or
policy is worth reporting to operators.
============================================================
"""


class ValidationSeverity(str, Enum):
    """
    Severity assigned to a configuration validation message.
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


"""
============================================================
SECTION 3 — Validation Message
============================================================

ConfigurationValidationMessage represents one individual
validation finding.

The message is immutable so callers cannot change validation
history after a result has been returned.

Fields
------
severity
    Error, warning, or information.

code
    Stable machine-readable validation code.

field
    Name of the configuration field associated with the finding.

message
    Human-readable explanation.

suggestion
    Optional remediation guidance.
============================================================
"""


@dataclass(frozen=True, slots=True)
class ConfigurationValidationMessage:
    """
    Immutable configuration validation finding.
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
            ValidationSeverity(self.severity),
        )

        if not isinstance(self.code, str):
            raise TypeError(
                "Validation message code must be text."
            )

        if not isinstance(self.field, str):
            raise TypeError(
                "Validation message field must be text."
            )

        if not isinstance(self.message, str):
            raise TypeError(
                "Validation message must be text."
            )

        normalized_code = self.code.strip()

        normalized_field = self.field.strip()

        normalized_message = self.message.strip()

        if not normalized_code:
            raise ValueError(
                "Validation message code cannot be empty."
            )

        if not normalized_field:
            raise ValueError(
                "Validation message field cannot be empty."
            )

        if not normalized_message:
            raise ValueError(
                "Validation message text cannot be empty."
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

        if self.suggestion is not None:
            if not isinstance(self.suggestion, str):
                raise TypeError(
                    "Validation suggestion must be text or None."
                )

            normalized_suggestion = self.suggestion.strip()

            object.__setattr__(
                self,
                "suggestion",
                normalized_suggestion or None,
            )

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

        if self.suggestion:
            formatted = (
                f"{formatted} "
                f"Suggestion: {self.suggestion}"
            )

        return formatted
"""
============================================================
SECTION 4 — Validation Result
============================================================

ConfigurationValidationResult contains every finding discovered
during one validation run.

The result is immutable.

A configuration is considered valid when no ERROR messages are
present. Warnings and informational findings do not make the
configuration invalid.
============================================================
"""


@dataclass(frozen=True, slots=True)
class ConfigurationValidationResult:
    """
    Immutable result produced by ConfigurationValidator.
    """

    messages: tuple[
        ConfigurationValidationMessage,
        ...,
    ] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """
        Normalize messages into an immutable tuple.
        """

        normalized_messages = tuple(self.messages)

        for message in normalized_messages:
            if not isinstance(
                message,
                ConfigurationValidationMessage,
            ):
                raise TypeError(
                    "messages must contain "
                    "ConfigurationValidationMessage instances."
                )

        object.__setattr__(
            self,
            "messages",
            normalized_messages,
        )

    @property
    def errors(
        self,
    ) -> tuple[ConfigurationValidationMessage, ...]:
        """
        Return all validation errors.
        """

        return tuple(
            message
            for message in self.messages
            if message.severity.is_error
        )

    @property
    def warnings(
        self,
    ) -> tuple[ConfigurationValidationMessage, ...]:
        """
        Return all validation warnings.
        """

        return tuple(
            message
            for message in self.messages
            if message.severity.is_warning
        )

    @property
    def information(
        self,
    ) -> tuple[ConfigurationValidationMessage, ...]:
        """
        Return all informational findings.
        """

        return tuple(
            message
            for message in self.messages
            if message.severity.is_information
        )

    @property
    def valid(self) -> bool:
        """
        Return True when no errors were found.
        """

        return not self.errors

    @property
    def invalid(self) -> bool:
        """
        Return True when one or more errors were found.
        """

        return not self.valid

    @property
    def error_count(self) -> int:
        """
        Return the number of validation errors.
        """

        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """
        Return the number of validation warnings.
        """

        return len(self.warnings)

    @property
    def information_count(self) -> int:
        """
        Return the number of informational findings.
        """

        return len(self.information)

    @property
    def message_count(self) -> int:
        """
        Return the total number of validation messages.
        """

        return len(self.messages)

    def has_code(
        self,
        code: str,
    ) -> bool:
        """
        Return True when a message with the supplied code exists.
        """

        if not isinstance(code, str):
            raise TypeError(
                "code must be text."
            )

        normalized_code = code.strip()

        return any(
            message.code == normalized_code
            for message in self.messages
        )

    def for_field(
        self,
        field_name: str,
    ) -> tuple[ConfigurationValidationMessage, ...]:
        """
        Return all messages associated with one field.
        """

        if not isinstance(field_name, str):
            raise TypeError(
                "field_name must be text."
            )

        normalized_field = field_name.strip()

        return tuple(
            message
            for message in self.messages
            if message.field == normalized_field
        )

    def to_dict(self) -> dict[str, object]:
        """
        Serialize the validation result.
        """

        return {
            "valid": self.valid,
            "invalid": self.invalid,
            "message_count": self.message_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "information_count": self.information_count,
            "messages": [
                message.to_dict()
                for message in self.messages
            ],
        }

    def summary(self) -> str:
        """
        Return a human-readable validation summary.
        """

        status = (
            "VALID"
            if self.valid
            else "INVALID"
        )

        lines = [
            "========================================================",
            "Nexa Provider Platform",
            "Configuration Validation Result",
            "--------------------------------------------------------",
            f"Status      : {status}",
            f"Errors      : {self.error_count}",
            f"Warnings    : {self.warning_count}",
            f"Information : {self.information_count}",
        ]

        if self.messages:
            lines.append(
                "--------------------------------------------------------"
            )

            lines.extend(
                message.format()
                for message in self.messages
            )

        lines.append(
            "========================================================"
        )

        return "\n".join(lines)

    def raise_for_errors(self) -> None:
        """
        Raise ConfigurationValidationError when invalid.
        """

        if self.invalid:
            raise ConfigurationValidationError(self)


"""
============================================================
SECTION 5 — Validation Exception
============================================================

ConfigurationValidationError is raised by the fail-fast
validation API.

The complete ConfigurationValidationResult is attached to the
exception so callers can inspect every error and warning instead
of receiving only the first failure.
============================================================
"""


class ConfigurationValidationError(ValueError):
    """
    Raised when configuration validation fails.
    """

    def __init__(
        self,
        result: ConfigurationValidationResult,
    ) -> None:
        if not isinstance(
            result,
            ConfigurationValidationResult,
        ):
            raise TypeError(
                "result must be a "
                "ConfigurationValidationResult."
            )

        self.result = result

        super().__init__(
            result.summary()
        )


"""
============================================================
SECTION 6 — Internal Validation Collector
============================================================

The validation collector is an internal helper used during a
single validation run.

It accumulates mutable messages while validation methods execute
and then returns an immutable ConfigurationValidationResult.

The collector prevents repeated message-construction code inside
every validator method.
============================================================
"""


class _ValidationCollector:
    """
    Internal mutable validation-message collector.
    """

    def __init__(self) -> None:
        self._messages: list[
            ConfigurationValidationMessage
        ] = []

    def add(
        self,
        *,
        severity: ValidationSeverity,
        code: str,
        field: str,
        message: str,
        suggestion: str | None = None,
    ) -> None:
        """
        Add one validation finding.
        """

        self._messages.append(
            ConfigurationValidationMessage(
                severity=severity,
                code=code,
                field=field,
                message=message,
                suggestion=suggestion,
            )
        )

    def error(
        self,
        *,
        code: str,
        field: str,
        message: str,
        suggestion: str | None = None,
    ) -> None:
        """
        Add an error finding.
        """

        self.add(
            severity=ValidationSeverity.ERROR,
            code=code,
            field=field,
            message=message,
            suggestion=suggestion,
        )

    def warning(
        self,
        *,
        code: str,
        field: str,
        message: str,
        suggestion: str | None = None,
    ) -> None:
        """
        Add a warning finding.
        """

        self.add(
            severity=ValidationSeverity.WARNING,
            code=code,
            field=field,
            message=message,
            suggestion=suggestion,
        )

    def information(
        self,
        *,
        code: str,
        field: str,
        message: str,
        suggestion: str | None = None,
    ) -> None:
        """
        Add an informational finding.
        """

        self.add(
            severity=ValidationSeverity.INFORMATION,
            code=code,
            field=field,
            message=message,
            suggestion=suggestion,
        )

    def result(
        self,
    ) -> ConfigurationValidationResult:
        """
        Return the immutable validation result.
        """

        return ConfigurationValidationResult(
            messages=tuple(self._messages)
        )
"""
============================================================
SECTION 7 — Configuration Validator Public API
============================================================

ConfigurationValidator coordinates the complete validation
pipeline.

The validator is stateless between calls. A single shared
instance can therefore be reused by ConfigLoader and other
platform modules.

Public Methods
--------------
validate()
    Returns a structured result without raising for validation
    failures.

validate_or_raise()
    Returns a valid result or raises ConfigurationValidationError.

is_valid()
    Returns a simple Boolean result.

errors()
    Returns only validation errors.
============================================================
"""


class ConfigurationValidator:
    """
    Validates ConfigurationSchema instances.
    """

    def validate(
        self,
        configuration: ConfigurationSchema,
    ) -> ConfigurationValidationResult:
        """
        Validate configuration and return all findings.

        Validation failures are returned inside the result.

        Type misuse still raises TypeError because passing a
        non-ConfigurationSchema object is a programming error,
        not a configuration finding.
        """

        if not isinstance(
            configuration,
            ConfigurationSchema,
        ):
            raise TypeError(
                "configuration must be a ConfigurationSchema."
            )

        collector = _ValidationCollector()

        self._validate_application_identity(
            configuration,
            collector,
        )

        self._validate_environment(
            configuration,
            collector,
        )

        self._validate_boolean_fields(
            configuration,
            collector,
        )

        self._validate_directories(
            configuration,
            collector,
        )

        self._validate_timezone(
            configuration,
            collector,
        )

        self._validate_encoding(
            configuration,
            collector,
        )

        self._validate_integer_fields(
            configuration,
            collector,
        )

        self._validate_metadata(
            configuration,
            collector,
        )

        self._validate_cross_field_rules(
            configuration,
            collector,
        )

        return collector.result()

    def validate_or_raise(
        self,
        configuration: ConfigurationSchema,
    ) -> ConfigurationValidationResult:
        """
        Validate configuration and raise when invalid.
        """

        result = self.validate(configuration)

        result.raise_for_errors()

        return result

    def is_valid(
        self,
        configuration: ConfigurationSchema,
    ) -> bool:
        """
        Return True when configuration is valid.
        """

        return self.validate(configuration).valid

    def errors(
        self,
        configuration: ConfigurationSchema,
    ) -> tuple[ConfigurationValidationMessage, ...]:
        """
        Return only configuration validation errors.
        """

        return self.validate(configuration).errors
    """
============================================================
SECTION 8 — Application Identity Validation
============================================================

This block validates:

- application_name
- application_version

These values identify the application in logs, runtime reports,
configuration summaries, audit records, and future provider
registries.

They must therefore be present, printable, and reasonably sized.
============================================================
    """

    def _validate_application_identity(
        self,
        configuration: ConfigurationSchema,
        collector: _ValidationCollector,
    ) -> None:
        """
        Validate application identity fields.
        """

        self._validate_application_name(
            configuration.application_name,
            collector,
        )

        self._validate_application_version(
            configuration.application_version,
            collector,
        )

    def _validate_application_name(
        self,
        value: object,
        collector: _ValidationCollector,
    ) -> None:
        """
        Validate application_name.
        """

        field_name = "application_name"

        if not isinstance(value, str):
            collector.error(
                code="CFG-APP-001",
                field=field_name,
                message=(
                    "Application name must be text."
                ),
            )

            return

        normalized = value.strip()

        if not normalized:
            collector.error(
                code="CFG-APP-002",
                field=field_name,
                message=(
                    "Application name cannot be empty."
                ),
                suggestion=(
                    "Set application_name to a stable platform "
                    "or service name."
                ),
            )

            return

        if len(normalized) > MAXIMUM_APPLICATION_NAME_LENGTH:
            collector.error(
                code="CFG-APP-003",
                field=field_name,
                message=(
                    "Application name exceeds the maximum "
                    f"length of "
                    f"{MAXIMUM_APPLICATION_NAME_LENGTH} "
                    "characters."
                ),
            )

        if CONTROL_CHARACTER_PATTERN.search(normalized):
            collector.error(
                code="CFG-APP-004",
                field=field_name,
                message=(
                    "Application name contains unsupported "
                    "control characters."
                ),
            )

        if normalized != value:
            collector.warning(
                code="CFG-APP-005",
                field=field_name,
                message=(
                    "Application name contains leading or "
                    "trailing whitespace."
                ),
                suggestion=(
                    "Store the normalized application name "
                    "without surrounding whitespace."
                ),
            )

    def _validate_application_version(
        self,
        value: object,
        collector: _ValidationCollector,
    ) -> None:
        """
        Validate application_version.
        """

        field_name = "application_version"

        if not isinstance(value, str):
            collector.error(
                code="CFG-APP-010",
                field=field_name,
                message=(
                    "Application version must be text."
                ),
            )

            return

        normalized = value.strip()

        if not normalized:
            collector.error(
                code="CFG-APP-011",
                field=field_name,
                message=(
                    "Application version cannot be empty."
                ),
            )

            return

        if len(normalized) > MAXIMUM_APPLICATION_VERSION_LENGTH:
            collector.error(
                code="CFG-APP-012",
                field=field_name,
                message=(
                    "Application version exceeds the maximum "
                    f"length of "
                    f"{MAXIMUM_APPLICATION_VERSION_LENGTH} "
                    "characters."
                ),
            )

        if not APPLICATION_VERSION_PATTERN.fullmatch(normalized):
            collector.error(
                code="CFG-APP-013",
                field=field_name,
                message=(
                    "Application version contains unsupported "
                    "characters."
                ),
                suggestion=(
                    "Use letters, numbers, periods, hyphens, "
                    "underscores, or plus signs."
                ),
            )

        if normalized != value:
            collector.warning(
                code="CFG-APP-014",
                field=field_name,
                message=(
                    "Application version contains leading or "
                    "trailing whitespace."
                ),
            )
    """
============================================================
SECTION 9 — Environment Validation
============================================================

The environment field controls important platform policy.

Supported values are defined exclusively by Environment:

- development
- testing
- staging
- production

ConfigurationSchema normally normalizes this field during object
construction. The validator still verifies the final type so
manually constructed or modified objects cannot bypass policy.
============================================================
    """

    def _validate_environment(
        self,
        configuration: ConfigurationSchema,
        collector: _ValidationCollector,
    ) -> None:
        """
        Validate the configured deployment environment.
        """

        environment = configuration.environment

        if not isinstance(environment, Environment):
            collector.error(
                code="CFG-ENV-001",
                field="environment",
                message=(
                    "Environment must be an Environment value."
                ),
                suggestion=(
                    "Use Environment.DEVELOPMENT, "
                    "Environment.TESTING, "
                    "Environment.STAGING, or "
                    "Environment.PRODUCTION."
                ),
            )

            return

        collector.information(
            code="CFG-ENV-002",
            field="environment",
            message=(
                f"Configuration targets the "
                f"{environment.label} environment."
            ),
        )
    """
============================================================
SECTION 10 — Boolean Field Validation
============================================================

Configuration booleans control operational behavior.

Python integers are not accepted as booleans here, even though
bool is a subclass of int. The final schema must contain actual
Boolean values.

Validated fields:

- debug
- audit_enabled
- strict_validation
- simulation_enabled
============================================================
    """

    def _validate_boolean_fields(
        self,
        configuration: ConfigurationSchema,
        collector: _ValidationCollector,
    ) -> None:
        """
        Validate all Boolean configuration fields.
        """

        boolean_fields = {
            "debug": configuration.debug,
            "audit_enabled": configuration.audit_enabled,
            "strict_validation": (
                configuration.strict_validation
            ),
            "simulation_enabled": (
                configuration.simulation_enabled
            ),
        }

        for field_name, value in boolean_fields.items():
            if not isinstance(value, bool):
                collector.error(
                    code="CFG-BOOL-001",
                    field=field_name,
                    message=(
                        f"{field_name} must be a Boolean value."
                    ),
                )
    """
============================================================
SECTION 11 — Directory Validation
============================================================

The Configuration Validator validates path structure and basic
filesystem safety.

It does not create directories. Directory creation belongs to
the runtime or storage initialization layer.

Validation includes:

- Path type
- Non-empty path
- Null-byte protection
- Excessive path length
- Existing target type
- Parent-path accessibility
- Relative-path visibility
- Directory duplication
- Nested-directory warnings

A missing directory is not automatically an error because the
platform may create it during controlled initialization.
============================================================
    """

    def _validate_directories(
        self,
        configuration: ConfigurationSchema,
        collector: _ValidationCollector,
    ) -> None:
        """
        Validate all managed platform directories.
        """

        directory_fields = {
            "storage_directory": (
                configuration.storage_directory
            ),
            "log_directory": (
                configuration.log_directory
            ),
            "data_directory": (
                configuration.data_directory
            ),
            "configuration_directory": (
                configuration.configuration_directory
            ),
            "temporary_directory": (
                configuration.temporary_directory
            ),
        }

        normalized_paths: dict[str, Path] = {}

        for field_name, value in directory_fields.items():
            normalized = self._validate_directory(
                field_name=field_name,
                value=value,
                collector=collector,
            )

            if normalized is not None:
                normalized_paths[field_name] = normalized

        self._validate_duplicate_directories(
            normalized_paths,
            collector,
        )

        self._validate_nested_directories(
            normalized_paths,
            collector,
        )

    def _validate_directory(
        self,
        *,
        field_name: str,
        value: object,
        collector: _ValidationCollector,
    ) -> Path | None:
        """
        Validate one configured directory path.
        """

        if not isinstance(value, Path):
            collector.error(
                code="CFG-PATH-001",
                field=field_name,
                message=(
                    f"{field_name} must be a pathlib.Path."
                ),
            )

            return None

        path_text = str(value)

        if not path_text.strip():
            collector.error(
                code="CFG-PATH-002",
                field=field_name,
                message=(
                    f"{field_name} cannot be empty."
                ),
            )

            return None

        if "\x00" in path_text:
            collector.error(
                code="CFG-PATH-003",
                field=field_name,
                message=(
                    f"{field_name} contains a null byte."
                ),
            )

            return None

        if len(path_text) > MAXIMUM_PATH_LENGTH:
            collector.error(
                code="CFG-PATH-004",
                field=field_name,
                message=(
                    f"{field_name} exceeds the supported "
                    f"path length of {MAXIMUM_PATH_LENGTH} "
                    "characters."
                ),
            )

        expanded = value.expanduser()

        try:
            normalized = expanded.resolve(
                strict=False
            )
        except OSError as exc:
            collector.error(
                code="CFG-PATH-005",
                field=field_name,
                message=(
                    f"{field_name} cannot be normalized: "
                    f"{exc}."
                ),
            )

            return None

        if expanded.exists():
            if not expanded.is_dir():
                collector.error(
                    code="CFG-PATH-006",
                    field=field_name,
                    message=(
                        f"{field_name} points to an existing "
                        "filesystem object that is not a "
                        "directory."
                    ),
                )

                return normalized

            if not os.access(expanded, os.R_OK):
                collector.warning(
                    code="CFG-PATH-007",
                    field=field_name,
                    message=(
                        f"{field_name} may not be readable by "
                        "the current process."
                    ),
                )

            if not os.access(expanded, os.W_OK):
                collector.warning(
                    code="CFG-PATH-008",
                    field=field_name,
                    message=(
                        f"{field_name} may not be writable by "
                        "the current process."
                    ),
                )
        else:
            collector.information(
                code="CFG-PATH-009",
                field=field_name,
                message=(
                    f"{field_name} does not currently exist "
                    "and may need to be created during "
                    "platform initialization."
                ),
            )

            parent = expanded.parent

            if parent.exists() and not parent.is_dir():
                collector.error(
                    code="CFG-PATH-010",
                    field=field_name,
                    message=(
                        f"The parent of {field_name} exists "
                        "but is not a directory."
                    ),
                )

            elif parent.exists() and not os.access(
                parent,
                os.W_OK,
            ):
                collector.warning(
                    code="CFG-PATH-011",
                    field=field_name,
                    message=(
                        f"The parent directory of {field_name} "
                        "may not be writable."
                    ),
                )

        if not value.is_absolute():
            collector.information(
                code="CFG-PATH-012",
                field=field_name,
                message=(
                    f"{field_name} uses a relative path and "
                    "will be resolved from the current working "
                    "directory."
                ),
            )

        return normalized

    def _validate_duplicate_directories(
        self,
        paths: Mapping[str, Path],
        collector: _ValidationCollector,
    ) -> None:
        """
        Detect directory fields that resolve to the same path.
        """

        by_path: dict[Path, list[str]] = {}

        for field_name, path in paths.items():
            by_path.setdefault(
                path,
                [],
            ).append(field_name)

        for path, field_names in by_path.items():
            if len(field_names) < 2:
                continue

            joined_fields = ", ".join(
                sorted(field_names)
            )

            collector.warning(
                code="CFG-PATH-020",
                field="directories",
                message=(
                    "Multiple configuration directory fields "
                    f"resolve to the same path {path}: "
                    f"{joined_fields}."
                ),
                suggestion=(
                    "Use separate directories unless shared "
                    "storage is intentional."
                ),
            )

    def _validate_nested_directories(
        self,
        paths: Mapping[str, Path],
        collector: _ValidationCollector,
    ) -> None:
        """
        Report sensitive directory nesting relationships.
        """

        configuration_path = paths.get(
            "configuration_directory"
        )

        temporary_path = paths.get(
            "temporary_directory"
        )

        storage_path = paths.get(
            "storage_directory"
        )

        if (
            configuration_path is not None
            and temporary_path is not None
            and self._is_path_within(
                configuration_path,
                temporary_path,
            )
        ):
            collector.warning(
                code="CFG-PATH-021",
                field="configuration_directory",
                message=(
                    "The configuration directory is located "
                    "inside the temporary directory."
                ),
                suggestion=(
                    "Store persistent configuration outside "
                    "temporary storage."
                ),
            )

        if (
            storage_path is not None
            and temporary_path is not None
            and self._is_path_within(
                storage_path,
                temporary_path,
            )
        ):
            collector.warning(
                code="CFG-PATH-022",
                field="storage_directory",
                message=(
                    "The storage directory is located inside "
                    "the temporary directory."
                ),
                suggestion=(
                    "Use persistent storage for platform "
                    "records."
                ),
            )

    @staticmethod
    def _is_path_within(
        child: Path,
        parent: Path,
    ) -> bool:
        """
        Return True when child is inside parent.
        """

        if child == parent:
            return False

        try:
            child.relative_to(parent)
        except ValueError:
            return False

        return True
    """
============================================================
SECTION 12 — Timezone Validation
============================================================

Timezone names are validated with Python's zoneinfo database.

Examples of valid timezone values:

- UTC
- Africa/Nairobi
- Africa/Harare
- Europe/London

The validator reports a clear error when the configured timezone
cannot be resolved.
============================================================
    """

    def _validate_timezone(
        self,
        configuration: ConfigurationSchema,
        collector: _ValidationCollector,
    ) -> None:
        """
        Validate the configured timezone.
        """

        field_name = "timezone"

        value = configuration.timezone

        if not isinstance(value, str):
            collector.error(
                code="CFG-TIME-001",
                field=field_name,
                message=(
                    "Timezone must be text."
                ),
            )

            return

        normalized = value.strip()

        if not normalized:
            collector.error(
                code="CFG-TIME-002",
                field=field_name,
                message=(
                    "Timezone cannot be empty."
                ),
            )

            return

        if len(normalized) > MAXIMUM_TIMEZONE_LENGTH:
            collector.error(
                code="CFG-TIME-003",
                field=field_name,
                message=(
                    "Timezone exceeds the maximum supported "
                    f"length of {MAXIMUM_TIMEZONE_LENGTH} "
                    "characters."
                ),
            )

            return

        try:
            ZoneInfo(normalized)
        except ZoneInfoNotFoundError:
            collector.error(
                code="CFG-TIME-004",
                field=field_name,
                message=(
                    f"Unknown timezone {normalized!r}."
                ),
                suggestion=(
                    "Use a valid IANA timezone such as UTC, "
                    "Africa/Nairobi, or Africa/Harare."
                ),
            )
        except (ValueError, OSError) as exc:
            collector.error(
                code="CFG-TIME-005",
                field=field_name,
                message=(
                    f"Timezone could not be loaded: {exc}."
                ),
            )

        if normalized != value:
            collector.warning(
                code="CFG-TIME-006",
                field=field_name,
                message=(
                    "Timezone contains leading or trailing "
                    "whitespace."
                ),
            )
    """
============================================================
SECTION 13 — Text Encoding Validation
============================================================

The configured encoding is validated using Python's codec
registry.

The encoding must:

- Be text
- Be non-empty
- Resolve to a registered codec
- Support ordinary text encoding and decoding

UTF-8 is recommended for platform interoperability.
============================================================
    """

    def _validate_encoding(
        self,
        configuration: ConfigurationSchema,
        collector: _ValidationCollector,
    ) -> None:
        """
        Validate the configured text encoding.
        """

        field_name = "encoding"

        value = configuration.encoding

        if not isinstance(value, str):
            collector.error(
                code="CFG-ENC-001",
                field=field_name,
                message=(
                    "Encoding must be text."
                ),
            )

            return

        normalized = value.strip()

        if not normalized:
            collector.error(
                code="CFG-ENC-002",
                field=field_name,
                message=(
                    "Encoding cannot be empty."
                ),
            )

            return

        if len(normalized) > MAXIMUM_ENCODING_LENGTH:
            collector.error(
                code="CFG-ENC-003",
                field=field_name,
                message=(
                    "Encoding exceeds the maximum supported "
                    f"length of {MAXIMUM_ENCODING_LENGTH} "
                    "characters."
                ),
            )

            return

        try:
            codec_info = codecs.lookup(normalized)
        except LookupError:
            collector.error(
                code="CFG-ENC-004",
                field=field_name,
                message=(
                    f"Unknown text encoding {normalized!r}."
                ),
                suggestion=(
                    "Use a registered Python text codec such "
                    "as utf-8."
                ),
            )

            return

        try:
            sample = "Nexa Provider Platform"

            encoded = sample.encode(
                codec_info.name
            )

            decoded = encoded.decode(
                codec_info.name
            )
        except (LookupError, UnicodeError) as exc:
            collector.error(
                code="CFG-ENC-005",
                field=field_name,
                message=(
                    "The configured encoding cannot safely "
                    f"encode and decode platform text: {exc}."
                ),
            )

            return

        if decoded != sample:
            collector.error(
                code="CFG-ENC-006",
                field=field_name,
                message=(
                    "The configured codec did not preserve "
                    "platform text during an encode/decode "
                    "round trip."
                ),
            )

        if codec_info.name not in {
            "utf-8",
            "utf-8-sig",
        }:
            collector.warning(
                code="CFG-ENC-007",
                field=field_name,
                message=(
                    f"Encoding resolves to "
                    f"{codec_info.name!r} instead of UTF-8."
                ),
                suggestion=(
                    "Use utf-8 unless another encoding is "
                    "required by a controlled integration."
                ),
            )
    """
============================================================
SECTION 14 — Integer Field Validation
============================================================

This block validates operational integer limits.

maximum_log_file_size_mb
    Maximum size of one log file before rotation.

retained_log_files
    Number of rotated log files retained.

maximum_worker_threads
    Maximum worker-thread count available to platform services.

Boolean values are explicitly rejected because Python treats
Boolean values as integer subclasses.
============================================================
    """

    def _validate_integer_fields(
        self,
        configuration: ConfigurationSchema,
        collector: _ValidationCollector,
    ) -> None:
        """
        Validate all integer configuration fields.
        """

        self._validate_integer_range(
            field_name="maximum_log_file_size_mb",
            value=configuration.maximum_log_file_size_mb,
            minimum=MINIMUM_LOG_FILE_SIZE_MB,
            maximum=MAXIMUM_LOG_FILE_SIZE_MB,
            collector=collector,
            code_prefix="CFG-INT-LOG-SIZE",
        )

        self._validate_integer_range(
            field_name="retained_log_files",
            value=configuration.retained_log_files,
            minimum=MINIMUM_RETAINED_LOG_FILES,
            maximum=MAXIMUM_RETAINED_LOG_FILES,
            collector=collector,
            code_prefix="CFG-INT-LOG-RETAIN",
        )

        self._validate_integer_range(
            field_name="maximum_worker_threads",
            value=configuration.maximum_worker_threads,
            minimum=MINIMUM_WORKER_THREADS,
            maximum=MAXIMUM_WORKER_THREADS,
            collector=collector,
            code_prefix="CFG-INT-WORKERS",
        )

        if (
            isinstance(
                configuration.maximum_worker_threads,
                int,
            )
            and not isinstance(
                configuration.maximum_worker_threads,
                bool,
            )
        ):
            cpu_count = os.cpu_count()

            if (
                cpu_count is not None
                and configuration.maximum_worker_threads
                > cpu_count * 8
            ):
                collector.warning(
                    code="CFG-INT-WORKERS-004",
                    field="maximum_worker_threads",
                    message=(
                        "Maximum worker threads is much larger "
                        "than the detected processor count."
                    ),
                    suggestion=(
                        "Review the worker limit to avoid "
                        "unnecessary scheduling overhead."
                    ),
                )

    def _validate_integer_range(
        self,
        *,
        field_name: str,
        value: object,
        minimum: int,
        maximum: int,
        collector: _ValidationCollector,
        code_prefix: str,
    ) -> None:
        """
        Validate one integer against an inclusive range.
        """

        if isinstance(value, bool) or not isinstance(value, int):
            collector.error(
                code=f"{code_prefix}-001",
                field=field_name,
                message=(
                    f"{field_name} must be an integer."
                ),
            )

            return

        if value < minimum:
            collector.error(
                code=f"{code_prefix}-002",
                field=field_name,
                message=(
                    f"{field_name} must be at least "
                    f"{minimum}."
                ),
            )

        if value > maximum:
            collector.error(
                code=f"{code_prefix}-003",
                field=field_name,
                message=(
                    f"{field_name} cannot exceed "
                    f"{maximum}."
                ),
            )
    """
============================================================
SECTION 15 — Metadata Validation
============================================================

Metadata provides optional platform-specific configuration
extensions.

Because metadata may later be persisted, logged, synchronized,
or transmitted through APIs, it must remain JSON-compatible.

Supported metadata values:

- None
- Boolean
- Integer
- Float
- String
- Lists
- Tuples
- Dictionaries with string keys

Unsupported examples:

- Sets
- Path objects
- Functions
- Open files
- Arbitrary class instances
- Circular data structures

The validator also protects against excessive depth and size.
============================================================
    """

    def _validate_metadata(
        self,
        configuration: ConfigurationSchema,
        collector: _ValidationCollector,
    ) -> None:
        """
        Validate metadata structure and serializability.
        """

        metadata = configuration.metadata

        if not isinstance(metadata, Mapping):
            collector.error(
                code="CFG-META-001",
                field="metadata",
                message=(
                    "Metadata must be a mapping."
                ),
            )

            return

        total_items = self._count_metadata_items(
            metadata,
            seen=set(),
        )

        if total_items > MAXIMUM_METADATA_ITEMS:
            collector.error(
                code="CFG-META-002",
                field="metadata",
                message=(
                    "Metadata contains too many values. "
                    f"Maximum supported items: "
                    f"{MAXIMUM_METADATA_ITEMS}."
                ),
            )

        self._validate_metadata_value(
            value=metadata,
            path="metadata",
            depth=0,
            seen=set(),
            collector=collector,
        )

        try:
            json.dumps(
                metadata,
                ensure_ascii=False,
                allow_nan=False,
            )
        except (
            TypeError,
            ValueError,
            OverflowError,
            RecursionError,
        ) as exc:
            collector.error(
                code="CFG-META-003",
                field="metadata",
                message=(
                    "Metadata is not safely JSON-serializable: "
                    f"{exc}."
                ),
            )

    def _validate_metadata_value(
        self,
        *,
        value: object,
        path: str,
        depth: int,
        seen: set[int],
        collector: _ValidationCollector,
    ) -> None:
        """
        Recursively validate one metadata value.
        """

        if depth > MAXIMUM_METADATA_DEPTH:
            collector.error(
                code="CFG-META-010",
                field=path,
                message=(
                    "Metadata exceeds the maximum nesting "
                    f"depth of {MAXIMUM_METADATA_DEPTH}."
                ),
            )

            return

        if value is None:
            return

        if isinstance(value, bool):
            return

        if isinstance(value, int):
            return

        if isinstance(value, float):
            if value != value:
                collector.error(
                    code="CFG-META-011",
                    field=path,
                    message=(
                        "Metadata cannot contain NaN."
                    ),
                )

            if value in {
                float("inf"),
                float("-inf"),
            }:
                collector.error(
                    code="CFG-META-012",
                    field=path,
                    message=(
                        "Metadata cannot contain infinite "
                        "floating-point values."
                    ),
                )

            return

        if isinstance(value, str):
            if len(value) > MAXIMUM_METADATA_STRING_LENGTH:
                collector.error(
                    code="CFG-META-013",
                    field=path,
                    message=(
                        "Metadata string exceeds the maximum "
                        f"length of "
                        f"{MAXIMUM_METADATA_STRING_LENGTH} "
                        "characters."
                    ),
                )

            if "\x00" in value:
                collector.error(
                    code="CFG-META-014",
                    field=path,
                    message=(
                        "Metadata string contains a null byte."
                    ),
                )

            return

        if isinstance(value, Mapping):
            object_id = id(value)

            if object_id in seen:
                collector.error(
                    code="CFG-META-015",
                    field=path,
                    message=(
                        "Metadata contains a circular mapping."
                    ),
                )

                return

            seen.add(object_id)

            for key, nested_value in value.items():
                if not isinstance(key, str):
                    collector.error(
                        code="CFG-META-016",
                        field=path,
                        message=(
                            "Metadata dictionary keys must "
                            "be text."
                        ),
                    )

                    key_text = repr(key)
                else:
                    key_text = key

                    if not key.strip():
                        collector.warning(
                            code="CFG-META-017",
                            field=path,
                            message=(
                                "Metadata contains an empty "
                                "dictionary key."
                            ),
                        )

                    if (
                        len(key)
                        > MAXIMUM_METADATA_KEY_LENGTH
                    ):
                        collector.error(
                            code="CFG-META-018",
                            field=path,
                            message=(
                                "Metadata key exceeds the "
                                "maximum length of "
                                f"{MAXIMUM_METADATA_KEY_LENGTH} "
                                "characters."
                            ),
                        )

                    if "\x00" in key:
                        collector.error(
                            code="CFG-META-019",
                            field=path,
                            message=(
                                "Metadata key contains a "
                                "null byte."
                            ),
                        )

                nested_path = (
                    f"{path}.{key_text}"
                )

                self._validate_metadata_value(
                    value=nested_value,
                    path=nested_path,
                    depth=depth + 1,
                    seen=seen,
                    collector=collector,
                )

            seen.remove(object_id)

            return

        if (
            isinstance(value, Sequence)
            and not isinstance(
                value,
                (
                    str,
                    bytes,
                    bytearray,
                ),
            )
        ):
            object_id = id(value)

            if object_id in seen:
                collector.error(
                    code="CFG-META-020",
                    field=path,
                    message=(
                        "Metadata contains a circular sequence."
                    ),
                )

                return

            seen.add(object_id)

            for index, nested_value in enumerate(value):
                self._validate_metadata_value(
                    value=nested_value,
                    path=f"{path}[{index}]",
                    depth=depth + 1,
                    seen=seen,
                    collector=collector,
                )

            seen.remove(object_id)

            return

        collector.error(
            code="CFG-META-021",
            field=path,
            message=(
                "Metadata contains an unsupported value type: "
                f"{type(value).__name__}."
            ),
            suggestion=(
                "Use JSON-compatible metadata values."
            ),
        )

    def _count_metadata_items(
        self,
        value: object,
        *,
        seen: set[int],
    ) -> int:
        """
        Count nested metadata values safely.
        """

        if isinstance(value, Mapping):
            object_id = id(value)

            if object_id in seen:
                return 0

            seen.add(object_id)

            total = len(value)

            for nested_value in value.values():
                total += self._count_metadata_items(
                    nested_value,
                    seen=seen,
                )

            seen.remove(object_id)

            return total

        if (
            isinstance(value, Sequence)
            and not isinstance(
                value,
                (
                    str,
                    bytes,
                    bytearray,
                ),
            )
        ):
            object_id = id(value)

            if object_id in seen:
                return 0

            seen.add(object_id)

            total = len(value)

            for nested_value in value:
                total += self._count_metadata_items(
                    nested_value,
                    seen=seen,
                )

            seen.remove(object_id)

            return total

        return 1
    """
============================================================
SECTION 16 — Cross-Field Policy Validation
============================================================

Cross-field rules validate combinations that may be individually
valid but unsafe when used together.

Environment policy is defined by Environment properties.

Production Rules
----------------
- Debugging must be disabled.
- Simulation must be disabled.
- Strict validation must be enabled.
- Audit logging must be enabled.

Staging Rules
-------------
- Strict validation must be enabled.
- Audit logging should be enabled.
- Debugging should normally be disabled.

Testing Rules
-------------
- Simulation is allowed.
- Debugging is allowed.
- Disabled audit logging produces a warning.

Development Rules
-----------------
- Debugging is allowed.
- Simulation is allowed.
- Strict validation is optional.
============================================================
    """

    def _validate_cross_field_rules(
        self,
        configuration: ConfigurationSchema,
        collector: _ValidationCollector,
    ) -> None:
        """
        Validate environment-specific and cross-field rules.
        """

        environment = configuration.environment

        if not isinstance(environment, Environment):
            return

        self._validate_debug_policy(
            configuration,
            collector,
        )

        self._validate_simulation_policy(
            configuration,
            collector,
        )

        self._validate_strict_validation_policy(
            configuration,
            collector,
        )

        self._validate_audit_policy(
            configuration,
            collector,
        )

        self._validate_storage_policy(
            configuration,
            collector,
        )

    def _validate_debug_policy(
        self,
        configuration: ConfigurationSchema,
        collector: _ValidationCollector,
    ) -> None:
        """
        Validate debug-mode environment policy.
        """

        if not isinstance(configuration.debug, bool):
            return

        environment = configuration.environment

        if (
            configuration.debug
            and not environment.allows_debugging
        ):
            if environment.is_production:
                collector.error(
                    code="CFG-POLICY-DEBUG-001",
                    field="debug",
                    message=(
                        "Debug mode cannot be enabled in "
                        "Production."
                    ),
                    suggestion=(
                        "Set debug to False before starting "
                        "the production platform."
                    ),
                )
            else:
                collector.warning(
                    code="CFG-POLICY-DEBUG-002",
                    field="debug",
                    message=(
                        f"Debug mode is enabled in the "
                        f"{environment.label} environment."
                    ),
                    suggestion=(
                        "Disable debug mode unless verbose "
                        "diagnostics are explicitly required."
                    ),
                )

    def _validate_simulation_policy(
        self,
        configuration: ConfigurationSchema,
        collector: _ValidationCollector,
    ) -> None:
        """
        Validate simulation-mode environment policy.
        """

        if not isinstance(
            configuration.simulation_enabled,
            bool,
        ):
            return

        environment = configuration.environment

        if (
            configuration.simulation_enabled
            and not environment.allows_simulation
        ):
            collector.error(
                code="CFG-POLICY-SIM-001",
                field="simulation_enabled",
                message=(
                    "Simulation mode cannot be enabled in "
                    "Production."
                ),
                suggestion=(
                    "Set simulation_enabled to False before "
                    "starting the production platform."
                ),
            )

        elif configuration.simulation_enabled:
            collector.information(
                code="CFG-POLICY-SIM-002",
                field="simulation_enabled",
                message=(
                    "Simulation mode is enabled. Simulation "
                    "events must remain isolated from live "
                    "production records."
                ),
            )

    def _validate_strict_validation_policy(
        self,
        configuration: ConfigurationSchema,
        collector: _ValidationCollector,
    ) -> None:
        """
        Validate strict-validation environment policy.
        """

        if not isinstance(
            configuration.strict_validation,
            bool,
        ):
            return

        environment = configuration.environment

        if (
            environment.requires_strict_validation
            and not configuration.strict_validation
        ):
            collector.error(
                code="CFG-POLICY-STRICT-001",
                field="strict_validation",
                message=(
                    "Strict validation is required in the "
                    f"{environment.label} environment."
                ),
                suggestion=(
                    "Set strict_validation to True."
                ),
            )

        elif configuration.strict_validation:
            collector.information(
                code="CFG-POLICY-STRICT-002",
                field="strict_validation",
                message=(
                    "Strict configuration validation is "
                    "enabled."
                ),
            )

    def _validate_audit_policy(
        self,
        configuration: ConfigurationSchema,
        collector: _ValidationCollector,
    ) -> None:
        """
        Validate audit environment policy.
        """

        if not isinstance(
            configuration.audit_enabled,
            bool,
        ):
            return

        environment = configuration.environment

        if (
            environment.is_production
            and not configuration.audit_enabled
        ):
            collector.error(
                code="CFG-POLICY-AUDIT-001",
                field="audit_enabled",
                message=(
                    "Audit logging must be enabled in "
                    "Production."
                ),
                suggestion=(
                    "Set audit_enabled to True."
                ),
            )

        elif (
            environment.is_staging
            and not configuration.audit_enabled
        ):
            collector.warning(
                code="CFG-POLICY-AUDIT-002",
                field="audit_enabled",
                message=(
                    "Audit logging is disabled in Staging."
                ),
                suggestion=(
                    "Enable audit logging so Staging behavior "
                    "matches Production."
                ),
            )

        elif (
            environment.is_testing
            and not configuration.audit_enabled
        ):
            collector.warning(
                code="CFG-POLICY-AUDIT-003",
                field="audit_enabled",
                message=(
                    "Audit logging is disabled in Testing."
                ),
                suggestion=(
                    "Enable audit logging for integration "
                    "tests that verify audit behavior."
                ),
            )

    def _validate_storage_policy(
        self,
        configuration: ConfigurationSchema,
        collector: _ValidationCollector,
    ) -> None:
        """
        Validate persistent-storage environment policy.
        """

        environment = configuration.environment

        if not environment.requires_persistent_storage:
            return

        temporary_directory = (
            configuration.temporary_directory
        )

        persistent_fields = {
            "storage_directory": (
                configuration.storage_directory
            ),
            "data_directory": (
                configuration.data_directory
            ),
            "configuration_directory": (
                configuration.configuration_directory
            ),
        }

        if not isinstance(temporary_directory, Path):
            return

        try:
            normalized_temporary = (
                temporary_directory
                .expanduser()
                .resolve(strict=False)
            )
        except OSError:
            return

        for field_name, path in persistent_fields.items():
            if not isinstance(path, Path):
                continue

            try:
                normalized_path = (
                    path
                    .expanduser()
                    .resolve(strict=False)
                )
            except OSError:
                continue

            if normalized_path == normalized_temporary:
                collector.error(
                    code="CFG-POLICY-STORAGE-001",
                    field=field_name,
                    message=(
                        f"{field_name} cannot use the same "
                        "location as temporary_directory in "
                        f"the {environment.label} environment."
                    ),
                )

            elif self._is_path_within(
                normalized_path,
                normalized_temporary,
            ):
                collector.error(
                    code="CFG-POLICY-STORAGE-002",
                    field=field_name,
                    message=(
                        f"{field_name} cannot be located "
                        "inside temporary_directory in the "
                        f"{environment.label} environment."
                    ),
                    suggestion=(
                        "Use a persistent filesystem location."
                    ),
                )
    """
============================================================
SECTION 17 — Default Validator and Convenience Functions
============================================================

The default validator is shared by ConfigLoader and any platform
module that does not require custom validation behavior.

Convenience functions provide a small functional API while
preserving the reusable ConfigurationValidator class.
============================================================
    """


DEFAULT_CONFIGURATION_VALIDATOR = ConfigurationValidator()


def validate_configuration(
    configuration: ConfigurationSchema,
) -> ConfigurationValidationResult:
    """
    Validate configuration using the default validator.
    """

    return DEFAULT_CONFIGURATION_VALIDATOR.validate(
        configuration
    )


def validate_configuration_or_raise(
    configuration: ConfigurationSchema,
) -> ConfigurationValidationResult:
    """
    Validate configuration and raise when invalid.
    """

    return DEFAULT_CONFIGURATION_VALIDATOR.validate_or_raise(
        configuration
    )


def is_configuration_valid(
    configuration: ConfigurationSchema,
) -> bool:
    """
    Return True when configuration is valid.
    """

    return DEFAULT_CONFIGURATION_VALIDATOR.is_valid(
        configuration
    )
