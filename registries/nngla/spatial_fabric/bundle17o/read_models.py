"""Additive read records; no direct knowledge is required by downstream registries."""
from __future__ import annotations
from .contracts import SpatialReadRecord
class MemorySpatialReadRepository:
    def __init__(self, records=()):
        self._records={r.subject_id:r for r in records}
    def add(self, record: SpatialReadRecord):
        if record.subject_id in self._records: raise ValueError("duplicate spatial read subject")
        self._records[record.subject_id]=record
    def get(self, subject_id: str, *, runtime_mode: str, allow_restricted: bool=False) -> SpatialReadRecord | None:
        r=self._records.get(subject_id)
        if r is None or r.runtime_mode!=runtime_mode: return None
        if r.visibility!="PUBLIC" and not allow_restricted: return None
        return r
    def list_family(self, family: str, *, runtime_mode: str, allow_restricted: bool=False):
        return tuple(sorted((
            r for r in self._records.values()
            if r.family==family and r.runtime_mode==runtime_mode and (allow_restricted or r.visibility=="PUBLIC")
        ),key=lambda r:r.subject_id))
    def all_visible(self, *, runtime_mode: str, allow_restricted: bool=False):
        return tuple(sorted((
            r for r in self._records.values()
            if r.runtime_mode==runtime_mode and (allow_restricted or r.visibility=="PUBLIC")
        ),key=lambda r:(r.family,r.subject_id)))
__all__=["MemorySpatialReadRepository"]
