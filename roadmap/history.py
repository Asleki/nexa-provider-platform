"""
Immutable roadmap history, change tracking, and snapshot comparison.

This module records deterministic milestone history entries without mutating
the canonical roadmap dataset. It supports snapshot creation, field-level
diffs, append-only histories, timeline queries, status transition analysis,
serialization, replay, and SHA-256 integrity checks.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

from .models import Milestone, RoadmapSnapshot
from .queries import MilestoneSource, all_milestones, build_number_index
from .statuses import RoadmapStatus, StatusLike, normalize_status


class RoadmapHistoryError(ValueError):
    """Base exception for roadmap history failures."""


class DuplicateHistoryEntryError(RoadmapHistoryError):
    """Raised when a history contains duplicate entry identifiers."""


class InvalidHistoryTransitionError(RoadmapHistoryError):
    """Raised when an invalid milestone transition is recorded."""


class HistoryIntegrityError(RoadmapHistoryError):
    """Raised when a history checksum does not match its contents."""


_TRACKED_FIELDS = (
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
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _require_aware_datetime(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise RoadmapHistoryError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _json_safe(value: Any) -> Any:
    if isinstance(value, RoadmapStatus):
        return value.value
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _freeze_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if value is None:
        return MappingProxyType({})
    return MappingProxyType({
        str(key): _freeze_value(item)
        for key, item in value.items()
    })


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({
            str(key): _freeze_value(item)
            for key, item in value.items()
        })
    if isinstance(value, list):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze_value(item) for item in value)
    return value


def _milestone_state(milestone: Milestone) -> dict[str, Any]:
    if not isinstance(milestone, Milestone):
        raise TypeError("milestone must be a Milestone")
    mapping = milestone.to_mapping(include_metadata=False)
    return {
        key: _json_safe(mapping[key])
        for key in _TRACKED_FIELDS
    }


def _canonical_json(value: Any) -> str:
    return json.dumps(
        _json_safe(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _hash_payload(value: Any) -> str:
    return hashlib.sha256(
        _canonical_json(value).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class FieldChange:
    """One immutable field-level change."""

    field_name: str
    before: Any
    after: Any

    def __post_init__(self) -> None:
        if not isinstance(self.field_name, str) or not self.field_name.strip():
            raise RoadmapHistoryError("field_name cannot be blank")
        object.__setattr__(self, "before", _freeze_value(self.before))
        object.__setattr__(self, "after", _freeze_value(self.after))
        if self.before == self.after:
            raise RoadmapHistoryError(
                "FieldChange requires different before and after values"
            )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "before": _json_safe(self.before),
            "after": _json_safe(self.after),
        }


@dataclass(frozen=True, slots=True)
class MilestoneHistoryEntry:
    """One append-only milestone history entry."""

    entry_id: str
    milestone_number: str
    record_id: str
    occurred_at: datetime
    actor: str
    action: str
    changes: tuple[FieldChange, ...]
    before_checksum: str | None
    after_checksum: str
    metadata: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        for name in ("entry_id", "milestone_number", "record_id", "actor", "action"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise RoadmapHistoryError(f"{name} cannot be blank")
        object.__setattr__(
            self,
            "occurred_at",
            _require_aware_datetime(self.occurred_at, "occurred_at"),
        )
        changes = tuple(self.changes)
        if not all(isinstance(item, FieldChange) for item in changes):
            raise TypeError("changes must contain only FieldChange instances")
        object.__setattr__(self, "changes", changes)
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))
        for checksum_name in ("before_checksum", "after_checksum"):
            checksum = getattr(self, checksum_name)
            if checksum is None and checksum_name == "before_checksum":
                continue
            if (
                not isinstance(checksum, str)
                or len(checksum) != 64
                or any(char not in "0123456789abcdef" for char in checksum)
            ):
                raise RoadmapHistoryError(
                    f"{checksum_name} must be a lowercase SHA-256 hex digest"
                )

    @property
    def changed_fields(self) -> tuple[str, ...]:
        return tuple(change.field_name for change in self.changes)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "milestone_number": self.milestone_number,
            "record_id": self.record_id,
            "occurred_at": self.occurred_at.isoformat(),
            "actor": self.actor,
            "action": self.action,
            "changes": [item.to_mapping() for item in self.changes],
            "before_checksum": self.before_checksum,
            "after_checksum": self.after_checksum,
            "metadata": _json_safe(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class RoadmapHistory:
    """Immutable append-only collection of history entries."""

    entries: tuple[MilestoneHistoryEntry, ...] = ()

    def __post_init__(self) -> None:
        entries = tuple(self.entries)
        if not all(isinstance(item, MilestoneHistoryEntry) for item in entries):
            raise TypeError(
                "entries must contain only MilestoneHistoryEntry instances"
            )
        ids = [item.entry_id for item in entries]
        if len(ids) != len(set(ids)):
            raise DuplicateHistoryEntryError(
                "history entry identifiers must be unique"
            )
        ordered = tuple(sorted(
            entries,
            key=lambda item: (
                item.occurred_at,
                item.entry_id,
            ),
        ))
        object.__setattr__(self, "entries", ordered)

    @property
    def total(self) -> int:
        return len(self.entries)

    @property
    def checksum(self) -> str:
        return _hash_payload([item.to_mapping() for item in self.entries])

    def append(self, entry: MilestoneHistoryEntry) -> "RoadmapHistory":
        if not isinstance(entry, MilestoneHistoryEntry):
            raise TypeError("entry must be MilestoneHistoryEntry")
        return RoadmapHistory(self.entries + (entry,))

    def extend(
        self,
        entries: Iterable[MilestoneHistoryEntry],
    ) -> "RoadmapHistory":
        return RoadmapHistory(self.entries + tuple(entries))

    def by_milestone(
        self,
        milestone_number: str,
    ) -> tuple[MilestoneHistoryEntry, ...]:
        return tuple(
            item
            for item in self.entries
            if item.milestone_number == milestone_number
        )

    def by_actor(self, actor: str) -> tuple[MilestoneHistoryEntry, ...]:
        return tuple(item for item in self.entries if item.actor == actor)

    def by_action(self, action: str) -> tuple[MilestoneHistoryEntry, ...]:
        return tuple(item for item in self.entries if item.action == action)

    def between(
        self,
        start: datetime,
        end: datetime,
    ) -> tuple[MilestoneHistoryEntry, ...]:
        start_utc = _require_aware_datetime(start, "start")
        end_utc = _require_aware_datetime(end, "end")
        if end_utc < start_utc:
            raise RoadmapHistoryError("end cannot be earlier than start")
        return tuple(
            item
            for item in self.entries
            if start_utc <= item.occurred_at <= end_utc
        )

    def latest_for(
        self,
        milestone_number: str,
    ) -> MilestoneHistoryEntry | None:
        matches = self.by_milestone(milestone_number)
        return matches[-1] if matches else None

    def to_mapping(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "checksum": self.checksum,
            "entries": [item.to_mapping() for item in self.entries],
        }


@dataclass(frozen=True, slots=True)
class SnapshotDiff:
    """Difference between two roadmap snapshots or milestone collections."""

    added: tuple[Milestone, ...]
    removed: tuple[Milestone, ...]
    changed: Mapping[str, tuple[FieldChange, ...]]
    unchanged: tuple[Milestone, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "added", tuple(self.added))
        object.__setattr__(self, "removed", tuple(self.removed))
        object.__setattr__(self, "unchanged", tuple(self.unchanged))
        object.__setattr__(
            self,
            "changed",
            MappingProxyType({
                str(key): tuple(value)
                for key, value in self.changed.items()
            }),
        )

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    @property
    def total_changed_records(self) -> int:
        return len(self.added) + len(self.removed) + len(self.changed)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "added": [item.number for item in self.added],
            "removed": [item.number for item in self.removed],
            "changed": {
                number: [change.to_mapping() for change in changes]
                for number, changes in self.changed.items()
            },
            "unchanged": [item.number for item in self.unchanged],
            "has_changes": self.has_changes,
            "total_changed_records": self.total_changed_records,
        }


def milestone_checksum(milestone: Milestone) -> str:
    """Return the canonical checksum of one milestone's tracked state."""

    return _hash_payload(_milestone_state(milestone))


