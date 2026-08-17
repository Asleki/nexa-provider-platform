"""Bundle 17F immutable reconciliation, traversal and association contracts."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re


class CanonicalSubjectFamily(str, Enum):
    PLACE = "PLACE"
    ADMINISTRATIVE_AREA = "ADMINISTRATIVE_AREA"
    ROAD = "ROAD"
    GEOGRAPHIC_FEATURE = "GEOGRAPHIC_FEATURE"
    EXISTING_GEOMETRY = "EXISTING_GEOMETRY"


class AssociationStatus(str, Enum):
    READY_ASSOCIATE_EXISTING_GEOMETRY = "READY_ASSOCIATE_EXISTING_GEOMETRY"
    DEFERRED_NO_GEOMETRY = "DEFERRED_NO_GEOMETRY"
    SUBJECT_ROLE_RECONCILIATION_REQUIRED = "SUBJECT_ROLE_RECONCILIATION_REQUIRED"
    SOURCE_NOT_CANONICAL = "SOURCE_NOT_CANONICAL"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True, slots=True)
class ExistingCanonicalAlignment:
    alignment_id: str
    object_family: CanonicalSubjectFamily
    source_record_id: str
    candidate_id: str
    canonical_id: str
    canonical_ordinal: int
    source_path: str
    source_sha256: str
    identity_status: str
    geometry_status: str
    geometry_id: str
    database_verification_status: str
    runtime_effect_scope: str
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.alignment_id.startswith("align:nngla:"):
            raise ValueError("invalid alignment identity")
        patterns = {
            CanonicalSubjectFamily.PLACE: r"NG-PLC-\d{6}",
            CanonicalSubjectFamily.ADMINISTRATIVE_AREA: r"NG-ADM-\d{6}",
            CanonicalSubjectFamily.ROAD: r"NG-RD-\d{6}",
            CanonicalSubjectFamily.GEOGRAPHIC_FEATURE: r"NG-FEAT-\d{6}",
            CanonicalSubjectFamily.EXISTING_GEOMETRY: r"NG-GEO-\d{6}",
        }
        if re.fullmatch(patterns[self.object_family], self.canonical_id) is None:
            raise ValueError("canonical identity does not match object family")
        if self.runtime_effect_scope != "SHARED_REFERENCE":
            raise ValueError("Bundle 17F reconciles shared canonical reference identities")
        if self.database_verification_status not in {
            "LOCKED_BASELINE_ASSERTED_REQUIRES_LIVE_RECHECK",
            "SOURCE_GEOMETRY_RECORD_NO_SEPARATE_OBJECT_RECHECK",
        }:
            raise ValueError("unexpected database verification status")


@dataclass(frozen=True, slots=True)
class SubjectSpatialAssociationCandidate:
    association_candidate_id: str
    subject_family: CanonicalSubjectFamily
    canonical_subject_id: str
    source_subject_id: str
    geometry_id: str
    geometry_role_code: str
    source_geometry_subject_id: str
    association_status: AssociationStatus
    association_basis: str
    runtime_effect_scope: str
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.association_candidate_id.startswith("assocand:nngla:"):
            raise ValueError("invalid spatial association candidate identity")
        if self.geometry_id and re.fullmatch(r"NG-GEO-\d{6}", self.geometry_id) is None:
            raise ValueError("association geometry must use governed geometry identity")
        if self.runtime_effect_scope != "SHARED_REFERENCE":
            raise ValueError("Bundle 17F associations remain shared reference")


@dataclass(frozen=True, slots=True)
class GeometryTraversalQualification:
    traversal_qualification_id: str
    geometry_id: str
    subject_type: str
    subject_id: str
    geometry_type_code: str
    crs_code: str
    source_path_reference: str
    source_artifact_exists: bool
    source_sha256_matches: bool
    geometry_type_supported: bool
    crs_valid: bool
    qualified_source: bool
    traversal_basis: str
    identifier_sequence_used: bool
    traversal_status: str
    findings: str

    def __post_init__(self) -> None:
        if re.fullmatch(r"NG-GTRAV-\d{6}", self.traversal_qualification_id) is None:
            raise ValueError("invalid geometry traversal qualification identity")
        if re.fullmatch(r"NG-GEO-\d{6}", self.geometry_id) is None:
            raise ValueError("invalid geometry identity")
        if self.identifier_sequence_used:
            raise ValueError("free-form geometry traversal may never use identifier sequence as geometry")
        if self.traversal_status not in {"PASS", "FAIL"}:
            raise ValueError("traversal status must be PASS or FAIL")


@dataclass(frozen=True, slots=True)
class SpatialAssociationPreconditionResult:
    precondition_result_id: str
    association_candidate_id: str
    canonical_subject_id: str
    geometry_id: str
    identity_preserved: bool
    canonical_subject_confirmed: bool
    geometry_evidence_available: bool
    geometry_traversal_valid: bool
    subject_role_compatible: bool
    association_ready: bool
    precondition_status: str
    findings: str

    def __post_init__(self) -> None:
        if re.fullmatch(r"NG-SPAPRE-\d{7}", self.precondition_result_id) is None:
            raise ValueError("invalid association precondition result identity")
        if self.precondition_status not in {
            "PASS_READY_TO_ASSOCIATE",
            "DEFERRED_NO_GEOMETRY",
            "DEFERRED_SUBJECT_ROLE_RECONCILIATION",
            "FAIL",
        }:
            raise ValueError("unexpected association precondition status")


__all__ = [
    "CanonicalSubjectFamily", "AssociationStatus", "ExistingCanonicalAlignment",
    "SubjectSpatialAssociationCandidate", "GeometryTraversalQualification", "SpatialAssociationPreconditionResult",
]
