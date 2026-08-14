"""P006.7.7 immutable parcel subdivision/consolidation lineage contracts."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from enum import Enum
import re

_PARCEL_RE=re.compile(r"^NV-\d{2}-\d{3}-\d{4,}$")

class ParcelLineageAction(str, Enum):
    SUBDIVISION="SUBDIVISION"
    CONSOLIDATION="CONSOLIDATION"

@dataclass(frozen=True, slots=True)
class ParcelLineageRecord:
    lineage_id: str
    action: ParcelLineageAction | str
    predecessor_parcel_ids: tuple[str,...]
    successor_parcel_ids: tuple[str,...]
    effective_on: date
    source_reference: str
    human_decision_reference: str | None = None
    simulation_assessment_reference: str | None = None

    def __post_init__(self) -> None:
        if not self.lineage_id.startswith("parcel-lineage:"):
            raise ValueError("lineage_id must use parcel-lineage: namespace")
        action=self.action if isinstance(self.action,ParcelLineageAction) else ParcelLineageAction(str(self.action))
        object.__setattr__(self,"action",action)
        if not self.predecessor_parcel_ids or not self.successor_parcel_ids:
            raise ValueError("parcel lineage requires predecessor and successor identities")
        ids=self.predecessor_parcel_ids+self.successor_parcel_ids
        if any(_PARCEL_RE.fullmatch(x) is None for x in ids):
            raise ValueError("lineage must reference governed parcel identities")
        if len(set(ids)) != len(ids):
            raise ValueError("predecessor/successor parcel identities must not repeat")
        if action is ParcelLineageAction.SUBDIVISION and len(self.predecessor_parcel_ids) != 1:
            raise ValueError("subdivision has exactly one predecessor parcel")
        if action is ParcelLineageAction.SUBDIVISION and len(self.successor_parcel_ids) < 2:
            raise ValueError("subdivision requires at least two successor parcels")
        if action is ParcelLineageAction.CONSOLIDATION and len(self.predecessor_parcel_ids) < 2:
            raise ValueError("consolidation requires at least two predecessor parcels")
        if action is ParcelLineageAction.CONSOLIDATION and len(self.successor_parcel_ids) != 1:
            raise ValueError("consolidation has exactly one successor parcel")
        if not self.source_reference:
            raise ValueError("source_reference is required")

class MemoryParcelLineageRepository:
    def __init__(self) -> None: self._items: dict[str,ParcelLineageRecord]={}
    def add(self, record: ParcelLineageRecord) -> ParcelLineageRecord:
        prior=self._items.get(record.lineage_id)
        if prior is not None and prior != record: raise ValueError("parcel lineage identifier collision")
        self._items[record.lineage_id]=record; return record
    def involving(self, parcel_id: str) -> tuple[ParcelLineageRecord,...]:
        return tuple(r for r in self._items.values() if parcel_id in r.predecessor_parcel_ids or parcel_id in r.successor_parcel_ids)

__all__=["ParcelLineageAction","ParcelLineageRecord","MemoryParcelLineageRepository"]