def diff_milestones(
    before: Milestone,
    after: Milestone,
) -> tuple[FieldChange, ...]:
    """Return deterministic field-level differences."""

    if before.number != after.number:
        raise InvalidHistoryTransitionError(
            "cannot diff milestones with different numbers"
        )
    if before.record_id != after.record_id:
        raise InvalidHistoryTransitionError(
            "cannot diff milestones with different record IDs"
        )

    before_state = _milestone_state(before)
    after_state = _milestone_state(after)

    return tuple(
        FieldChange(
            field_name=field_name,
            before=before_state[field_name],
            after=after_state[field_name],
        )
        for field_name in _TRACKED_FIELDS
        if before_state[field_name] != after_state[field_name]
    )


def create_history_entry(
    after: Milestone,
    *,
    before: Milestone | None = None,
    actor: str = "system",
    action: str | None = None,
    occurred_at: datetime | None = None,
    metadata: Mapping[str, Any] | None = None,
    entry_id: str | None = None,
) -> MilestoneHistoryEntry:
    """Create a deterministic, integrity-protected history entry."""

    if before is not None:
        changes = diff_milestones(before, after)
        before_checksum = milestone_checksum(before)
        inferred_action = "updated"
    else:
        changes = tuple(
            FieldChange(field_name=key, before=None, after=value)
            for key, value in _milestone_state(after).items()
            if value not in (None, [], "")
        )
        before_checksum = None
        inferred_action = "created"

    timestamp = _require_aware_datetime(
        occurred_at or _utc_now(),
        "occurred_at",
    )
    after_checksum = milestone_checksum(after)
    resolved_action = action or inferred_action

    payload = {
        "milestone_number": after.number,
        "record_id": after.record_id,
        "occurred_at": timestamp.isoformat(),
        "actor": actor,
        "action": resolved_action,
        "changes": [item.to_mapping() for item in changes],
        "before_checksum": before_checksum,
        "after_checksum": after_checksum,
        "metadata": _json_safe(metadata or {}),
    }
    resolved_entry_id = entry_id or _hash_payload(payload)

    return MilestoneHistoryEntry(
        entry_id=resolved_entry_id,
        milestone_number=after.number,
        record_id=after.record_id,
        occurred_at=timestamp,
        actor=actor,
        action=resolved_action,
        changes=changes,
        before_checksum=before_checksum,
        after_checksum=after_checksum,
        metadata=metadata or {},
    )


