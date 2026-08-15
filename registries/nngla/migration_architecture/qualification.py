"""P006.7.11.3 domain-aware, zero-write NNGLA qualification rules."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path

from .contracts import CanonicalObjectFamily, SourceIdentity
from .identity import CanonicalIdentityAllocator, CanonicalIdentityError
from .limits import CODE_LIMIT, IDENTIFIER_LIMIT, LATITUDE_RANGE, LONGITUDE_RANGE, NAME_LIMIT, SOURCE_PATH_LIMIT
from .plans import MigrationPlan, PlanPurpose
from .source_catalogue import ROOT, SourceRecord, SourceSnapshot
from registries.nngla.bundle15a_source import load_feature_types
from registries.nngla.bundle15b_source import load_crs_definitions, load_geometry_types, load_road_classifications


class QualificationOutcome(str, Enum):
    QUALIFIED = "QUALIFIED"
    QUALIFIED_WITH_REUSE = "QUALIFIED_WITH_REUSE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    QUARANTINE = "QUARANTINE"
    BLOCKED = "BLOCKED"
    EMPTY_GOVERNED_SOURCE = "EMPTY_GOVERNED_SOURCE"


@dataclass(frozen=True, slots=True)
class QualificationFinding:
    code: str
    severity: str
    subject_id: str
    detail: str


@dataclass(frozen=True, slots=True)
class RecordQualification:
    source_id: str
    outcome: QualificationOutcome
    findings: tuple[QualificationFinding, ...]
    proposed_canonical_id: str | None = None


_FAMILY_MAP = {
    "PLACE": CanonicalObjectFamily.PLACE,
    "ADMINISTRATIVE_AREA": CanonicalObjectFamily.ADMINISTRATIVE_AREA,
    "ROAD": CanonicalObjectFamily.ROAD,
    "GEOGRAPHIC_FEATURE": CanonicalObjectFamily.GEOGRAPHIC_FEATURE,
    "GEOMETRY": CanonicalObjectFamily.GEOMETRY,
    "ADDRESS": CanonicalObjectFamily.ADDRESS,
    "TITLE": CanonicalObjectFamily.TITLE,
}


class QualificationEngine:
    def __init__(self) -> None:
        self._allocator = CanonicalIdentityAllocator()
        self._feature_types = frozenset(item.feature_type_code for item in load_feature_types())
        self._road_classes = frozenset(item.road_class_code for item in load_road_classifications())
        self._geometry_types = frozenset(item.geometry_type_code for item in load_geometry_types())
        self._crs_codes = frozenset(item.crs_code for item in load_crs_definitions())
        self._place_types = frozenset({
            "VILLAGE", "TOWN", "SUBURB", "TOWNSHIP", "CITY_DISTRICT", "MARKET_CENTRE",
            "MUNICIPALITY", "INDUSTRIAL_ZONE", "RESORT_SETTLEMENT", "CITY", "ISLAND_SETTLEMENT",
        })

    @staticmethod
    def _finding(code: str, subject: str, detail: str, severity: str = "BLOCKING") -> QualificationFinding:
        return QualificationFinding(code, severity, subject, detail)

    def qualify(self, plan: MigrationPlan, snapshot: SourceSnapshot, record: SourceRecord) -> RecordQualification:
        findings: list[QualificationFinding] = []
        p = record.payload
        for failure in IDENTIFIER_LIMIT.validate(record.source_id):
            findings.append(self._finding("IDENTIFIER_LIMIT", record.source_id, failure))

        name = p.get("canonical_name")
        if name is not None:
            for failure in NAME_LIMIT.validate(name):
                findings.append(self._finding("NAME_LIMIT", record.source_id, failure))

        runtime_scope = p.get("runtime_effect_scope")
        if runtime_scope and runtime_scope not in {"SHARED_REFERENCE", "SIMULATION_ONLY", "PRODUCTION_ONLY", "RUNTIME_SCOPED", "HISTORICAL_REFERENCE"}:
            findings.append(self._finding("RUNTIME_EFFECT_SCOPE_INVALID", record.source_id, str(runtime_scope)))

        if plan.qualification_profile == "place-v1":
            self._place(record, findings)
        elif plan.qualification_profile == "administrative-area-v1":
            self._admin(record, findings)
        elif plan.qualification_profile == "road-v1":
            self._road(record, findings)
        elif plan.qualification_profile == "geographic-feature-v1":
            self._feature(record, findings)
        elif plan.qualification_profile == "geometry-v1":
            self._geometry(record, findings)
        elif plan.qualification_profile == "survey-control-v1":
            self._survey_control(record, findings)
        elif plan.qualification_profile == "sovereign-boundary-v1":
            self._sovereign(record, findings)
        elif plan.qualification_profile in {"address-v1", "parcel-v1", "title-v1", "state-land-v1", "geographic-name-reference-v1"}:
            pass
        else:
            findings.append(self._finding("QUALIFICATION_PROFILE_UNKNOWN", record.source_id, plan.qualification_profile))

        proposed = self._proposal(plan, snapshot, record, findings)
        blocking = any(f.severity == "BLOCKING" for f in findings)
        review = any(f.severity == "REVIEW" for f in findings)
        outcome = QualificationOutcome.BLOCKED if blocking else QualificationOutcome.REVIEW_REQUIRED if review else QualificationOutcome.QUALIFIED
        return RecordQualification(record.source_id, outcome, tuple(findings), proposed)

    def _proposal(self, plan: MigrationPlan, snapshot: SourceSnapshot, record: SourceRecord, findings: list[QualificationFinding]) -> str | None:
        if plan.purpose is not PlanPurpose.CANONICAL_OBJECT:
            return None
        family = _FAMILY_MAP.get(snapshot.descriptor.domain_family)
        if family is None:
            return None
        candidate = None
        for key in ("administrative_candidate_id", "road_candidate_id", "feature_candidate_id"):
            if record.payload.get(key):
                candidate = str(record.payload[key])
                break
        try:
            proposal = self._allocator.propose(
                source=SourceIdentity(snapshot.descriptor.dataset_id, snapshot.descriptor.dataset_version, record.source_id, candidate),
                object_family=family,
            )
            return proposal.canonical_id
        except CanonicalIdentityError as exc:
            # Geometry/title identifiers can already be canonical in source and are validated by their schema family.
            source_contract_id = record.source_id
            if family in {CanonicalObjectFamily.GEOMETRY, CanonicalObjectFamily.TITLE, CanonicalObjectFamily.ADDRESS}:
                return source_contract_id
            findings.append(self._finding("CANONICAL_ID_PROPOSAL_FAILED", record.source_id, str(exc)))
            return None

    def _place(self, record: SourceRecord, findings: list[QualificationFinding]) -> None:
        p = record.payload
        for field in ("settlement_name_record_id", "place_type_code", "region_code", "source_dataset_id"):
            if not str(p.get(field, "")).strip():
                findings.append(self._finding("PLACE_REQUIRED_FIELD", record.source_id, field))
        if p.get("place_type_code") not in self._place_types:
            findings.append(self._finding("PLACE_TYPE_INVALID", record.source_id, str(p.get("place_type_code"))))
        if p.get("record_status") != "ACTIVE":
            findings.append(self._finding("PLACE_STATUS_NOT_ACTIVE", record.source_id, str(p.get("record_status")), "REVIEW"))

    def _admin(self, record: SourceRecord, findings: list[QualificationFinding]) -> None:
        p = record.payload
        for field in ("source_record_id", "administrative_type_code", "canonical_name", "parent_source_record_id", "candidate_status"):
            if not str(p.get(field, "")).strip():
                findings.append(self._finding("ADMIN_REQUIRED_FIELD", record.source_id, field))

    def _road(self, record: SourceRecord, findings: list[QualificationFinding]) -> None:
        p = record.payload
        for field in ("road_name_id", "canonical_name", "road_class_code", "planning_status"):
            if not str(p.get(field, "")).strip():
                findings.append(self._finding("ROAD_REQUIRED_FIELD", record.source_id, field))
        if p.get("road_class_code") not in self._road_classes:
            findings.append(self._finding("ROAD_CLASS_INVALID", record.source_id, str(p.get("road_class_code"))))

    def _feature(self, record: SourceRecord, findings: list[QualificationFinding]) -> None:
        p = record.payload
        for field in ("source_feature_id", "feature_type_code", "source_dataset_id", "recognition_status", "candidate_status"):
            if not str(p.get(field, "")).strip():
                findings.append(self._finding("FEATURE_REQUIRED_FIELD", record.source_id, field))
        if p.get("feature_type_code") not in self._feature_types:
            findings.append(self._finding("FEATURE_TYPE_INVALID", record.source_id, str(p.get("feature_type_code"))))
        if p.get("crs_code") and p.get("crs_code") not in self._crs_codes:
            findings.append(self._finding("CRS_INVALID", record.source_id, str(p.get("crs_code"))))
        lon, lat = str(p.get("centroid_lon", "")).strip(), str(p.get("centroid_lat", "")).strip()
        if bool(lon) != bool(lat):
            findings.append(self._finding("FEATURE_CENTROID_INCOMPLETE", record.source_id, "centroid longitude/latitude must be paired"))
        if lon and lat:
            for failure in LONGITUDE_RANGE.validate(lon) + LATITUDE_RANGE.validate(lat):
                findings.append(self._finding("COORDINATE_INVALID", record.source_id, failure))

    def _geometry(self, record: SourceRecord, findings: list[QualificationFinding]) -> None:
        p = record.payload
        allowed = self._geometry_types
        if p.get("crs_code") != "NG-CRS-EPSG4326" or p.get("crs_code") not in self._crs_codes:
            findings.append(self._finding("CRS_INVALID", record.source_id, str(p.get("crs_code"))))
        if p.get("geometry_type_code") not in allowed:
            findings.append(self._finding("GEOMETRY_TYPE_INVALID", record.source_id, str(p.get("geometry_type_code"))))
        checksum = str(p.get("checksum_sha256", ""))
        if len(checksum) != 64 or any(c not in "0123456789abcdef" for c in checksum):
            findings.append(self._finding("GEOMETRY_CHECKSUM_INVALID", record.source_id, checksum))
        source_path = str(p.get("source_path_reference", ""))
        for failure in SOURCE_PATH_LIMIT.validate(source_path):
            findings.append(self._finding("SOURCE_PATH_INVALID", record.source_id, failure))
        if source_path and not (ROOT / source_path).exists():
            findings.append(self._finding("GEOMETRY_SOURCE_MISSING", record.source_id, source_path))

    def _survey_control(self, record: SourceRecord, findings: list[QualificationFinding]) -> None:
        p = record.payload
        for failure in LONGITUDE_RANGE.validate(p.get("longitude")) + LATITUDE_RANGE.validate(p.get("latitude")):
            findings.append(self._finding("COORDINATE_INVALID", record.source_id, failure))
        if p.get("crs_code") != "NG-CRS-EPSG4326":
            findings.append(self._finding("CRS_INVALID", record.source_id, str(p.get("crs_code"))))

    def _sovereign(self, record: SourceRecord, findings: list[QualificationFinding]) -> None:
        if record.payload.get("geometry_type") != "MultiPolygon":
            findings.append(self._finding("SOVEREIGN_GEOMETRY_TYPE_INVALID", record.source_id, str(record.payload.get("geometry_type"))))
        if record.payload.get("boundaryVersion") != "2":
            findings.append(self._finding("SOVEREIGN_VERSION_INVALID", record.source_id, str(record.payload.get("boundaryVersion"))))


__all__ = [
    "QualificationOutcome",
    "QualificationFinding",
    "RecordQualification",
    "QualificationEngine",
]
