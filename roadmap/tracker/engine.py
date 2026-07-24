"""
Top-level operational tracker engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .architecture import ArchitectureSnapshot
from .generator import write_tracker
from .storage import TrackerStore
from .validation import (
    TrackerValidationReport,
    validate_records,
    validate_synchronization,
)


@dataclass(frozen=True, slots=True)
class TrackerBuildResult:
    architecture_sha256: str
    tracker_records: int
    output: Path
    validation: TrackerValidationReport


@dataclass(slots=True)
class TrackerEngine:
    store: TrackerStore

    def build(
        self,
        architecture: ArchitectureSnapshot,
        *,
        roadmap_path: Path = Path("ROADMAP.md"),
        output: Path = Path("ROADMAP_TRACKER.md"),
        generated_at: str | None = None,
    ) -> TrackerBuildResult:
        records = self.store.load()
        report = validate_records(architecture, records)
        report.raise_for_errors()

        timestamp = generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
        write_tracker(
            architecture,
            records,
            generated_at=timestamp,
            roadmap_path=roadmap_path,
            output=output,
        )
        sync = validate_synchronization(
            architecture=architecture,
            roadmap_path=roadmap_path,
            tracker_path=output,
        )
        sync.raise_for_errors()
        return TrackerBuildResult(
            architecture_sha256=architecture.sha256,
            tracker_records=len(records),
            output=Path(output),
            validation=sync,
        )
