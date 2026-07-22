"""
Typed roadmap domain models for the Nexa Provider Platform.

This module converts raw roadmap mappings into immutable, validated Python
objects. It contains no persistence, CLI, Markdown generation, dependency
resolution, or roadmap mutation logic.

The canonical lifecycle status definitions come from ``roadmap.statuses``.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date
from types import MappingProxyType
from typing import Any, Final, Iterable, Mapping, TypeAlias

from .statuses import RoadmapStatus, StatusLike, normalize_status


JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = (
    JsonScalar
    | list["JsonValue"]
    | dict[str, "JsonValue"]
)

ROOT_DEPTH: Final[int] = 0
RECORD_ID_PREFIX: Final[str] = "npp-rm-"


class RoadmapModelError(ValueError):
    """Base exception for invalid roadmap model data."""


class MissingRoadmapFieldError(RoadmapModelError):
    """Raised when a required roadmap field is absent."""


class InvalidRoadmapFieldError(RoadmapModelError):
    """Raised when a roadmap field contains an invalid value."""


def _require_mapping_value(
    source: Mapping[str, Any],
    key: str,
) -> Any:
    if key not in source:
        raise MissingRoadmapFieldError(f"Missing required roadmap field: {key}")
    return source[key]


def _require_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise InvalidRoadmapFieldError(
            f"{field_name} must be a string, received {type(value).__name__}"
        )
    normalized = value.strip()
    if not normalized:
        raise InvalidRoadmapFieldError(f"{field_name} cannot be blank")
    return normalized


def _optional_string(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_non_empty_string(value, field_name)


def _require_non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidRoadmapFieldError(
            f"{field_name} must be an integer, received {type(value).__name__}"
        )
    if value < 0:
        raise InvalidRoadmapFieldError(f"{field_name} cannot be negative")
    return value


def _require_positive_int(value: Any, field_name: str) -> int:
    parsed = _require_non_negative_int(value, field_name)
    if parsed == 0:
        raise InvalidRoadmapFieldError(f"{field_name} must be greater than zero")
    return parsed


def _parse_optional_date(value: Any, field_name: str) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise InvalidRoadmapFieldError(
            f"{field_name} must be an ISO date string, date, or None"
        )
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise InvalidRoadmapFieldError(
            f"{field_name} must use ISO format YYYY-MM-DD"
        ) from exc


def _normalize_string_tuple(
    value: Any,
    field_name: str,
) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        value = (value,)
    try:
        items = tuple(value)
    except TypeError as exc:
        raise InvalidRoadmapFieldError(
            f"{field_name} must be a string or iterable of strings"
        ) from exc

    normalized: list[str] = []
    for index, item in enumerate(items):
        normalized.append(
            _require_non_empty_string(item, f"{field_name}[{index}]")
        )
    return tuple(normalized)


def _freeze_metadata(value: Any) -> Mapping[str, JsonValue]:
    if value is None:
        return MappingProxyType({})
    if not isinstance(value, Mapping):
        raise InvalidRoadmapFieldError("metadata must be a mapping")
    return MappingProxyType(dict(value))


def expected_depth(number: str) -> int:
    """Return the hierarchy depth implied by a visible milestone number."""

    normalized = _require_non_empty_string(number, "number")
    if not normalized.startswith("M"):
        raise InvalidRoadmapFieldError(
            "number must begin with the milestone prefix 'M'"
        )
    return normalized.count(".")


def derive_parent_number(number: str) -> str | None:
    """Derive the visible parent number from a milestone number."""

    normalized = _require_non_empty_string(number, "number")
    if expected_depth(normalized) == ROOT_DEPTH:
        return None
    return normalized.rsplit(".", 1)[0]


@dataclass(frozen=True, slots=True)
class Milestone:
    """
    Immutable roadmap milestone domain model.

    ``number`` is positional and may change during renumbering.
    ``record_id`` is stable identity and must survive renumbering.
    """

    record_id: str
    number: str
    title: str
    parent_number: str | None
    sequence: int
    depth: int
    semantic_path: str
    status: RoadmapStatus = RoadmapStatus.PLANNED
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    priority: str | None = None
    commit_hash: str | None = None
    verification_state: str | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)
    test_information: tuple[str, ...] = field(default_factory=tuple)
    passing_tests: int | None = None
    started_date: date | None = None
    completed_date: date | None = None
    metadata: Mapping[str, JsonValue] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        record_id = _require_non_empty_string(self.record_id, "record_id")
        number = _require_non_empty_string(self.number, "number")
        title = _require_non_empty_string(self.title, "title")
        semantic_path = _require_non_empty_string(
            self.semantic_path,
            "semantic_path",
        )
        parent_number = _optional_string(self.parent_number, "parent_number")
        sequence = _require_positive_int(self.sequence, "sequence")
        depth = _require_non_negative_int(self.depth, "depth")
        status = normalize_status(self.status)
        dependencies = _normalize_string_tuple(
            self.dependencies,
            "dependencies",
        )
        priority = _optional_string(self.priority, "priority")
        commit_hash = _optional_string(self.commit_hash, "commit_hash")
        verification_state = _optional_string(
            self.verification_state,
            "verification_state",
        )
        notes = _normalize_string_tuple(self.notes, "notes")
        test_information = _normalize_string_tuple(
            self.test_information,
            "test_information",
        )
        started_date = _parse_optional_date(self.started_date, "started_date")
        completed_date = _parse_optional_date(
            self.completed_date,
            "completed_date",
        )
        metadata = _freeze_metadata(self.metadata)

        if not record_id.startswith(RECORD_ID_PREFIX):
            raise InvalidRoadmapFieldError(
                f"record_id must start with {RECORD_ID_PREFIX!r}"
            )

        implied_depth = expected_depth(number)
        if depth != implied_depth:
            raise InvalidRoadmapFieldError(
                f"depth {depth} does not match number {number!r}; "
                f"expected {implied_depth}"
            )

        derived_parent = derive_parent_number(number)
        if parent_number != derived_parent:
            raise InvalidRoadmapFieldError(
                f"parent_number {parent_number!r} does not match number "
                f"{number!r}; expected {derived_parent!r}"
            )

        if self.passing_tests is not None:
            passing_tests = _require_non_negative_int(
                self.passing_tests,
                "passing_tests",
            )
        else:
            passing_tests = None

        if (
            started_date is not None
            and completed_date is not None
            and completed_date < started_date
        ):
            raise InvalidRoadmapFieldError(
                "completed_date cannot be earlier than started_date"
            )

        object.__setattr__(self, "record_id", record_id)
        object.__setattr__(self, "number", number)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "parent_number", parent_number)
        object.__setattr__(self, "sequence", sequence)
        object.__setattr__(self, "depth", depth)
        object.__setattr__(self, "semantic_path", semantic_path)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "dependencies", dependencies)
        object.__setattr__(self, "priority", priority)
        object.__setattr__(self, "commit_hash", commit_hash)
        object.__setattr__(self, "verification_state", verification_state)
        object.__setattr__(self, "notes", notes)
        object.__setattr__(self, "test_information", test_information)
        object.__setattr__(self, "passing_tests", passing_tests)
        object.__setattr__(self, "started_date", started_date)
        object.__setattr__(self, "completed_date", completed_date)
        object.__setattr__(self, "metadata", metadata)

    @property
    def is_root(self) -> bool:
        """Return whether this is a root milestone."""

        return self.parent_number is None

    @property
    def is_child(self) -> bool:
        """Return whether this milestone has a parent."""

        return self.parent_number is not None

    @property
    def path_parts(self) -> tuple[str, ...]:
        """Return semantic-path components."""

        return tuple(
            part for part in self.semantic_path.split("/")
            if part
        )

    @classmethod
    def from_mapping(cls, source: Mapping[str, Any]) -> "Milestone":
        """Construct and validate a milestone from a raw mapping."""

        if not isinstance(source, Mapping):
            raise TypeError("source must be a mapping")

        known_fields = {
            "record_id",
            "number",
            "title",
            "parent_number",
            "sequence",
            "depth",
            "semantic_path",
            "status",
            "dependencies",
            "priority",
            "commit_hash",
            "verification_state",
            "notes",
            "test_information",
            "passing_tests",
            "started_date",
            "completed_date",
            "metadata",
        }

        metadata = dict(source.get("metadata") or {})
        for key, value in source.items():
            if key not in known_fields:
                metadata[key] = value

        return cls(
            record_id=_require_mapping_value(source, "record_id"),
            number=_require_mapping_value(source, "number"),
            title=_require_mapping_value(source, "title"),
            parent_number=source.get("parent_number"),
            sequence=_require_mapping_value(source, "sequence"),
            depth=_require_mapping_value(source, "depth"),
            semantic_path=_require_mapping_value(source, "semantic_path"),
            status=source.get("status", RoadmapStatus.PLANNED),
            dependencies=source.get("dependencies", ()),
            priority=source.get("priority"),
            commit_hash=source.get("commit_hash"),
            verification_state=source.get("verification_state"),
            notes=source.get("notes", ()),
            test_information=source.get("test_information", ()),
            passing_tests=source.get("passing_tests"),
            started_date=source.get("started_date"),
            completed_date=source.get("completed_date"),
            metadata=metadata,
        )

    def to_mapping(
        self,
        *,
        include_metadata: bool = True,
        flatten_metadata: bool = False,
    ) -> dict[str, Any]:
        """Serialize the milestone into a new plain dictionary."""

        result: dict[str, Any] = {
            "record_id": self.record_id,
            "number": self.number,
            "title": self.title,
            "parent_number": self.parent_number,
            "sequence": self.sequence,
            "depth": self.depth,
            "semantic_path": self.semantic_path,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "priority": self.priority,
            "commit_hash": self.commit_hash,
            "verification_state": self.verification_state,
            "notes": self.notes,
            "test_information": self.test_information,
            "passing_tests": self.passing_tests,
            "started_date": (
                self.started_date.isoformat()
                if self.started_date is not None
                else None
            ),
            "completed_date": (
                self.completed_date.isoformat()
                if self.completed_date is not None
                else None
            ),
        }

        if include_metadata:
            if flatten_metadata:
                for key, value in self.metadata.items():
                    result.setdefault(key, value)
            else:
                result["metadata"] = dict(self.metadata)

        return result

    def with_changes(self, **changes: Any) -> "Milestone":
        """
        Return a validated copy with selected fields changed.

        Stable record identity changes are intentionally blocked.
        """

        if "record_id" in changes and changes["record_id"] != self.record_id:
            raise InvalidRoadmapFieldError(
                "record_id is immutable and cannot be changed"
            )
        return replace(self, **changes)


@dataclass(frozen=True, slots=True)
class RoadmapMetadata:
    """Immutable metadata describing one roadmap dataset."""

    title: str
    version: str
    start: str
    end: str
    allowed_statuses: tuple[RoadmapStatus, ...]
    boundaries: Mapping[str, JsonValue] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "title",
            _require_non_empty_string(self.title, "title"),
        )
        object.__setattr__(
            self,
            "version",
            _require_non_empty_string(self.version, "version"),
        )
        object.__setattr__(
            self,
            "start",
            _require_non_empty_string(self.start, "start"),
        )
        object.__setattr__(
            self,
            "end",
            _require_non_empty_string(self.end, "end"),
        )

        statuses = tuple(
            normalize_status(status)
            for status in self.allowed_statuses
        )
        if not statuses:
            raise InvalidRoadmapFieldError(
                "allowed_statuses cannot be empty"
            )
        if len(statuses) != len(set(statuses)):
            raise InvalidRoadmapFieldError(
                "allowed_statuses cannot contain duplicates"
            )

        object.__setattr__(self, "allowed_statuses", statuses)
        object.__setattr__(
            self,
            "boundaries",
            _freeze_metadata(self.boundaries),
        )


@dataclass(frozen=True, slots=True)
class RoadmapSnapshot:
    """Immutable collection of roadmap metadata and milestone records."""

    metadata: RoadmapMetadata
    milestones: tuple[Milestone, ...]

    def __post_init__(self) -> None:
        milestones = tuple(self.milestones)
        if not milestones:
            raise InvalidRoadmapFieldError(
                "roadmap snapshot must contain at least one milestone"
            )
        if not all(isinstance(item, Milestone) for item in milestones):
            raise InvalidRoadmapFieldError(
                "milestones must contain only Milestone instances"
            )
        object.__setattr__(self, "milestones", milestones)

    @property
    def total(self) -> int:
        return len(self.milestones)

    @property
    def roots(self) -> tuple[Milestone, ...]:
        return tuple(item for item in self.milestones if item.is_root)

    def by_number(self) -> Mapping[str, Milestone]:
        return MappingProxyType(
            {item.number: item for item in self.milestones}
        )

    def by_record_id(self) -> Mapping[str, Milestone]:
        return MappingProxyType(
            {item.record_id: item for item in self.milestones}
        )


def milestones_from_mappings(
    records: Iterable[Mapping[str, Any]],
) -> tuple[Milestone, ...]:
    """Convert raw roadmap records into immutable milestone models."""

    return tuple(Milestone.from_mapping(record) for record in records)


def milestone_to_mapping(
    milestone: Milestone,
    *,
    include_metadata: bool = True,
    flatten_metadata: bool = False,
) -> dict[str, Any]:
    """Functional serialization wrapper for one milestone."""

    if not isinstance(milestone, Milestone):
        raise TypeError("milestone must be a Milestone instance")
    return milestone.to_mapping(
        include_metadata=include_metadata,
        flatten_metadata=flatten_metadata,
    )


__all__ = (
    "InvalidRoadmapFieldError",
    "JsonScalar",
    "JsonValue",
    "Milestone",
    "MissingRoadmapFieldError",
    "RECORD_ID_PREFIX",
    "ROOT_DEPTH",
    "RoadmapMetadata",
    "RoadmapModelError",
    "RoadmapSnapshot",
    "derive_parent_number",
    "expected_depth",
    "milestone_to_mapping",
    "milestones_from_mappings",
)
