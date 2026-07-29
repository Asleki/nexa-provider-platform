"""Framework-neutral contracts for M008.16.6 relationship validation APIs.

The contracts carry already validated relationship value objects through one
application boundary.  They do not persist relationships, publish events,
resolve registry records, authorise callers, or imply approval.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Final

from .constraint_contract import RelationshipConstraint
from .direction_contract import RelationshipDirection
from .provenance_contract import RelationshipProvenance
from .relationship_constraint_rules import RelationshipConstraintContext
from .relationship_definition import RelationshipDefinition

_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")


class RelationshipApiError(ValueError):
    """Base error for relationship API contracts."""


class RelationshipApiValidationError(RelationshipApiError):
    """Raised when a validation request is malformed."""


class RelationshipApiContractError(RelationshipApiError):
    """Raised when an API capability declaration is malformed."""


class RelationshipApiResultError(RelationshipApiError):
    """Raised when an API finding or result is internally inconsistent."""


class RelationshipApiOperation(str, Enum):
    VALIDATE = "validate"

    @classmethod
    def parse(cls, value: "RelationshipApiOperation | str") -> "RelationshipApiOperation":
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise TypeError("operation must be a RelationshipApiOperation or text.")
        try:
            return cls(value.strip().lower())
        except ValueError as exc:
            raise RelationshipApiValidationError(f"unsupported relationship API operation: {value!r}.") from exc


class RelationshipApiSubsystem(str, Enum):
    IMMUTABLE_REFERENCE = "immutable_reference"
    DIRECTION = "direction"
    CONSTRAINT = "constraint"
    PROVENANCE = "provenance"

    @classmethod
    def parse(cls, value: "RelationshipApiSubsystem | str") -> "RelationshipApiSubsystem":
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise TypeError("subsystem must be a RelationshipApiSubsystem or text.")
        try:
            return cls(value.strip().lower())
        except ValueError as exc:
            raise RelationshipApiResultError(f"unsupported relationship API subsystem: {value!r}.") from exc


def _identifier(name: str, value: object, error_type: type[RelationshipApiError]) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be text.")
    normalised = value.strip()
    if not normalised:
        raise error_type(f"{name} cannot be empty.")
    if not _ID_PATTERN.fullmatch(normalised):
        raise error_type(
            f"{name} must start with a letter or digit and contain only letters, "
            "digits, '.', '_', ':' or '-'."
        )
    return normalised


def _aware_datetime(name: str, value: object, error_type: type[RelationshipApiError]) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise error_type(f"{name} must be timezone-aware.")
    return value.astimezone(timezone.utc)


def _parse_datetime(name: str, value: object, error_type: type[RelationshipApiError]) -> datetime:
    if isinstance(value, datetime):
        return _aware_datetime(name, value, error_type)
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a datetime or ISO datetime string.")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise error_type(f"{name} must be a valid ISO datetime string.") from exc
    return _aware_datetime(name, parsed, error_type)


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        frozen: dict[object, object] = {}
        for key, nested in value.items():
            try:
                hash(key)
            except TypeError as exc:
                raise TypeError("metadata mapping keys must be hashable.") from exc
            frozen[key] = _freeze(nested)
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze(item) for item in value)
    return value


def _thaw(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw(nested) for key, nested in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    if isinstance(value, frozenset):
        return [_thaw(item) for item in sorted(value, key=repr)]
    return value


def _normalise_metadata(value: object, error_type: type[RelationshipApiError]) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError("metadata must be a mapping.")
    normalised: dict[str, object] = {}
    for key, nested in value.items():
        if not isinstance(key, str):
            raise TypeError("metadata keys must be text.")
        clean = key.strip()
        if not clean:
            raise error_type("metadata keys cannot be empty.")
        if clean in normalised:
            raise error_type("metadata keys must remain unique after whitespace normalization.")
        normalised[clean] = _freeze(nested)
    return MappingProxyType(normalised)


@dataclass(frozen=True, slots=True)
class RelationshipApiContract:
    name: str = "relationship"
    version: int = 1
    operations: tuple[RelationshipApiOperation, ...] = (RelationshipApiOperation.VALIDATE,)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise RelationshipApiContractError("name must be non-empty text.")
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version < 1:
            raise RelationshipApiContractError("version must be a positive integer.")
        if not isinstance(self.operations, tuple):
            raise RelationshipApiContractError("operations must be a tuple.")
        parsed = tuple(RelationshipApiOperation.parse(item) for item in self.operations)
        if not parsed or len(parsed) != len(set(parsed)):
            raise RelationshipApiContractError("operations must be non-empty and unique.")
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "operations", parsed)

    def supports(self, operation: RelationshipApiOperation | str) -> bool:
        try:
            return RelationshipApiOperation.parse(operation) in self.operations
        except (TypeError, RelationshipApiError):
            return False

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "version": self.version, "operations": [item.value for item in self.operations]}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "RelationshipApiContract":
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        allowed = {"name", "version", "operations"}
        unknown = set(data) - allowed
        if unknown:
            raise RelationshipApiContractError(f"unknown relationship API contract fields: {', '.join(sorted(map(str, unknown)))}.")
        payload = dict(data)
        if "operations" in payload:
            value = payload["operations"]
            if not isinstance(value, (list, tuple)):
                raise TypeError("operations must be a list or tuple.")
            payload["operations"] = tuple(RelationshipApiOperation.parse(item) for item in value)
        return cls(**payload)


@dataclass(frozen=True, slots=True)
class RelationshipValidationRequest:
    request_id: str
    relationship: RelationshipDefinition
    direction: RelationshipDirection
    constraint: RelationshipConstraint
    constraint_context: RelationshipConstraintContext
    provenance: RelationshipProvenance
    requested_at: datetime
    operation: RelationshipApiOperation = RelationshipApiOperation.VALIDATE
    existing_relationship: RelationshipDefinition | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_id", _identifier("request_id", self.request_id, RelationshipApiValidationError))
        object.__setattr__(self, "operation", RelationshipApiOperation.parse(self.operation))
        typed = (
            ("relationship", self.relationship, RelationshipDefinition),
            ("direction", self.direction, RelationshipDirection),
            ("constraint", self.constraint, RelationshipConstraint),
            ("constraint_context", self.constraint_context, RelationshipConstraintContext),
            ("provenance", self.provenance, RelationshipProvenance),
        )
        for name, value, expected in typed:
            if not isinstance(value, expected):
                raise TypeError(f"{name} must be a {expected.__name__}.")
        if self.existing_relationship is not None and not isinstance(self.existing_relationship, RelationshipDefinition):
            raise TypeError("existing_relationship must be a RelationshipDefinition or None.")
        object.__setattr__(self, "requested_at", _aware_datetime("requested_at", self.requested_at, RelationshipApiValidationError))
        object.__setattr__(self, "metadata", _normalise_metadata(self.metadata, RelationshipApiValidationError))

    def to_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "operation": self.operation.value,
            "relationship": self.relationship.to_dict(),
            "direction": self.direction.to_dict(),
            "constraint": self.constraint.to_dict(),
            "constraint_context": self.constraint_context.to_dict(),
            "provenance": self.provenance.to_dict(),
            "requested_at": self.requested_at.isoformat(),
            "existing_relationship": None if self.existing_relationship is None else self.existing_relationship.to_dict(),
            "metadata": _thaw(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "RelationshipValidationRequest":
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        allowed = {
            "request_id", "operation", "relationship", "direction", "constraint",
            "constraint_context", "provenance", "requested_at", "existing_relationship", "metadata",
        }
        unknown = set(data) - allowed
        if unknown:
            raise RelationshipApiValidationError(f"unknown relationship validation request fields: {', '.join(sorted(map(str, unknown)))}.")
        payload = dict(data)
        required = {"request_id", "relationship", "direction", "constraint", "constraint_context", "provenance", "requested_at"}
        missing = required - set(payload)
        if missing:
            raise RelationshipApiValidationError(f"missing required relationship validation request fields: {', '.join(sorted(missing))}.")
        converters = {
            "relationship": RelationshipDefinition.from_dict,
            "direction": RelationshipDirection.from_dict,
            "constraint": RelationshipConstraint.from_dict,
            "constraint_context": RelationshipConstraintContext.from_dict,
            "provenance": RelationshipProvenance.from_dict,
        }
        for name, converter in converters.items():
            if not isinstance(payload[name], {
                "relationship": RelationshipDefinition,
                "direction": RelationshipDirection,
                "constraint": RelationshipConstraint,
                "constraint_context": RelationshipConstraintContext,
                "provenance": RelationshipProvenance,
            }[name]):
                payload[name] = converter(payload[name])
        existing = payload.get("existing_relationship")
        if existing is not None and not isinstance(existing, RelationshipDefinition):
            payload["existing_relationship"] = RelationshipDefinition.from_dict(existing)
        payload["requested_at"] = _parse_datetime("requested_at", payload["requested_at"], RelationshipApiValidationError)
        if "operation" in payload:
            payload["operation"] = RelationshipApiOperation.parse(payload["operation"])
        return cls(**payload)


@dataclass(frozen=True, slots=True)
class RelationshipApiFinding:
    subsystem: RelationshipApiSubsystem
    code: str
    message: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "subsystem", RelationshipApiSubsystem.parse(self.subsystem))
        for name in ("code", "message"):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(f"{name} must be text.")
            clean = value.strip()
            if not clean:
                raise RelationshipApiResultError(f"{name} cannot be empty.")
            object.__setattr__(self, name, clean)

    def to_dict(self) -> dict[str, str]:
        return {"subsystem": self.subsystem.value, "code": self.code, "message": self.message}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "RelationshipApiFinding":
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        allowed = {"subsystem", "code", "message"}
        unknown = set(data) - allowed
        if unknown:
            raise RelationshipApiResultError(f"unknown relationship API finding fields: {', '.join(sorted(map(str, unknown)))}.")
        try:
            return cls(**dict(data))
        except TypeError as exc:
            raise RelationshipApiResultError("relationship API finding requires subsystem, code and message.") from exc


@dataclass(frozen=True, slots=True)
class RelationshipValidationResult:
    request_id: str
    completed_at: datetime
    is_valid: bool
    findings: tuple[RelationshipApiFinding, ...] = ()
    operation: RelationshipApiOperation = RelationshipApiOperation.VALIDATE
    api_name: str = "relationship"
    api_version: int = 1
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_id", _identifier("request_id", self.request_id, RelationshipApiResultError))
        object.__setattr__(self, "operation", RelationshipApiOperation.parse(self.operation))
        object.__setattr__(self, "completed_at", _aware_datetime("completed_at", self.completed_at, RelationshipApiResultError))
        if not isinstance(self.is_valid, bool):
            raise TypeError("is_valid must be a boolean.")
        if not isinstance(self.findings, tuple):
            raise TypeError("findings must be a tuple.")
        seen: set[tuple[RelationshipApiSubsystem, str]] = set()
        for finding in self.findings:
            if not isinstance(finding, RelationshipApiFinding):
                raise TypeError("findings must contain RelationshipApiFinding values.")
            key = (finding.subsystem, finding.code)
            if key in seen:
                raise RelationshipApiResultError("findings must be unique by subsystem and code.")
            seen.add(key)
        if self.is_valid and self.findings:
            raise RelationshipApiResultError("valid results cannot contain findings.")
        if not self.is_valid and not self.findings:
            raise RelationshipApiResultError("invalid results must contain findings.")
        if not isinstance(self.api_name, str) or not self.api_name.strip():
            raise RelationshipApiResultError("api_name must be non-empty text.")
        object.__setattr__(self, "api_name", self.api_name.strip())
        if isinstance(self.api_version, bool) or not isinstance(self.api_version, int) or self.api_version < 1:
            raise RelationshipApiResultError("api_version must be a positive integer.")
        object.__setattr__(self, "metadata", _normalise_metadata(self.metadata, RelationshipApiResultError))

    @classmethod
    def valid(cls, *, request_id: str, completed_at: datetime, operation: RelationshipApiOperation = RelationshipApiOperation.VALIDATE, api_name: str = "relationship", api_version: int = 1, metadata: Mapping[str, object] | None = None) -> "RelationshipValidationResult":
        return cls(request_id, completed_at, True, operation=operation, api_name=api_name, api_version=api_version, metadata={} if metadata is None else metadata)

    @classmethod
    def invalid(cls, *, request_id: str, completed_at: datetime, findings: tuple[RelationshipApiFinding, ...], operation: RelationshipApiOperation = RelationshipApiOperation.VALIDATE, api_name: str = "relationship", api_version: int = 1, metadata: Mapping[str, object] | None = None) -> "RelationshipValidationResult":
        return cls(request_id, completed_at, False, findings, operation, api_name, api_version, {} if metadata is None else metadata)

    def to_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "operation": self.operation.value,
            "completed_at": self.completed_at.isoformat(),
            "is_valid": self.is_valid,
            "findings": [finding.to_dict() for finding in self.findings],
            "api_name": self.api_name,
            "api_version": self.api_version,
            "metadata": _thaw(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "RelationshipValidationResult":
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        allowed = {"request_id", "operation", "completed_at", "is_valid", "findings", "api_name", "api_version", "metadata"}
        unknown = set(data) - allowed
        if unknown:
            raise RelationshipApiResultError(f"unknown relationship validation result fields: {', '.join(sorted(map(str, unknown)))}.")
        payload = dict(data)
        required = {"request_id", "completed_at", "is_valid"}
        missing = required - set(payload)
        if missing:
            raise RelationshipApiResultError(f"missing required relationship validation result fields: {', '.join(sorted(missing))}.")
        payload["completed_at"] = _parse_datetime("completed_at", payload["completed_at"], RelationshipApiResultError)
        if "operation" in payload:
            payload["operation"] = RelationshipApiOperation.parse(payload["operation"])
        raw_findings = payload.get("findings", ())
        if not isinstance(raw_findings, (list, tuple)):
            raise TypeError("findings must be a list or tuple.")
        payload["findings"] = tuple(item if isinstance(item, RelationshipApiFinding) else RelationshipApiFinding.from_dict(item) for item in raw_findings)
        return cls(**payload)


__all__ = [
    "RelationshipApiContract", "RelationshipApiContractError", "RelationshipApiError",
    "RelationshipApiFinding", "RelationshipApiOperation", "RelationshipApiResultError",
    "RelationshipApiSubsystem", "RelationshipApiValidationError",
    "RelationshipValidationRequest", "RelationshipValidationResult",
]
