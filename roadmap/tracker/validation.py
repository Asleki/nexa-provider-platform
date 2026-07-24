"""
Boundary, reference, hierarchy and synchronization validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable

from .architecture import ArchitectureSnapshot
from .extensions import resolve_display_numbers, TrackerExtensionError
from .models import TrackerRecord, TrackerRecordKind


class TrackerValidationError(ValueError):
    def __init__(self, report: "TrackerValidationReport") -> None:
        self.report = report
        super().__init__(f"tracker validation failed with {len(report.errors)} error(s)")


@dataclass(frozen=True, slots=True)
class TrackerValidationReport:
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def raise_for_errors(self) -> None:
        if self.errors:
            raise TrackerValidationError(self)


def validate_records(
    architecture: ArchitectureSnapshot,
    records: Iterable[TrackerRecord],
) -> TrackerValidationReport:
    records = tuple(records)
    errors: list[str] = []
    ids = [item.tracker_id for item in records]
    if len(ids) != len(set(ids)):
        errors.append("duplicate tracker IDs detected")

    architecture_ids = set(architecture.by_record_id)
    for item in records:
        if item.architecture_record_id and item.architecture_record_id not in architecture_ids:
            errors.append(
                f"{item.tracker_id} references unknown architecture record "
                f"{item.architecture_record_id}"
            )

    try:
        resolve_display_numbers(architecture, records)
    except TrackerExtensionError as exc:
        errors.append(str(exc))

    return TrackerValidationReport(errors=tuple(errors))


def file_sha256(path: Path) -> str:
    return sha256(Path(path).read_bytes()).hexdigest()


def validate_synchronization(
    *,
    architecture: ArchitectureSnapshot,
    roadmap_path: Path,
    tracker_path: Path,
) -> TrackerValidationReport:
    errors: list[str] = []
    if not roadmap_path.exists():
        errors.append(f"missing roadmap output: {roadmap_path}")
    if not tracker_path.exists():
        errors.append(f"missing tracker output: {tracker_path}")
    if errors:
        return TrackerValidationReport(tuple(errors))

    text = tracker_path.read_text(encoding="utf-8")
    expected_arch = f"architecture_snapshot_sha256: {architecture.sha256}"
    expected_roadmap = f"roadmap_md_sha256: {file_sha256(roadmap_path)}"
    if expected_arch not in text:
        errors.append("ROADMAP_TRACKER.md uses a stale architecture snapshot")
    if expected_roadmap not in text:
        errors.append("ROADMAP_TRACKER.md uses a stale ROADMAP.md digest")
    return TrackerValidationReport(tuple(errors))
