"""P006.7.7 governed NNGLA parcel identity and lifecycle contracts."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from enum import Enum
import re
from registries.country.operating_context import RecordEffectScope

_PARCEL_RE = re.compile(r"^NV-\d{2}-\d{3}-\d{4,}$")
_GEO_RE = re.compile(r"^NG-GEO-\d{6}$")

class ParcelStatus(str, Enum):
    DRAFT="DRAFT"
    SURVEYED="SURVEYED"
    REGISTERED="REGISTERED"
    ACTIVE="ACTIVE"
    SUBDIVIDED="SUBDIVIDED"
    CONSOLIDATED="CONSOLIDATED"
    CANCELLED="CANCELLED"
    HISTORIC="HISTORIC"
    DISPUTED="DISPUTED"

@dataclass(frozen=True, slots=True)
class ParcelRecord:
    parcel_id: str
    parent_parcel_id: str | None
    cadastral_series: str
    parcel_sequence: str
    parcel_status: ParcelStatus | str
    geometry_reference: str | None
    land_use_code: str | None
    survey_status: str
    created_effective_at: date
    retired_effective_at: date | None
    source_reference: str
    runtime_effect_scope: RecordEffectScope | str = RecordEffectScope.RUNTIME_SCOPED

    def __post_init__(self) -> None:
        if not _PARCEL_RE.fullmatch(self.parcel_id):
            raise ValueError("parcel_id must use governed NV-##-###-####+ identity")
        if self.parent_parcel_id is not None:
            if not _PARCEL_RE.fullmatch(self.parent_parcel_id):
                raise ValueError("parent_parcel_id must use governed parcel identity")
            if self.parent_parcel_id == self.parcel_id:
                raise ValueError("parcel cannot be its own parent")
        if not self.cadastral_series or not self.parcel_sequence:
            raise ValueError("cadastral series and parcel sequence are required")
        status=self.parcel_status if isinstance(self.parcel_status,ParcelStatus) else ParcelStatus(str(self.parcel_status))
        object.__setattr__(self,"parcel_status",status)
        if self.geometry_reference is not None and not _GEO_RE.fullmatch(self.geometry_reference):
            raise ValueError("geometry_reference must use governed NG-GEO identity")
        if not self.survey_status:
            raise ValueError("survey_status is required and remains distinct from parcel_status")
        if self.retired_effective_at is not None and self.retired_effective_at < self.created_effective_at:
            raise ValueError("retired_effective_at cannot precede created_effective_at")
        if not self.source_reference:
            raise ValueError("source_reference is required")
        scope=self.runtime_effect_scope if isinstance(self.runtime_effect_scope,RecordEffectScope) else RecordEffectScope(str(self.runtime_effect_scope))
        if scope is not RecordEffectScope.RUNTIME_SCOPED:
            raise ValueError("parcel operational effect must remain RUNTIME_SCOPED")
        object.__setattr__(self,"runtime_effect_scope",scope)

class MemoryParcelRepository:
    def __init__(self) -> None:
        self._items: dict[str, ParcelRecord] = {}
    def add(self, parcel: ParcelRecord) -> ParcelRecord:
        prior=self._items.get(parcel.parcel_id)
        if prior is not None and prior != parcel:
            raise ValueError("parcel identifier collision")
        self._items[parcel.parcel_id]=parcel
        return parcel
    def get(self, parcel_id: str) -> ParcelRecord | None:
        return self._items.get(parcel_id)
    def children_of(self, parcel_id: str) -> tuple[ParcelRecord,...]:
        return tuple(sorted((p for p in self._items.values() if p.parent_parcel_id==parcel_id),key=lambda p:p.parcel_id))
    def all(self) -> tuple[ParcelRecord,...]:
        return tuple(self._items[k] for k in sorted(self._items))

__all__=["ParcelStatus","ParcelRecord","MemoryParcelRepository"]
