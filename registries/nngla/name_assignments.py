"""P006.7.3 feature/place to geographic-name assignment contracts."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from registries.country.operating_context import RecordEffectScope
from .geographic_names import GeographicNameRole

@dataclass(frozen=True, slots=True)
class GeographicNameAssignment:
    assignment_id: str
    subject_id: str
    feature_type_code: str
    name_id: str
    canonical_name: str
    assignment_status: str
    role: GeographicNameRole
    effective_from: date | None
    effective_to: date | None
    gazette_reference: str | None
    source_basis: str
    runtime_effect_scope: RecordEffectScope
    simulation_assessment_id: str | None = None
    human_decision_id: str | None = None

    def __post_init__(self) -> None:
        if not self.assignment_id or not self.subject_id or not self.name_id:
            raise ValueError("assignment, subject and name identifiers are required")
        if self.effective_from and self.effective_to and self.effective_to < self.effective_from:
            raise ValueError("effective_to cannot precede effective_from")
        if not isinstance(self.runtime_effect_scope, RecordEffectScope):
            object.__setattr__(self, "runtime_effect_scope", RecordEffectScope(str(self.runtime_effect_scope)))
        if self.assignment_status == "PROPOSED_UNGAZETTED" and self.gazette_reference:
            raise ValueError("ungazetted proposals cannot carry a gazette reference")

    @property
    def is_publicly_official(self) -> bool:
        return self.assignment_status in {"GAZETTED", "ACTIVE_OFFICIAL"}

class MemoryNameAssignmentRepository:
    def __init__(self) -> None:
        self._items: dict[str, GeographicNameAssignment] = {}

    def add(self, assignment: GeographicNameAssignment) -> GeographicNameAssignment:
        prior = self._items.get(assignment.assignment_id)
        if prior is not None and prior != assignment:
            raise ValueError("name-assignment identifier collision")
        self._items[assignment.assignment_id] = assignment
        return assignment

    def for_subject(self, subject_id: str) -> tuple[GeographicNameAssignment, ...]:
        return tuple(x for x in self._items.values() if x.subject_id == subject_id)

    def all(self) -> tuple[GeographicNameAssignment, ...]:
        return tuple(self._items[k] for k in sorted(self._items))

__all__ = ["GeographicNameAssignment", "MemoryNameAssignmentRepository"]
