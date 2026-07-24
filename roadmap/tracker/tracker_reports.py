"""
Structured tracker reports.
"""

from __future__ import annotations

from typing import Iterable

from .architecture import ArchitectureSnapshot
from .files import detect_previous_milestone_impacts
from .models import TrackerRecord
from .progress import calculate_progress


def build_summary_report(
    architecture: ArchitectureSnapshot,
    records: Iterable[TrackerRecord],
) -> dict[str, object]:
    records = tuple(records)
    progress = calculate_progress(architecture, records)
    return {
        "architecture": {
            "version": architecture.version,
            "sha256": architecture.sha256,
            "total": progress.architecture_total,
            "completed": progress.architecture_completed,
            "percentage": progress.architecture_percentage,
        },
        "tracker": {
            "total": progress.tracker_total,
            "completed": progress.tracker_completed,
            "percentage": progress.tracker_percentage,
            "commits": len({c.sha for r in records for c in r.commits}),
            "files": len({f.path for r in records for f in r.files}),
            "previous_milestone_impacts": len(
                detect_previous_milestone_impacts(records)
            ),
        },
    }
