"""
Roadmap progress calculation utilities for the Nexa Provider Platform.

This module derives immutable progress metrics from ``Milestone`` records and
``RoadmapSnapshot`` objects. It never mutates canonical roadmap data.

Default completion uses the canonical ``COMPLETE_STATUSES`` set from
``roadmap.statuses``: COMPLETED and RELEASED.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from types import MappingProxyType
from typing import Final, Iterable, Mapping, TypeAlias

from .models import Milestone, RoadmapSnapshot
from .queries import MilestoneSource, all_milestones, get_descendants, get_roots
from .statuses import (
    ACTIVE_STATUSES,
    COMPLETE_STATUSES,
    OPEN_STATUSES,
    RoadmapStatus,
    StatusLike,
    normalize_status,
)


DEFAULT_PERCENTAGE_PLACES: Final[int] = 2
PERCENT_BASE: Final[Decimal] = Decimal("100")


class RoadmapProgressError(ValueError):
    """Base exception for invalid roadmap progress calculations."""


class InvalidWeightError(RoadmapProgressError):
    """Raised when a milestone weight is missing or invalid."""


@dataclass(frozen=True, slots=True)
class ProgressCounts:
    """Immutable aggregate counts for one roadmap scope."""

    total: int
    complete: int
    active: int
    open: int
    blocked: int
    planned: int
    deprecated: int

    def __post_init__(self) -> None:
        values = (
            self.total,
            self.complete,
            self.active,
            self.open,
            self.blocked,
            self.planned,
            self.deprecated,
        )
        if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
            raise TypeError("progress counts must be integers")
        if any(value < 0 for value in values):
            raise RoadmapProgressError("progress counts cannot be negative")
        if self.complete > self.total:
            raise RoadmapProgressError("complete count cannot exceed total")
        if self.active > self.total:
            raise RoadmapProgressError("active count cannot exceed total")
        if self.open > self.total:
            raise RoadmapProgressError("open count cannot exceed total")

    @property
    def incomplete(self) -> int:
        """Return records not in a complete status."""

        return self.total - self.complete

    @property
    def remaining(self) -> int:
        """Alias for incomplete records."""

        return self.incomplete


@dataclass(frozen=True, slots=True)
class ProgressSummary:
    """Immutable progress result for a roadmap scope."""

    counts: ProgressCounts
    percentage: Decimal
    status_counts: Mapping[RoadmapStatus, int]
    passing_tests: int
    milestones_with_tests: int
    started_milestones: int
    completed_milestones_with_dates: int

    def __post_init__(self) -> None:
        if not isinstance(self.percentage, Decimal):
            raise TypeError("percentage must be Decimal")
        if self.percentage < 0 or self.percentage > PERCENT_BASE:
            raise RoadmapProgressError("percentage must be between 0 and 100")
        for field_name in (
            "passing_tests",
            "milestones_with_tests",
            "started_milestones",
            "completed_milestones_with_dates",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field_name} must be an integer")
            if value < 0:
                raise RoadmapProgressError(f"{field_name} cannot be negative")
        object.__setattr__(
            self,
            "status_counts",
            MappingProxyType(dict(self.status_counts)),
        )

    @property
    def total(self) -> int:
        return self.counts.total

    @property
    def complete(self) -> int:
        return self.counts.complete

    @property
    def incomplete(self) -> int:
        return self.counts.incomplete

    @property
    def is_complete(self) -> bool:
        return self.total > 0 and self.complete == self.total

    @property
    def is_empty(self) -> bool:
        return self.total == 0

    def to_mapping(self) -> dict[str, object]:
        """Serialize the summary into plain Python values."""

        return {
            "total": self.total,
            "complete": self.complete,
            "incomplete": self.incomplete,
            "active": self.counts.active,
            "open": self.counts.open,
            "blocked": self.counts.blocked,
            "planned": self.counts.planned,
            "deprecated": self.counts.deprecated,
            "percentage": float(self.percentage),
            "status_counts": {
                status.value: count
                for status, count in self.status_counts.items()
            },
            "passing_tests": self.passing_tests,
            "milestones_with_tests": self.milestones_with_tests,
            "started_milestones": self.started_milestones,
            "completed_milestones_with_dates": (
                self.completed_milestones_with_dates
            ),
        }


@dataclass(frozen=True, slots=True)
class WeightedProgress:
    """Immutable weighted completion result."""

    total_weight: Decimal
    completed_weight: Decimal
    percentage: Decimal
    milestone_count: int

    def __post_init__(self) -> None:
        if self.total_weight < 0 or self.completed_weight < 0:
            raise InvalidWeightError("weights cannot be negative")
        if self.completed_weight > self.total_weight:
            raise InvalidWeightError(
                "completed weight cannot exceed total weight"
            )
        if self.percentage < 0 or self.percentage > PERCENT_BASE:
            raise RoadmapProgressError("percentage must be between 0 and 100")
        if (
            isinstance(self.milestone_count, bool)
            or not isinstance(self.milestone_count, int)
            or self.milestone_count < 0
        ):
            raise RoadmapProgressError(
                "milestone_count must be a non-negative integer"
            )


def _validate_places(places: int) -> int:
    if isinstance(places, bool) or not isinstance(places, int):
        raise TypeError("places must be an integer")
    if places < 0:
        raise RoadmapProgressError("places cannot be negative")
    return places


def _quantizer(places: int) -> Decimal:
    return Decimal("1").scaleb(-_validate_places(places))


def percentage(
    completed: int | Decimal,
    total: int | Decimal,
    *,
    places: int = DEFAULT_PERCENTAGE_PLACES,
) -> Decimal:
    """
    Calculate a percentage using deterministic Decimal arithmetic.

    Empty totals return Decimal("0") rather than raising division-by-zero.
    """

    completed_value = Decimal(str(completed))
    total_value = Decimal(str(total))

    if completed_value < 0 or total_value < 0:
        raise RoadmapProgressError(
            "completed and total values cannot be negative"
        )
    if completed_value > total_value:
        raise RoadmapProgressError(
            "completed value cannot exceed total value"
        )
    if total_value == 0:
        return Decimal("0").quantize(_quantizer(places))

    result = (completed_value / total_value) * PERCENT_BASE
    return result.quantize(_quantizer(places), rounding=ROUND_HALF_UP)


def completion_count(
    source: MilestoneSource,
    *,
    complete_statuses: Iterable[StatusLike] = COMPLETE_STATUSES,
) -> int:
    """Count milestones considered complete."""

    accepted = frozenset(normalize_status(value) for value in complete_statuses)
    return sum(
        1 for milestone in all_milestones(source)
        if milestone.status in accepted
    )


def completion_percentage(
    source: MilestoneSource,
    *,
    complete_statuses: Iterable[StatusLike] = COMPLETE_STATUSES,
    places: int = DEFAULT_PERCENTAGE_PLACES,
) -> Decimal:
    """Calculate completion percentage for a roadmap scope."""

    records = all_milestones(source)
    return percentage(
        completion_count(records, complete_statuses=complete_statuses),
        len(records),
        places=places,
    )


def progress_counts(
    source: MilestoneSource,
    *,
    complete_statuses: Iterable[StatusLike] = COMPLETE_STATUSES,
) -> ProgressCounts:
    """Calculate aggregate lifecycle counts."""

    records = all_milestones(source)
    accepted_complete = frozenset(
        normalize_status(value) for value in complete_statuses
    )

    return ProgressCounts(
        total=len(records),
        complete=sum(item.status in accepted_complete for item in records),
        active=sum(item.status in ACTIVE_STATUSES for item in records),
        open=sum(item.status in OPEN_STATUSES for item in records),
        blocked=sum(
            item.status is RoadmapStatus.BLOCKED for item in records
        ),
        planned=sum(
            item.status is RoadmapStatus.PLANNED for item in records
        ),
        deprecated=sum(
            item.status is RoadmapStatus.DEPRECATED for item in records
        ),
    )


def summarize_progress(
    source: MilestoneSource,
    *,
    complete_statuses: Iterable[StatusLike] = COMPLETE_STATUSES,
    places: int = DEFAULT_PERCENTAGE_PLACES,
) -> ProgressSummary:
    """Build a complete immutable progress summary."""

    records = all_milestones(source)
    counts = progress_counts(
        records,
        complete_statuses=complete_statuses,
    )
    status_counts = Counter(item.status for item in records)

    return ProgressSummary(
        counts=counts,
        percentage=percentage(
            counts.complete,
            counts.total,
            places=places,
        ),
        status_counts=status_counts,
        passing_tests=sum(
            item.passing_tests or 0 for item in records
        ),
        milestones_with_tests=sum(
            item.passing_tests is not None for item in records
        ),
        started_milestones=sum(
            item.started_date is not None for item in records
        ),
        completed_milestones_with_dates=sum(
            item.completed_date is not None for item in records
        ),
    )


def progress_by_status(
    source: MilestoneSource,
) -> Mapping[RoadmapStatus, int]:
    """Return immutable status counts."""

    return MappingProxyType(
        dict(Counter(item.status for item in all_milestones(source)))
    )


def progress_by_depth(
    source: MilestoneSource,
    *,
    places: int = DEFAULT_PERCENTAGE_PLACES,
) -> Mapping[int, ProgressSummary]:
    """Return progress summaries grouped by hierarchy depth."""

    grouped: dict[int, list[Milestone]] = defaultdict(list)
    for item in all_milestones(source):
        grouped[item.depth].append(item)
    return MappingProxyType({
        depth: summarize_progress(items, places=places)
        for depth, items in sorted(grouped.items())
    })


def progress_by_priority(
    source: MilestoneSource,
    *,
    places: int = DEFAULT_PERCENTAGE_PLACES,
) -> Mapping[str | None, ProgressSummary]:
    """Return progress summaries grouped by priority."""

    grouped: dict[str | None, list[Milestone]] = defaultdict(list)
    for item in all_milestones(source):
        grouped[item.priority].append(item)
    return MappingProxyType({
        priority: summarize_progress(items, places=places)
        for priority, items in grouped.items()
    })


def progress_by_parent(
    source: MilestoneSource,
    *,
    include_parent: bool = True,
    places: int = DEFAULT_PERCENTAGE_PLACES,
) -> Mapping[str, ProgressSummary]:
    """
    Calculate progress for every root milestone subtree.

    By default the root milestone itself is included in its subtree.
    """

    records = all_milestones(source)
    results: dict[str, ProgressSummary] = {}
    for root in get_roots(records):
        subtree = get_descendants(
            records,
            root,
            include_self=include_parent,
        )
        results[root.number] = summarize_progress(
            subtree,
            places=places,
        )
    return MappingProxyType(results)


def progress_for_milestone(
    source: MilestoneSource,
    milestone: Milestone | str,
    *,
    include_self: bool = True,
    places: int = DEFAULT_PERCENTAGE_PLACES,
) -> ProgressSummary:
    """Calculate progress for one milestone and all descendants."""

    records = all_milestones(source)
    subtree = get_descendants(
        records,
        milestone,
        include_self=include_self,
    )
    return summarize_progress(subtree, places=places)


def completed_milestones(
    source: MilestoneSource,
    *,
    complete_statuses: Iterable[StatusLike] = COMPLETE_STATUSES,
) -> tuple[Milestone, ...]:
    """Return milestones considered complete."""

    accepted = frozenset(normalize_status(value) for value in complete_statuses)
    return tuple(
        item for item in all_milestones(source)
        if item.status in accepted
    )


def incomplete_milestones(
    source: MilestoneSource,
    *,
    complete_statuses: Iterable[StatusLike] = COMPLETE_STATUSES,
) -> tuple[Milestone, ...]:
    """Return milestones not considered complete."""

    accepted = frozenset(normalize_status(value) for value in complete_statuses)
    return tuple(
        item for item in all_milestones(source)
        if item.status not in accepted
    )


def active_milestones(
    source: MilestoneSource,
) -> tuple[Milestone, ...]:
    """Return milestones in active execution statuses."""

    return tuple(
        item for item in all_milestones(source)
        if item.status in ACTIVE_STATUSES
    )


def blocked_milestones(
    source: MilestoneSource,
) -> tuple[Milestone, ...]:
    """Return blocked milestones."""

    return tuple(
        item for item in all_milestones(source)
        if item.status is RoadmapStatus.BLOCKED
    )


def next_incomplete(
    source: MilestoneSource,
    *,
    limit: int | None = None,
    complete_statuses: Iterable[StatusLike] = COMPLETE_STATUSES,
) -> tuple[Milestone, ...]:
    """Return incomplete milestones in canonical sequence order."""

    if limit is not None:
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be an integer or None")
        if limit < 0:
            raise RoadmapProgressError("limit cannot be negative")

    records = sorted(
        incomplete_milestones(
            source,
            complete_statuses=complete_statuses,
        ),
        key=lambda item: (item.sequence, item.number),
    )
    if limit is not None:
        records = records[:limit]
    return tuple(records)


def weighted_progress(
    source: MilestoneSource,
    *,
    weights: Mapping[str, int | float | Decimal] | None = None,
    default_weight: int | float | Decimal = 1,
    complete_statuses: Iterable[StatusLike] = COMPLETE_STATUSES,
    places: int = DEFAULT_PERCENTAGE_PLACES,
    strict: bool = False,
) -> WeightedProgress:
    """
    Calculate weighted completion using stable ``record_id`` keys.

    When ``strict`` is true, every milestone must have an explicit weight.
    """

    records = all_milestones(source)
    accepted = frozenset(normalize_status(value) for value in complete_statuses)
    supplied = weights or {}
    default = Decimal(str(default_weight))

    if default < 0:
        raise InvalidWeightError("default_weight cannot be negative")

    total_weight = Decimal("0")
    completed_weight = Decimal("0")

    for item in records:
        if strict and item.record_id not in supplied:
            raise InvalidWeightError(
                f"Missing weight for record_id {item.record_id!r}"
            )
        raw_weight = supplied.get(item.record_id, default)
        try:
            weight = Decimal(str(raw_weight))
        except Exception as exc:
            raise InvalidWeightError(
                f"Invalid weight for record_id {item.record_id!r}"
            ) from exc
        if weight < 0:
            raise InvalidWeightError(
                f"Weight cannot be negative for {item.record_id!r}"
            )

        total_weight += weight
        if item.status in accepted:
            completed_weight += weight

    return WeightedProgress(
        total_weight=total_weight,
        completed_weight=completed_weight,
        percentage=percentage(
            completed_weight,
            total_weight,
            places=places,
        ),
        milestone_count=len(records),
    )


def format_progress(
    summary: ProgressSummary,
    *,
    width: int = 20,
    complete_character: str = "#",
    remaining_character: str = "-",
) -> str:
    """Render a deterministic plain-text progress bar."""

    if not isinstance(summary, ProgressSummary):
        raise TypeError("summary must be a ProgressSummary")
    if isinstance(width, bool) or not isinstance(width, int):
        raise TypeError("width must be an integer")
    if width <= 0:
        raise RoadmapProgressError("width must be greater than zero")
    if len(complete_character) != 1 or len(remaining_character) != 1:
        raise RoadmapProgressError(
            "progress bar characters must each be one character"
        )

    fraction = summary.percentage / PERCENT_BASE
    filled = int(
        (fraction * Decimal(width)).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )
    filled = min(width, max(0, filled))
    bar = (
        complete_character * filled
        + remaining_character * (width - filled)
    )
    return (
        f"[{bar}] {summary.percentage}% "
        f"({summary.complete}/{summary.total})"
    )


__all__ = (
    "DEFAULT_PERCENTAGE_PLACES",
    "InvalidWeightError",
    "PERCENT_BASE",
    "ProgressCounts",
    "ProgressSummary",
    "RoadmapProgressError",
    "WeightedProgress",
    "active_milestones",
    "blocked_milestones",
    "completed_milestones",
    "completion_count",
    "completion_percentage",
    "format_progress",
    "incomplete_milestones",
    "next_incomplete",
    "percentage",
    "progress_by_depth",
    "progress_by_parent",
    "progress_by_priority",
    "progress_by_status",
    "progress_counts",
    "progress_for_milestone",
    "summarize_progress",
    "weighted_progress",
)
