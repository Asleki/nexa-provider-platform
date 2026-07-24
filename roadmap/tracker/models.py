"""
Immutable operational models for the NPP Roadmap Tracker Engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import PurePosixPath
from typing import Mapping, Any


class TrackerModelError(ValueError):
    """Base exception for invalid tracker data."""


class TrackerRecordKind(str, Enum):
    ARCHITECTURE = "ARCHITECTURE"
    EXTENSION = "EXTENSION"
    TRACKER_MILESTONE = "TRACKER_MILESTONE"


class TrackerStatus(str, Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    VALIDATED = "VALIDATED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class CommitEvidence:
    sha: str
    message: str
    committed_at: str
    author: str | None = None

    def __post_init__(self) -> None:
        sha = self.sha.strip().lower()
        if len(sha) < 7 or any(ch not in "0123456789abcdef" for ch in sha):
            raise TrackerModelError("commit sha must contain 7-64 hexadecimal characters")
        if len(sha) > 64:
            raise TrackerModelError("commit sha cannot exceed 64 characters")
        if not self.message.strip():
            raise TrackerModelError("commit message cannot be blank")
        _validate_timestamp(self.committed_at, "committed_at")
        object.__setattr__(self, "sha", sha)
        object.__setattr__(self, "message", self.message.strip())

    def to_mapping(self) -> dict[str, object]:
        return {
            "sha": self.sha,
            "message": self.message,
            "committed_at": self.committed_at,
            "author": self.author,
        }


@dataclass(frozen=True, slots=True)
class FileEvidence:
    path: str
    action: str
    owning_record_id: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        normalized = PurePosixPath(self.path.replace("\\", "/")).as_posix()
        if normalized in {"", "."} or normalized.startswith("../") or "/../" in normalized:
            raise TrackerModelError(f"unsafe tracker file path: {self.path!r}")
        action = self.action.strip().upper()
        if action not in {"CREATED", "MODIFIED", "DELETED", "RENAMED"}:
            raise TrackerModelError(f"unsupported file action: {self.action!r}")
        object.__setattr__(self, "path", normalized)
        object.__setattr__(self, "action", action)

    def to_mapping(self) -> dict[str, object]:
        return {
            "path": self.path,
            "action": self.action,
            "owning_record_id": self.owning_record_id,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class TrackerRecord:
    tracker_id: str
    kind: TrackerRecordKind
    title: str | None
    status: TrackerStatus
    created_at: str
    updated_at: str
    architecture_record_id: str | None = None
    parent_tracker_id: str | None = None
    local_segment: int | None = None
    display_number: str | None = None
    description: str | None = None
    commits: tuple[CommitEvidence, ...] = ()
    files: tuple[FileEvidence, ...] = ()
    tests: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.tracker_id.startswith("npp-trk-"):
            raise TrackerModelError("tracker_id must start with 'npp-trk-'")
        if not isinstance(self.kind, TrackerRecordKind):
            object.__setattr__(self, "kind", TrackerRecordKind(str(self.kind)))
        if not isinstance(self.status, TrackerStatus):
            object.__setattr__(self, "status", TrackerStatus(str(self.status)))
        _validate_timestamp(self.created_at, "created_at")
        _validate_timestamp(self.updated_at, "updated_at")

        if self.kind is TrackerRecordKind.ARCHITECTURE:
            if not self.architecture_record_id:
                raise TrackerModelError(
                    "architecture tracker records require architecture_record_id"
                )
            if self.title is not None:
                raise TrackerModelError(
                    "architecture titles must be fetched dynamically, not stored"
                )

        if self.kind is TrackerRecordKind.EXTENSION:
            if not self.architecture_record_id and not self.parent_tracker_id:
                raise TrackerModelError(
                    "extensions require an architecture or tracker parent"
                )
            if not self.title or not self.title.strip():
                raise TrackerModelError("extension title cannot be blank")
            if not isinstance(self.local_segment, int) or self.local_segment < 1:
                raise TrackerModelError(
                    "extensions require a positive local_segment"
                )

        if self.kind is TrackerRecordKind.TRACKER_MILESTONE:
            if not self.title or not self.title.strip():
                raise TrackerModelError("tracker milestone title cannot be blank")
            if not self.display_number or not self.display_number.strip():
                raise TrackerModelError(
                    "tracker milestones require a display_number"
                )

        if self.title is not None:
            object.__setattr__(self, "title", self.title.strip())
        object.__setattr__(self, "commits", tuple(self.commits))
        object.__setattr__(self, "files", tuple(self.files))
        object.__setattr__(self, "tests", tuple(str(x).strip() for x in self.tests if str(x).strip()))
        object.__setattr__(self, "notes", tuple(str(x).strip() for x in self.notes if str(x).strip()))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @classmethod
    def from_mapping(cls, source: Mapping[str, Any]) -> "TrackerRecord":
        return cls(
            tracker_id=str(source["tracker_id"]),
            kind=TrackerRecordKind(str(source["kind"])),
            title=source.get("title"),
            status=TrackerStatus(str(source.get("status", "PLANNED"))),
            created_at=str(source["created_at"]),
            updated_at=str(source["updated_at"]),
            architecture_record_id=source.get("architecture_record_id"),
            parent_tracker_id=source.get("parent_tracker_id"),
            local_segment=source.get("local_segment"),
            display_number=source.get("display_number"),
            description=source.get("description"),
            commits=tuple(
                CommitEvidence(**item) for item in source.get("commits", ())
            ),
            files=tuple(
                FileEvidence(**item) for item in source.get("files", ())
            ),
            tests=tuple(source.get("tests", ())),
            notes=tuple(source.get("notes", ())),
            metadata=source.get("metadata", {}),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "tracker_id": self.tracker_id,
            "kind": self.kind.value,
            "title": self.title,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "architecture_record_id": self.architecture_record_id,
            "parent_tracker_id": self.parent_tracker_id,
            "local_segment": self.local_segment,
            "display_number": self.display_number,
            "description": self.description,
            "commits": [item.to_mapping() for item in self.commits],
            "files": [item.to_mapping() for item in self.files],
            "tests": list(self.tests),
            "notes": list(self.notes),
            "metadata": dict(self.metadata),
        }


def _validate_timestamp(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise TrackerModelError(f"{field_name} cannot be blank")
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise TrackerModelError(
            f"{field_name} must be an ISO-8601 timestamp"
        ) from exc
    if parsed.tzinfo is None:
        raise TrackerModelError(f"{field_name} must include a timezone offset")