def snapshot_diff(
    before: MilestoneSource | RoadmapSnapshot,
    after: MilestoneSource | RoadmapSnapshot,
) -> SnapshotDiff:
    """Compare two roadmap states by milestone number."""

    before_records = (
        before.milestones if isinstance(before, RoadmapSnapshot)
        else all_milestones(before)
    )
    after_records = (
        after.milestones if isinstance(after, RoadmapSnapshot)
        else all_milestones(after)
    )

    before_index = build_number_index(before_records)
    after_index = build_number_index(after_records)

    added_numbers = sorted(
        set(after_index) - set(before_index),
        key=lambda number: after_index[number].sequence,
    )
    removed_numbers = sorted(
        set(before_index) - set(after_index),
        key=lambda number: before_index[number].sequence,
    )

    changed: dict[str, tuple[FieldChange, ...]] = {}
    unchanged: list[Milestone] = []

    common_numbers = sorted(
        set(before_index) & set(after_index),
        key=lambda number: after_index[number].sequence,
    )
    for number in common_numbers:
        differences = diff_milestones(
            before_index[number],
            after_index[number],
        )
        if differences:
            changed[number] = differences
        else:
            unchanged.append(after_index[number])

    return SnapshotDiff(
        added=tuple(after_index[number] for number in added_numbers),
        removed=tuple(before_index[number] for number in removed_numbers),
        changed=changed,
        unchanged=tuple(unchanged),
    )


