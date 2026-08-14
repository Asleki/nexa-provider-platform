"""P006.7.5 immutable NNGLA geometry authority/version contracts."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from enum import Enum
import re
from registries.country.operating_context import RecordEffectScope

_SHA256=re.compile(r"^[0-9a-f]{64}$")

class GeometryAuthorityLevel(str, Enum):
    AUTHORITATIVE="AUTHORITATIVE"
    QUALIFIED_SOURCE="QUALIFIED_SOURCE"

class GeometryQualificationStatus(str, Enum):
    QUALIFIED="QUALIFIED"

class GeometryPublicationStatus(str, Enum):
    PUBLISHED="PUBLISHED"
    SOURCE_AVAILABLE="SOURCE_AVAILABLE"

@dataclass(frozen=True, slots=True)
class GeometryVersionRecord:
    geometry_id: str
    subject_type: str
    subject_id: str
    geometry_role_code: str
    source_geometry_id: str
    source_dataset_id: str
    source_version: str
    geometry_type_code: str
    crs_code: str
    authoritative_level: GeometryAuthorityLevel | str
    vertex_count: int | None
    part_count: int | None
    valid_from: date
    valid_to: date | None
    supersedes_geometry_id: str | None
    superseded_by_geometry_id: str | None
    qualification_status: GeometryQualificationStatus | str
    publication_status: GeometryPublicationStatus | str
    checksum_sha256: str
    source_path_reference: str
    runtime_effect_scope: RecordEffectScope | str
    notes: str
    def __post_init__(self) -> None:
        if not re.fullmatch(r"NG-GEO-\d{6}", self.geometry_id):
            raise ValueError("geometry_id must use governed NG-GEO-###### identity")
        if not self.subject_type or not self.subject_id or not self.geometry_role_code:
            raise ValueError("geometry subject and role are required")
        if not self.source_geometry_id or not self.source_dataset_id or not self.source_version:
            raise ValueError("source geometry lineage is required")
        if self.crs_code != "NG-CRS-EPSG4326":
            raise ValueError("Bundle 15B source geometry must use governed NoveGeo WGS84 CRS")
        level=self.authoritative_level if isinstance(self.authoritative_level,GeometryAuthorityLevel) else GeometryAuthorityLevel(str(self.authoritative_level))
        q=self.qualification_status if isinstance(self.qualification_status,GeometryQualificationStatus) else GeometryQualificationStatus(str(self.qualification_status))
        pub=self.publication_status if isinstance(self.publication_status,GeometryPublicationStatus) else GeometryPublicationStatus(str(self.publication_status))
        scope=self.runtime_effect_scope if isinstance(self.runtime_effect_scope,RecordEffectScope) else RecordEffectScope(str(self.runtime_effect_scope))
        if self.vertex_count is not None and self.vertex_count <= 0:
            raise ValueError("vertex_count must be positive when supplied")
        if self.part_count is not None and self.part_count <= 0:
            raise ValueError("part_count must be positive when supplied")
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValueError("geometry valid_to cannot precede valid_from")
        if self.supersedes_geometry_id == self.geometry_id or self.superseded_by_geometry_id == self.geometry_id:
            raise ValueError("a geometry version cannot supersede itself")
        if not _SHA256.fullmatch(self.checksum_sha256):
            raise ValueError("geometry checksum must be lowercase SHA-256")
        if level is GeometryAuthorityLevel.AUTHORITATIVE and pub is not GeometryPublicationStatus.PUBLISHED:
            raise ValueError("the supplied authoritative geometry must remain published")
        object.__setattr__(self,"authoritative_level",level)
        object.__setattr__(self,"qualification_status",q)
        object.__setattr__(self,"publication_status",pub)
        object.__setattr__(self,"runtime_effect_scope",scope)

    @property
    def is_authoritative(self) -> bool:
        return self.authoritative_level is GeometryAuthorityLevel.AUTHORITATIVE

    @property
    def is_public(self) -> bool:
        return self.publication_status is GeometryPublicationStatus.PUBLISHED

class MemoryGeometryAuthorityRepository:
    def __init__(self) -> None:
        self._items: dict[str,GeometryVersionRecord]={}
    def add(self, record: GeometryVersionRecord) -> GeometryVersionRecord:
        prior=self._items.get(record.geometry_id)
        if prior is not None and prior != record: raise ValueError("geometry identifier collision")
        self._items[record.geometry_id]=record; return record
    def get(self, geometry_id: str): return self._items.get(geometry_id)
    def by_subject(self, subject_id: str, geometry_role_code: str | None=None):
        rows=[r for r in self._items.values() if r.subject_id==subject_id and (geometry_role_code is None or r.geometry_role_code==geometry_role_code)]
        return tuple(sorted(rows,key=lambda x:x.geometry_id))
    def all(self): return tuple(self._items[k] for k in sorted(self._items))

__all__=["GeometryAuthorityLevel","GeometryQualificationStatus","GeometryPublicationStatus","GeometryVersionRecord","MemoryGeometryAuthorityRepository"]
