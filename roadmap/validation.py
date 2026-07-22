"""
Comprehensive roadmap validation for the Nexa Provider Platform.

The module validates raw roadmap mappings, immutable ``Milestone`` models,
metadata, snapshots, hierarchy, identities, sequencing, semantic paths,
statuses, lifecycle dates, test data, commit hashes, dependency references,
and complete roadmap collections.

Validation is read-only. It returns immutable reports and can optionally raise
``RoadmapValidationError`` when errors are present.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

from .dependencies import validate_dependencies
from .models import (
    ROOT_DEPTH,
    Milestone,
    RoadmapMetadata,
    RoadmapSnapshot,
    derive_parent_number,
    expected_depth,
)
from .queries import MilestoneSource, all_milestones
from .statuses import RoadmapStatus, StatusLike, normalize_status


RECORD_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NUMBER_PATTERN = re.compile(r"^M\d{3}(?:\.\d+)*$")
COMMIT_HASH_PATTERN = re.compile(r"^[0-9a-fA-F]{7,64}$")
SEMANTIC_PATH_SEPARATOR = " / "

REQUIRED_MAPPING_FIELDS = (
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
    "passing_tests",
    "started_date",
    "completed_date",
)


class RoadmapValidationError(ValueError):
    """Raised when roadmap validation finds one or more errors."""

    def __init__(self, report: "ValidationReport") -> None:
        self.report = report
        super().__init__(
            f"Roadmap validation failed with {report.error_count} error(s) "
            f"and {report.warning_count} warning(s)"
        )


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One immutable validation finding."""

    code: str
    message: str
    severity: str = "ERROR"
    record_id: str | None = None
    number: str | None = None
    field: str | None = None

    def __post_init__(self) -> None:
        if self.severity not in {"ERROR", "WARNING"}:
            raise ValueError("severity must be ERROR or WARNING")
        if not self.code.strip():
            raise ValueError("code cannot be blank")
        if not self.message.strip():
            raise ValueError("message cannot be blank")

    @property
    def is_error(self) -> bool:
        return self.severity == "ERROR"

    @property
    def is_warning(self) -> bool:
        return self.severity == "WARNING"

    def to_mapping(self) -> dict[str, str | None]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "record_id": self.record_id,
            "number": self.number,
            "field": self.field,
        }


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Immutable result of a validation pass."""

    issues: tuple[ValidationIssue, ...]
    records_checked: int = 0
    metadata_checked: bool = False

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.is_error)

    @property
    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.is_warning)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    @property
    def is_valid(self) -> bool:
        return self.error_count == 0

    @property
    def is_clean(self) -> bool:
        return not self.issues

    def by_code(self) -> Mapping[str, tuple[ValidationIssue, ...]]:
        grouped: dict[str, list[ValidationIssue]] = defaultdict(list)
        for issue in self.issues:
            grouped[issue.code].append(issue)
        return MappingProxyType({
            code: tuple(values) for code, values in grouped.items()
        })

    def to_mapping(self) -> dict[str, object]:
        return {
            "is_valid": self.is_valid,
            "is_clean": self.is_clean,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "records_checked": self.records_checked,
            "metadata_checked": self.metadata_checked,
            "issues": tuple(issue.to_mapping() for issue in self.issues),
        }

    def raise_for_errors(self) -> "ValidationReport":
        if not self.is_valid:
            raise RoadmapValidationError(self)
        return self


def _issue(
    code: str,
    message: str,
    *,
    severity: str = "ERROR",
    milestone: Milestone | None = None,
    record_id: str | None = None,
    number: str | None = None,
    field: str | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        message=message,
        severity=severity,
        record_id=record_id if record_id is not None else (
            milestone.record_id if milestone else None
        ),
        number=number if number is not None else (
            milestone.number if milestone else None
        ),
        field=field,
    )


def _parse_date(value: str | None, field: str, milestone: Milestone) -> tuple[date | None, list[ValidationIssue]]:
    if value is None:
        return None, []
    try:
        return date.fromisoformat(value), []
    except (TypeError, ValueError):
        return None, [_issue(
            "INVALID_DATE",
            f"{field} must use ISO date format YYYY-MM-DD",
            milestone=milestone,
            field=field,
        )]


def validate_mapping(
    mapping: Mapping[str, Any],
    *,
    allow_extra_fields: bool = True,
) -> ValidationReport:
    """Validate a raw milestone mapping without constructing a model."""

    if not isinstance(mapping, Mapping):
        raise TypeError("mapping must implement Mapping")

    issues: list[ValidationIssue] = []
    keys = set(mapping)
    required = set(REQUIRED_MAPPING_FIELDS)

    for field in sorted(required - keys):
        issues.append(_issue(
            "MISSING_FIELD",
            f"Required field {field!r} is missing",
            record_id=str(mapping.get("record_id")) if mapping.get("record_id") else None,
            number=str(mapping.get("number")) if mapping.get("number") else None,
            field=field,
        ))

    if not allow_extra_fields:
        for field in sorted(keys - required):
            issues.append(_issue(
                "EXTRA_FIELD",
                f"Unexpected field {field!r}",
                record_id=str(mapping.get("record_id")) if mapping.get("record_id") else None,
                number=str(mapping.get("number")) if mapping.get("number") else None,
                field=field,
            ))

    if "record_id" in mapping:
        value = mapping["record_id"]
        if not isinstance(value, str) or not value.strip():
            issues.append(_issue(
                "INVALID_RECORD_ID",
                "record_id must be a non-empty string",
                field="record_id",
            ))
        elif not RECORD_ID_PATTERN.fullmatch(value):
            issues.append(_issue(
                "INVALID_RECORD_ID_FORMAT",
                "record_id must be lowercase kebab-case",
                record_id=value,
                field="record_id",
            ))

    if "number" in mapping:
        value = mapping["number"]
        if not isinstance(value, str) or not NUMBER_PATTERN.fullmatch(value):
            issues.append(_issue(
                "INVALID_NUMBER_FORMAT",
                "number must match MNNN or MNNN.N hierarchy format",
                number=value if isinstance(value, str) else None,
                field="number",
            ))

    if "sequence" in mapping:
        value = mapping["sequence"]
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            issues.append(_issue(
                "INVALID_SEQUENCE",
                "sequence must be a positive integer",
                field="sequence",
            ))

    if "depth" in mapping:
        value = mapping["depth"]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            issues.append(_issue(
                "INVALID_DEPTH",
                "depth must be a non-negative integer",
                field="depth",
            ))

    if "status" in mapping:
        try:
            normalize_status(mapping["status"])
        except (TypeError, ValueError):
            issues.append(_issue(
                "INVALID_STATUS",
                f"Unsupported status {mapping['status']!r}",
                field="status",
            ))

    if "dependencies" in mapping and not isinstance(
        mapping["dependencies"], (tuple, list)
    ):
        issues.append(_issue(
            "INVALID_DEPENDENCIES",
            "dependencies must be a tuple or list",
            field="dependencies",
        ))

    if "notes" in mapping and mapping["notes"] is not None and not isinstance(
        mapping["notes"], (tuple, list, str)
    ):
        issues.append(_issue(
            "INVALID_NOTES",
            "notes must be a string, tuple, or list",
            field="notes",
        ))

    if (
        "test_information" in mapping
        and mapping["test_information"] is not None
        and not isinstance(mapping["test_information"], (tuple, list, str))
    ):
        issues.append(_issue(
            "INVALID_TEST_INFORMATION",
            "test_information must be a string, tuple, or list",
            field="test_information",
        ))

    return ValidationReport(tuple(issues), records_checked=1)


def validate_milestone(
    milestone: Milestone,
    *,
    allowed_statuses: Iterable[StatusLike] | None = None,
    require_commit_for_complete: bool = False,
    require_completed_date_for_complete: bool = False,
    warn_on_empty_title: bool = True,
) -> ValidationReport:
    """Validate one immutable milestone model."""

    if not isinstance(milestone, Milestone):
        raise TypeError("milestone must be a Milestone")

    issues: list[ValidationIssue] = []

    if not RECORD_ID_PATTERN.fullmatch(milestone.record_id):
        issues.append(_issue(
            "INVALID_RECORD_ID_FORMAT",
            "record_id must be lowercase kebab-case",
            milestone=milestone,
            field="record_id",
        ))

    if not NUMBER_PATTERN.fullmatch(milestone.number):
        issues.append(_issue(
            "INVALID_NUMBER_FORMAT",
            "number must match MNNN or MNNN.N hierarchy format",
            milestone=milestone,
            field="number",
        ))

    if not milestone.title.strip():
        issues.append(_issue(
            "EMPTY_TITLE",
            "title cannot be blank",
            milestone=milestone,
            field="title",
            severity="WARNING" if warn_on_empty_title else "ERROR",
        ))

    calculated_depth = expected_depth(milestone.number)
    if milestone.depth != calculated_depth:
        issues.append(_issue(
            "DEPTH_MISMATCH",
            f"depth {milestone.depth} does not match number-derived depth {calculated_depth}",
            milestone=milestone,
            field="depth",
        ))

    calculated_parent = derive_parent_number(milestone.number)
    if milestone.parent_number != calculated_parent:
        issues.append(_issue(
            "PARENT_NUMBER_MISMATCH",
            f"parent_number {milestone.parent_number!r} does not match "
            f"number-derived parent {calculated_parent!r}",
            milestone=milestone,
            field="parent_number",
        ))

    if milestone.is_root and milestone.depth != ROOT_DEPTH:
        issues.append(_issue(
            "INVALID_ROOT_DEPTH",
            "root milestones must have depth 0",
            milestone=milestone,
            field="depth",
        ))

    if milestone.sequence < 1:
        issues.append(_issue(
            "INVALID_SEQUENCE",
            "sequence must be positive",
            milestone=milestone,
            field="sequence",
        ))

    path_parts = tuple(
        part.strip()
        for part in milestone.semantic_path.split(SEMANTIC_PATH_SEPARATOR)
    )
    if len(path_parts) != milestone.depth + 1:
        issues.append(_issue(
            "SEMANTIC_PATH_DEPTH_MISMATCH",
            f"semantic_path has {len(path_parts)} segment(s), expected "
            f"{milestone.depth + 1}",
            milestone=milestone,
            field="semantic_path",
        ))
    if path_parts and path_parts[-1] != milestone.title:
        issues.append(_issue(
            "SEMANTIC_PATH_TITLE_MISMATCH",
            "semantic_path must end with the milestone title",
            milestone=milestone,
            field="semantic_path",
        ))

    if allowed_statuses is not None:
        allowed = frozenset(normalize_status(value) for value in allowed_statuses)
        if milestone.status not in allowed:
            issues.append(_issue(
                "STATUS_NOT_ALLOWED",
                f"status {milestone.status.value!r} is not allowed",
                milestone=milestone,
                field="status",
            ))

    if len(set(milestone.dependencies)) != len(milestone.dependencies):
        issues.append(_issue(
            "DUPLICATE_DEPENDENCY",
            "dependencies contain duplicate values",
            milestone=milestone,
            field="dependencies",
        ))
    if milestone.number in milestone.dependencies:
        issues.append(_issue(
            "SELF_DEPENDENCY",
            "milestone cannot depend on itself",
            milestone=milestone,
            field="dependencies",
        ))

    if milestone.commit_hash is not None and not COMMIT_HASH_PATTERN.fullmatch(
        milestone.commit_hash
    ):
        issues.append(_issue(
            "INVALID_COMMIT_HASH",
            "commit_hash must contain 7 to 64 hexadecimal characters",
            milestone=milestone,
            field="commit_hash",
        ))

    if (
        require_commit_for_complete
        and milestone.status is RoadmapStatus.COMPLETED
        and milestone.commit_hash is None
    ):
        issues.append(_issue(
            "MISSING_COMPLETION_COMMIT",
            "completed milestones must include commit_hash",
            milestone=milestone,
            field="commit_hash",
        ))

    started, started_issues = _parse_date(
        milestone.started_date, "started_date", milestone
    )
    completed, completed_issues = _parse_date(
        milestone.completed_date, "completed_date", milestone
    )
    issues.extend(started_issues)
    issues.extend(completed_issues)

    if started and completed and completed < started:
        issues.append(_issue(
            "COMPLETION_BEFORE_START",
            "completed_date cannot be earlier than started_date",
            milestone=milestone,
            field="completed_date",
        ))

    if (
        require_completed_date_for_complete
        and milestone.status is RoadmapStatus.COMPLETED
        and milestone.completed_date is None
    ):
        issues.append(_issue(
            "MISSING_COMPLETED_DATE",
            "completed milestones must include completed_date",
            milestone=milestone,
            field="completed_date",
        ))

    if milestone.passing_tests is not None and milestone.passing_tests < 0:
        issues.append(_issue(
            "INVALID_PASSING_TESTS",
            "passing_tests cannot be negative",
            milestone=milestone,
            field="passing_tests",
        ))

    if (
        milestone.passing_tests is not None
        and milestone.passing_tests > 0
        and not milestone.test_information
    ):
        issues.append(_issue(
            "MISSING_TEST_INFORMATION",
            "positive passing_tests should include test_information",
            severity="WARNING",
            milestone=milestone,
            field="test_information",
        ))

    return ValidationReport(tuple(issues), records_checked=1)


def validate_metadata(metadata: RoadmapMetadata) -> ValidationReport:
    """Validate roadmap metadata."""

    if not isinstance(metadata, RoadmapMetadata):
        raise TypeError("metadata must be RoadmapMetadata")

    issues: list[ValidationIssue] = []

    if not metadata.title.strip():
        issues.append(_issue(
            "EMPTY_ROADMAP_TITLE",
            "roadmap title cannot be blank",
            field="title",
        ))
    if not metadata.version.strip():
        issues.append(_issue(
            "EMPTY_ROADMAP_VERSION",
            "roadmap version cannot be blank",
            field="version",
        ))

    def parse_boundary(
        value: str,
        field: str,
    ) -> tuple[str, date | tuple[int, ...] | None]:
        try:
            return "date", date.fromisoformat(value)
        except ValueError:
            if NUMBER_PATTERN.fullmatch(value):
                number_parts = tuple(
                    int(part) for part in value[1:].split(".")
                )
                return "number", number_parts
            issues.append(_issue(
                "INVALID_ROADMAP_BOUNDARY",
                f"{field} must be an ISO date or milestone number",
                field=field,
            ))
            return "invalid", None

    start_kind, start_value = parse_boundary(metadata.start, "start")
    end_kind, end_value = parse_boundary(metadata.end, "end")

    if (
        start_kind == end_kind
        and start_value is not None
        and end_value is not None
        and end_value < start_value
    ):
        issues.append(_issue(
            "ROADMAP_END_BEFORE_START",
            "roadmap end cannot be earlier than roadmap start",
            field="end",
        ))
    elif (
        start_kind != "invalid"
        and end_kind != "invalid"
        and start_kind != end_kind
    ):
        issues.append(_issue(
            "MIXED_ROADMAP_BOUNDARY_TYPES",
            "roadmap start and end must use the same boundary type",
            field="end",
        ))

    if not metadata.allowed_statuses:
        issues.append(_issue(
            "EMPTY_ALLOWED_STATUSES",
            "allowed_statuses cannot be empty",
            field="allowed_statuses",
        ))
    else:
        normalized = []
        for value in metadata.allowed_statuses:
            try:
                normalized.append(normalize_status(value))
            except (TypeError, ValueError):
                issues.append(_issue(
                    "INVALID_ALLOWED_STATUS",
                    f"Unsupported allowed status {value!r}",
                    field="allowed_statuses",
                ))
        if len(set(normalized)) != len(normalized):
            issues.append(_issue(
                "DUPLICATE_ALLOWED_STATUS",
                "allowed_statuses contains duplicate statuses",
                field="allowed_statuses",
            ))

    return ValidationReport(
        tuple(issues),
        metadata_checked=True,
    )


def validate_collection(
    source: MilestoneSource,
    *,
    allowed_statuses: Iterable[StatusLike] | None = None,
    require_contiguous_sequences: bool = True,
    require_parent_before_child: bool = True,
    validate_semantic_ancestry: bool = True,
    raise_on_error: bool = False,
) -> ValidationReport:
    """Validate a complete milestone collection."""

    records = all_milestones(source)
    issues: list[ValidationIssue] = []

    for item in records:
        issues.extend(validate_milestone(
            item,
            allowed_statuses=allowed_statuses,
        ).issues)

    number_counts = Counter(item.number for item in records)
    for number, count in number_counts.items():
        if count > 1:
            issues.append(_issue(
                "DUPLICATE_NUMBER",
                f"milestone number appears {count} times",
                number=number,
                field="number",
            ))

    record_id_counts = Counter(item.record_id for item in records)
    for record_id, count in record_id_counts.items():
        if count > 1:
            issues.append(_issue(
                "DUPLICATE_RECORD_ID",
                f"record_id appears {count} times",
                record_id=record_id,
                field="record_id",
            ))

    sequence_counts = Counter(item.sequence for item in records)
    for sequence, count in sequence_counts.items():
        if count > 1:
            issues.append(_issue(
                "DUPLICATE_SEQUENCE",
                f"sequence {sequence} appears {count} times",
                field="sequence",
            ))

    if require_contiguous_sequences and records:
        actual = sorted(sequence_counts)
        expected = list(range(min(actual), max(actual) + 1))
        if actual != expected:
            missing = sorted(set(expected) - set(actual))
            issues.append(_issue(
                "NON_CONTIGUOUS_SEQUENCE",
                "sequence values are not contiguous"
                + (f"; missing {missing[:10]}" if missing else ""),
                field="sequence",
            ))

    number_index = {item.number: item for item in records}
    for item in records:
        if item.parent_number is not None:
            parent = number_index.get(item.parent_number)
            if parent is None:
                issues.append(_issue(
                    "MISSING_PARENT",
                    f"parent milestone {item.parent_number!r} does not exist",
                    milestone=item,
                    field="parent_number",
                ))
                continue
            if parent.depth != item.depth - 1:
                issues.append(_issue(
                    "PARENT_DEPTH_MISMATCH",
                    "parent depth must be exactly one less than child depth",
                    milestone=item,
                    field="parent_number",
                ))
            if require_parent_before_child and parent.sequence >= item.sequence:
                issues.append(_issue(
                    "PARENT_AFTER_CHILD",
                    "parent sequence must precede child sequence",
                    milestone=item,
                    field="sequence",
                ))
            if validate_semantic_ancestry:
                expected_prefix = parent.semantic_path + SEMANTIC_PATH_SEPARATOR
                if not item.semantic_path.startswith(expected_prefix):
                    issues.append(_issue(
                        "SEMANTIC_PATH_PARENT_MISMATCH",
                        "child semantic_path must begin with its parent's path",
                        milestone=item,
                        field="semantic_path",
                    ))

    if all(count == 1 for count in number_counts.values()):
        dependency_result = validate_dependencies(records)
        for owner, dependency in dependency_result.missing_dependencies:
            issues.append(_issue(
                "MISSING_DEPENDENCY",
                f"dependency {dependency!r} does not exist",
                number=owner,
                field="dependencies",
            ))
        for owner, dependency in dependency_result.duplicate_dependencies:
            issues.append(_issue(
                "DUPLICATE_DEPENDENCY",
                f"dependency {dependency!r} is declared more than once",
                number=owner,
                field="dependencies",
            ))
        for number in dependency_result.self_dependencies:
            issues.append(_issue(
                "SELF_DEPENDENCY",
                "milestone cannot depend on itself",
                number=number,
                field="dependencies",
            ))
        for cycle in dependency_result.cycles:
            issues.append(_issue(
                "DEPENDENCY_CYCLE",
                "dependency cycle detected: " + " -> ".join(cycle),
                field="dependencies",
            ))
    else:
        issues.append(_issue(
            "DEPENDENCY_VALIDATION_SKIPPED",
            "dependency graph validation was skipped because milestone "
            "numbers are not unique",
            severity="WARNING",
            field="dependencies",
        ))

    report = ValidationReport(
        tuple(issues),
        records_checked=len(records),
    )
    if raise_on_error:
        report.raise_for_errors()
    return report


def validate_snapshot(
    snapshot: RoadmapSnapshot,
    *,
    raise_on_error: bool = False,
) -> ValidationReport:
    """Validate metadata and all milestones in a snapshot."""

    if not isinstance(snapshot, RoadmapSnapshot):
        raise TypeError("snapshot must be RoadmapSnapshot")

    metadata_report = validate_metadata(snapshot.metadata)
    collection_report = validate_collection(
        snapshot.milestones,
        allowed_statuses=snapshot.metadata.allowed_statuses,
    )
    report = ValidationReport(
        metadata_report.issues + collection_report.issues,
        records_checked=len(snapshot.milestones),
        metadata_checked=True,
    )
    if raise_on_error:
        report.raise_for_errors()
    return report


def validate_roadmap(
    source: MilestoneSource | RoadmapSnapshot,
    *,
    metadata: RoadmapMetadata | None = None,
    allowed_statuses: Iterable[StatusLike] | None = None,
    raise_on_error: bool = False,
) -> ValidationReport:
    """Unified validation entry point."""

    if isinstance(source, RoadmapSnapshot):
        return validate_snapshot(source, raise_on_error=raise_on_error)

    records = all_milestones(source)
    issues: list[ValidationIssue] = []
    metadata_checked = False

    if metadata is not None:
        metadata_report = validate_metadata(metadata)
        issues.extend(metadata_report.issues)
        metadata_checked = True
        if allowed_statuses is None:
            allowed_statuses = metadata.allowed_statuses

    collection_report = validate_collection(
        records,
        allowed_statuses=allowed_statuses,
    )
    issues.extend(collection_report.issues)

    report = ValidationReport(
        tuple(issues),
        records_checked=len(records),
        metadata_checked=metadata_checked,
    )
    if raise_on_error:
        report.raise_for_errors()
    return report


def assert_valid(
    source: MilestoneSource | RoadmapSnapshot,
    *,
    metadata: RoadmapMetadata | None = None,
    allowed_statuses: Iterable[StatusLike] | None = None,
) -> ValidationReport:
    """Validate and raise ``RoadmapValidationError`` on any error."""

    return validate_roadmap(
        source,
        metadata=metadata,
        allowed_statuses=allowed_statuses,
        raise_on_error=True,
    )


__all__ = (
    "COMMIT_HASH_PATTERN",
    "NUMBER_PATTERN",
    "RECORD_ID_PATTERN",
    "REQUIRED_MAPPING_FIELDS",
    "RoadmapValidationError",
    "SEMANTIC_PATH_SEPARATOR",
    "ValidationIssue",
    "ValidationReport",
    "assert_valid",
    "validate_collection",
    "validate_mapping",
    "validate_metadata",
    "validate_milestone",
    "validate_roadmap",
    "validate_snapshot",
)
