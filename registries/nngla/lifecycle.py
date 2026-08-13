"""P006.7.2.4 spatial lifecycle and effective-dating contracts."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

class SpatialLifecycleStatus(str, Enum):
    DETECTED="DETECTED"; DISCOVERED="DISCOVERED"; PROVISIONAL="PROVISIONAL"; OBSERVED="OBSERVED"
    SURVEY_PENDING="SURVEY_PENDING"; SURVEYED="SURVEYED"; CLASSIFIED="CLASSIFIED"; RECOGNIZED="RECOGNIZED"
    ACTIVE="ACTIVE"; INACTIVE="INACTIVE"; SEASONAL="SEASONAL"; DRY="DRY"; SUBMERGED="SUBMERGED"
    EXTINCT="EXTINCT"; MERGED="MERGED"; SPLIT="SPLIT"; SUPERSEDED="SUPERSEDED"; RETIRED="RETIRED"
    DEPRECATED="DEPRECATED"; DISPUTED="DISPUTED"

TERMINAL_SPATIAL_STATES = frozenset({SpatialLifecycleStatus.EXTINCT, SpatialLifecycleStatus.SUPERSEDED, SpatialLifecycleStatus.RETIRED, SpatialLifecycleStatus.DEPRECATED})

@dataclass(frozen=True, slots=True)
class SpatialLifecycleDefinition:
    status: SpatialLifecycleStatus
    canonical_label: str
    applies_to_origin_class: str
    allows_geometry: bool
    allows_official_name: bool
    terminal_status: bool
    status_rank: int
    description: str
    register_status: str

    def __post_init__(self) -> None:
        if self.status_rank < 1:
            raise ValueError("status_rank must be positive")
        if self.terminal_status != (self.status in TERMINAL_SPATIAL_STATES):
            raise ValueError("terminal_status conflicts with governed lifecycle code")

@dataclass(frozen=True, slots=True)
class EffectiveDateRange:
    effective_from: date
    effective_to: date | None = None

    def __post_init__(self) -> None:
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to cannot precede effective_from")

    def contains(self, value: date) -> bool:
        return self.effective_from <= value and (self.effective_to is None or value <= self.effective_to)

@dataclass(frozen=True, slots=True)
class TemporalDimensions:
    record_effective: EffectiveDateRange
    geometry_valid: EffectiveDateRange | None = None
    physical_origin_time: datetime | None = None
    physical_end_time: datetime | None = None

    def __post_init__(self) -> None:
        if self.physical_origin_time and self.physical_end_time and self.physical_end_time < self.physical_origin_time:
            raise ValueError("physical_end_time cannot precede physical_origin_time")

@dataclass(frozen=True, slots=True)
class SuccessionReference:
    subject_id: str
    supersedes_id: str | None = None
    superseded_by_id: str | None = None

    def __post_init__(self) -> None:
        if self.supersedes_id == self.subject_id or self.superseded_by_id == self.subject_id:
            raise ValueError("a record cannot supersede itself")