def history_from_snapshots(
    before: MilestoneSource | RoadmapSnapshot,
    after: MilestoneSource | RoadmapSnapshot,
    *,
    actor: str = "system",
    occurred_at: datetime | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> RoadmapHistory:
    """Build history entries representing the transition between snapshots."""

    timestamp = occurred_at or _utc_now()
    before_records = (
        before.milestones if isinstance(before, RoadmapSnapshot)
        else all_milestones(before)
    )
    after_records = (
        after.milestones if isinstance(after, RoadmapSnapshot)
        else all_milestones(after)
    )
    before_index = build_number_index(before_records)
    after_index = build_number_index(after_records)
    diff = snapshot_diff(before_records, after_records)

    entries: list[MilestoneHistoryEntry] = []

    for item in diff.added:
        entries.append(create_history_entry(
            item,
            actor=actor,
            action="created",
            occurred_at=timestamp,
            metadata=metadata,
        ))

    for number in diff.changed:
        entries.append(create_history_entry(
            after_index[number],
            before=before_index[number],
            actor=actor,
            action="updated",
            occurred_at=timestamp,
            metadata=metadata,
        ))

    for item in diff.removed:
        payload = {
            "milestone_number": item.number,
            "record_id": item.record_id,
            "occurred_at": _require_aware_datetime(
                timestamp,
                "occurred_at",
            ).isoformat(),
            "actor": actor,
            "action": "removed",
            "changes": [],
            "before_checksum": milestone_checksum(item),
            "after_checksum": milestone_checksum(item),
            "metadata": _json_safe(metadata or {}),
        }
        entries.append(MilestoneHistoryEntry(
            entry_id=_hash_payload(payload),
            milestone_number=item.number,
            record_id=item.record_id,
            occurred_at=timestamp,
            actor=actor,
            action="removed",
            changes=(),
            before_checksum=milestone_checksum(item),
            after_checksum=milestone_checksum(item),
            metadata=metadata or {},
        ))

    return RoadmapHistory(tuple(entries))


def status_transitions(
    history: RoadmapHistory,
    *,
    milestone_number: str | None = None,
) -> tuple[tuple[str, str, str, datetime], ...]:
    """Return status transitions as number, before, after, timestamp."""

    if not isinstance(history, RoadmapHistory):
        raise TypeError("history must be RoadmapHistory")
    transitions: list[tuple[str, str, str, datetime]] = []
    for entry in history.entries:
        if (
            milestone_number is not None
            and entry.milestone_number != milestone_number
        ):
            continue
        for change in entry.changes:
            if change.field_name == "status":
                transitions.append((
                    entry.milestone_number,
                    str(change.before),
                    str(change.after),
                    entry.occurred_at,
                ))
    return tuple(transitions)


def count_transitions(
    history: RoadmapHistory,
) -> Mapping[tuple[str, str], int]:
    """Count status transition pairs."""

    counts: dict[tuple[str, str], int] = {}
    for _, before, after, _ in status_transitions(history):
        key = (before, after)
        counts[key] = counts.get(key, 0) + 1
    return MappingProxyType(counts)


def serialize_history(
    history: RoadmapHistory,
    *,
    indent: int = 2,
) -> str:
    """Serialize history to deterministic JSON."""

    if not isinstance(history, RoadmapHistory):
        raise TypeError("history must be RoadmapHistory")
    return json.dumps(
        history.to_mapping(),
        indent=indent,
        ensure_ascii=False,
        sort_keys=False,
    ) + "\n"


def deserialize_history(text: str) -> RoadmapHistory:
    """Deserialize and validate history JSON."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    payload = json.loads(text)
    entries: list[MilestoneHistoryEntry] = []

    for item in payload.get("entries", []):
        changes = tuple(
            FieldChange(
                field_name=change["field_name"],
                before=change.get("before"),
                after=change.get("after"),
            )
            for change in item.get("changes", [])
        )
        entries.append(MilestoneHistoryEntry(
            entry_id=item["entry_id"],
            milestone_number=item["milestone_number"],
            record_id=item["record_id"],
            occurred_at=datetime.fromisoformat(item["occurred_at"]),
            actor=item["actor"],
            action=item["action"],
            changes=changes,
            before_checksum=item.get("before_checksum"),
            after_checksum=item["after_checksum"],
            metadata=item.get("metadata", {}),
        ))

    history = RoadmapHistory(tuple(entries))
    expected = payload.get("checksum")
    if expected is not None and expected != history.checksum:
        raise HistoryIntegrityError(
            "history checksum does not match serialized contents"
        )
    return history


def verify_history_integrity(history: RoadmapHistory) -> bool:
    """Validate all entry and collection checksums structurally."""

    if not isinstance(history, RoadmapHistory):
        raise TypeError("history must be RoadmapHistory")
    if len({entry.entry_id for entry in history.entries}) != history.total:
        return False
    for entry in history.entries:
        if len(entry.after_checksum) != 64:
            return False
        if entry.before_checksum is not None and len(entry.before_checksum) != 64:
            return False
    return history.checksum == _hash_payload(
        [entry.to_mapping() for entry in history.entries]
    )


__all__ = (
    "DuplicateHistoryEntryError",
    "FieldChange",
    "HistoryIntegrityError",
    "InvalidHistoryTransitionError",
    "MilestoneHistoryEntry",
    "RoadmapHistory",
    "RoadmapHistoryError",
    "SnapshotDiff",
    "count_transitions",
    "create_history_entry",
    "deserialize_history",
    "diff_milestones",
    "history_from_snapshots",
    "milestone_checksum",
    "serialize_history",
    "snapshot_diff",
    "status_transitions",
    "verify_history_integrity",
)
