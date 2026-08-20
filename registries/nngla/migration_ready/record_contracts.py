"""Record-atomic migration contracts for P006.7.11.7 Bundle 17.1.0MR.

A logical window is an operator-selected range of governed NNGLA migration
ordinals.  The durability boundary is one coordinate, not the whole window.
PostgreSQL remains the sole authority for which ordinals are already complete.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecordReceiptObservation:
    execution_id: str
    logical_batch_id: str
    window_start_ordinal: int
    window_end_ordinal: int
    requested_count: int
    migration_ordinal: int
    coordinate_candidate_id: str
    canonical_spatial_point_id: str
    geometry_id: str
    outcome: str
    completed_at: str

    def __post_init__(self) -> None:
        if not self.execution_id.startswith("nnglarun:spatial:"):
            raise ValueError("invalid record execution identity")
        if not self.logical_batch_id.startswith("nnglabatch:spatial:mr:"):
            raise ValueError("invalid logical batch identity")
        if self.window_start_ordinal < 1 or self.window_end_ordinal < self.window_start_ordinal:
            raise ValueError("invalid logical window bounds")
        if self.requested_count != self.window_end_ordinal - self.window_start_ordinal + 1:
            raise ValueError("requested_count does not match logical window bounds")
        if not self.window_start_ordinal <= self.migration_ordinal <= self.window_end_ordinal:
            raise ValueError("migration ordinal lies outside logical window")
        if self.outcome != "INSERTED":
            raise ValueError("17.1.0MR import receipts are created only for newly inserted coordinates")


@dataclass(frozen=True, slots=True)
class RecordMigrationProgress:
    total_count: int
    canonical_count: int
    contiguous_completed_ordinal: int
    first_unfulfilled_ordinal: int | None
    migration_complete: bool
    active_logical_batch_id: str | None = None
    active_window_start_ordinal: int | None = None
    active_window_end_ordinal: int | None = None
    active_requested_count: int | None = None

    def __post_init__(self) -> None:
        if self.total_count < 1:
            raise ValueError("total_count must be positive")
        if not 0 <= self.canonical_count <= self.total_count:
            raise ValueError("canonical_count is outside source bounds")
        if not 0 <= self.contiguous_completed_ordinal <= self.total_count:
            raise ValueError("contiguous completion is outside source bounds")
        expected_first = None if self.contiguous_completed_ordinal == self.total_count else self.contiguous_completed_ordinal + 1
        if self.first_unfulfilled_ordinal != expected_first:
            raise ValueError("first_unfulfilled_ordinal must follow the contiguous high-water mark")
        if self.migration_complete != (self.first_unfulfilled_ordinal is None):
            raise ValueError("migration_complete does not match first_unfulfilled_ordinal")
        active_values = (
            self.active_logical_batch_id,
            self.active_window_start_ordinal,
            self.active_window_end_ordinal,
            self.active_requested_count,
        )
        if any(value is not None for value in active_values) and not all(value is not None for value in active_values):
            raise ValueError("active logical batch metadata must be all present or all absent")


@dataclass(frozen=True, slots=True)
class RecordMigrationWindow:
    logical_batch_id: str
    window_start_ordinal: int
    window_end_ordinal: int
    requested_count: int
    execution_start_ordinal: int
    execution_end_ordinal: int
    candidate_ids: tuple[str, ...]
    resumed: bool = False
    explicit_range: bool = False

    def __post_init__(self) -> None:
        if not self.logical_batch_id.startswith("nnglabatch:spatial:mr:"):
            raise ValueError("invalid logical batch identity")
        if self.window_start_ordinal < 1 or self.window_end_ordinal < self.window_start_ordinal:
            raise ValueError("invalid logical window")
        if self.requested_count != self.window_end_ordinal - self.window_start_ordinal + 1:
            raise ValueError("requested_count does not match logical window")
        if not self.window_start_ordinal <= self.execution_start_ordinal <= self.execution_end_ordinal <= self.window_end_ordinal:
            raise ValueError("execution range lies outside logical window")
        if len(self.candidate_ids) != self.execution_end_ordinal - self.execution_start_ordinal + 1:
            raise ValueError("candidate count does not match execution range")
        if len(self.candidate_ids) != len(set(self.candidate_ids)):
            raise ValueError("record migration window contains duplicate candidates")

    @property
    def logical_count(self) -> int:
        return self.requested_count

    @property
    def selected_count(self) -> int:
        return len(self.candidate_ids)


@dataclass(frozen=True, slots=True)
class RecordWindowPreview:
    database_name: str
    environment_name: str
    source_sha256: str
    repository_revision: str
    requested_count: int
    progress: RecordMigrationProgress
    window: RecordMigrationWindow | None
    selected_count: int
    insert_count: int
    reuse_count: int
    conflict_count: int
    fingerprint: str

    @property
    def execution_ready(self) -> bool:
        return self.conflict_count == 0

    @property
    def migration_complete(self) -> bool:
        return self.progress.migration_complete


@dataclass(frozen=True, slots=True)
class RecordExecutionResult:
    logical_batch_id: str | None
    window_start_ordinal: int | None
    window_end_ordinal: int | None
    execution_start_ordinal: int | None
    execution_end_ordinal: int | None
    selected_count: int
    inserted_count: int
    reused_count: int
    last_committed_ordinal: int | None
    status: str

    def __post_init__(self) -> None:
        if self.status not in {"COMPLETE", "REUSED", "MIGRATION_COMPLETE"}:
            raise ValueError("invalid record execution status")
        if self.selected_count != self.inserted_count + self.reused_count:
            raise ValueError("record execution counts do not reconcile")


__all__ = [
    "RecordReceiptObservation",
    "RecordMigrationProgress",
    "RecordMigrationWindow",
    "RecordWindowPreview",
    "RecordExecutionResult",
]
