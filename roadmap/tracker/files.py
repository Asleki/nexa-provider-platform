"""
File evidence, ownership and previous-milestone impact analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .models import FileEvidence, TrackerRecord


@dataclass(frozen=True, slots=True)
class PreviousMilestoneImpact:
    path: str
    current_tracker_id: str
    owning_record_id: str
    reason: str | None


def build_file_index(
    records: Iterable[TrackerRecord],
) -> Mapping[str, tuple[str, ...]]:
    index: dict[str, list[str]] = {}
    for record in records:
        for evidence in record.files:
            index.setdefault(evidence.path, []).append(record.tracker_id)
    return {path: tuple(ids) for path, ids in sorted(index.items())}


def detect_previous_milestone_impacts(
    records: Iterable[TrackerRecord],
) -> tuple[PreviousMilestoneImpact, ...]:
    impacts: list[PreviousMilestoneImpact] = []
    for record in records:
        for evidence in record.files:
            if (
                evidence.action in {"MODIFIED", "DELETED", "RENAMED"}
                and evidence.owning_record_id
                and evidence.owning_record_id
                not in {record.tracker_id, record.architecture_record_id}
            ):
                impacts.append(
                    PreviousMilestoneImpact(
                        path=evidence.path,
                        current_tracker_id=record.tracker_id,
                        owning_record_id=evidence.owning_record_id,
                        reason=evidence.reason,
                    )
                )
    return tuple(impacts)
