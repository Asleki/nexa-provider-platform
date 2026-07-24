"""
Tracker execution progress calculations.

Architecture progress is copied from ArchitectureSnapshot and is never inferred
from tracker extension completion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .architecture import ArchitectureSnapshot
from .models import TrackerRecord, TrackerStatus


COMPLETE_TRACKER_STATUSES = {
    TrackerStatus.VALIDATED,
    TrackerStatus.COMPLETED,
    TrackerStatus.CANCELLED,
}


@dataclass(frozen=True, slots=True)
class TrackerProgress:
    architecture_total: int
    architecture_completed: int
    architecture_percentage: float
    tracker_total: int
    tracker_completed: int
    tracker_percentage: float


def calculate_progress(
    architecture: ArchitectureSnapshot,
    records: Iterable[TrackerRecord],
) -> TrackerProgress:
    records = tuple(records)
    complete = sum(item.status in COMPLETE_TRACKER_STATUSES for item in records)
    tracker_percentage = round((complete / len(records)) * 100, 2) if records else 0.0
    return TrackerProgress(
        architecture_total=len(architecture.records),
        architecture_completed=architecture.completed,
        architecture_percentage=architecture.percentage,
        tracker_total=len(records),
        tracker_completed=complete,
        tracker_percentage=tracker_percentage,
    )
