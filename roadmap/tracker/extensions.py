"""
Tracker-only extension numbering and hierarchy resolution.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping

from .architecture import ArchitectureSnapshot
from .models import TrackerRecord, TrackerRecordKind


class TrackerExtensionError(ValueError):
    """Raised when tracker-only hierarchy is invalid."""


def resolve_display_numbers(
    architecture: ArchitectureSnapshot,
    records: Iterable[TrackerRecord],
) -> Mapping[str, str]:
    records = tuple(records)
    by_id = {item.tracker_id: item for item in records}
    resolved: dict[str, str] = {}

    def resolve(record: TrackerRecord, visiting: set[str]) -> str:
        if record.tracker_id in resolved:
            return resolved[record.tracker_id]
        if record.tracker_id in visiting:
            raise TrackerExtensionError("tracker extension cycle detected")
        visiting.add(record.tracker_id)

        if record.kind is TrackerRecordKind.ARCHITECTURE:
            parent = architecture.require_record(record.architecture_record_id or "")
            number = parent.number
        elif record.kind is TrackerRecordKind.TRACKER_MILESTONE:
            number = str(record.display_number)
        else:
            if record.parent_tracker_id:
                try:
                    parent_record = by_id[record.parent_tracker_id]
                except KeyError as exc:
                    raise TrackerExtensionError(
                        f"missing tracker parent {record.parent_tracker_id}"
                    ) from exc
                parent_number = resolve(parent_record, visiting)
            else:
                parent = architecture.require_record(
                    record.architecture_record_id or ""
                )
                parent_number = parent.number
            number = f"{parent_number}.{record.local_segment}"

        visiting.remove(record.tracker_id)
        resolved[record.tracker_id] = number
        return number

    for item in records:
        resolve(item, set())

    siblings: dict[tuple[str, int], list[str]] = defaultdict(list)
    for item in records:
        if item.kind is TrackerRecordKind.EXTENSION:
            parent_key = item.parent_tracker_id or item.architecture_record_id or ""
            siblings[(parent_key, int(item.local_segment or 0))].append(item.tracker_id)

    duplicates = [ids for ids in siblings.values() if len(ids) > 1]
    if duplicates:
        raise TrackerExtensionError(
            f"duplicate extension segments detected: {duplicates}"
        )

    return resolved
