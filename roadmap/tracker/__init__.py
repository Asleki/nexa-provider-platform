"""
Nexa Provider Platform Roadmap Tracker Engine.

The tracker is an operational, read-only consumer of the canonical roadmap.
It never mutates roadmap_data.py, ROADMAP.md, or the existing roadmap package.
"""

from .architecture import ArchitectureSnapshot, ArchitectureRecord
from .engine import TrackerEngine, TrackerBuildResult
from .models import (
    CommitEvidence,
    FileEvidence,
    TrackerRecord,
    TrackerRecordKind,
    TrackerStatus,
)
from .storage import TrackerStore
from .validation import TrackerValidationError, TrackerValidationReport

__version__ = "0.1.0"

__all__ = (
    "ArchitectureRecord",
    "ArchitectureSnapshot",
    "CommitEvidence",
    "FileEvidence",
    "TrackerBuildResult",
    "TrackerEngine",
    "TrackerRecord",
    "TrackerRecordKind",
    "TrackerStatus",
    "TrackerStore",
    "TrackerValidationError",
    "TrackerValidationReport",
)
