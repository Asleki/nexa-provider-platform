"""Delivery 3 R1 contracts for feature-level CITY qualification and authority.

Delivery 3 deliberately separates FEATURE_QUALIFIED from FABRIC_COMPLETE.
A CITY is qualified as one feature using exact PostGIS evidence. REGION and
peer municipality geometries may be read-only validation evidence; they are
not authority prerequisites.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
import re
from typing import Mapping

_SHA = re.compile(r"^[0-9a-f]{64}$")
_ADMIN = re.compile(r"^NG-ADM-[0-9]{6}$")
_GEO = re.compile(r"^NG-GEO-[0-9]{6}$")


def stable_digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def stable_id(prefix: str, value: object) -> str:
    return prefix + stable_digest(value)


class CandidateSourceMode(str, Enum):
    FROZEN_SOURCE_REUSE = "FROZEN_SOURCE_REUSE"
    SHARED_FACE_RECONSTRUCTION = "SHARED_FACE_RECONSTRUCTION"


class CityQualificationStatus(str, Enum):
    CITY_READY_FOR_AUTHORITY = "CITY_READY_FOR_AUTHORITY"
    CITY_RECONSTRUCTION_REQUIRED = "CITY_RECONSTRUCTION_REQUIRED"
    CITY_BLOCKED_BY_EVIDENCE = "CITY_BLOCKED_BY_EVIDENCE"


class FeatureQualificationStatus(str, Enum):
    FEATURE_QUALIFIED = "FEATURE_QUALIFIED"
    FEATURE_REJECTED = "FEATURE_REJECTED"


class FabricCompletenessStatus(str, Enum):
    NOT_ASSESSED = "NOT_ASSESSED"
    PARTIAL = "PARTIAL"
    COMPLETE = "COMPLETE"


class PrecisionMode(str, Enum):
    SOURCE_COORDINATES_EXACT_NO_GENERAL_SNAP = "SOURCE_COORDINATES_EXACT_NO_GENERAL_SNAP"
    GOVERNED_COMMON_PRECISION = "GOVERNED_COMMON_PRECISION"


class ResidualReviewStatus(str, Enum):
    REVIEW_DEFERRED = "REVIEW_DEFERRED"
    RESOLVED = "RESOLVED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True, slots=True)
class PrecisionPolicy:
    policy_id: str
    mode: PrecisionMode
    crs_code: str = "NG-CRS-EPSG4326"
    grid_size_degrees: float | None = None
    evidence_reference: str = "locked:source-coordinate-exact"
    policy_version: int = 1
    policy_sha256: str = ""

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or self.crs_code != "NG-CRS-EPSG4326":
            raise ValueError("precision policy identity and locked CRS are required")
        if self.policy_version < 1 or not self.evidence_reference.strip():
            raise ValueError("precision policy evidence/version are required")
        if self.mode is PrecisionMode.SOURCE_COORDINATES_EXACT_NO_GENERAL_SNAP:
            if self.grid_size_degrees is not None:
                raise ValueError("source-exact precision cannot declare a normalization grid")
        else:
            if self.grid_size_degrees is None or not (0.0 < float(self.grid_size_degrees) < 1.0):
                raise ValueError("governed common precision requires an explicit positive degree grid")
        material = {
            "policyId": self.policy_id,
            "mode": self.mode.value,
            "crsCode": self.crs_code,
            "gridSizeDegrees": self.grid_size_degrees,
            "evidenceReference": self.evidence_reference,
            "policyVersion": self.policy_version,
        }
        expected = stable_digest(material)
        if self.policy_sha256 and self.policy_sha256 != expected:
            raise ValueError("precision policy hash does not match policy material")
        object.__setattr__(self, "policy_sha256", expected)

    @property
    def normalization_grid(self) -> float | None:
        return self.grid_size_degrees if self.mode is PrecisionMode.GOVERNED_COMMON_PRECISION else None


SOURCE_EXACT_PRECISION = PrecisionPolicy(
    policy_id="precision-policy:nngla:source-exact-v1",
    mode=PrecisionMode.SOURCE_COORDINATES_EXACT_NO_GENERAL_SNAP,
)


@dataclass(frozen=True, slots=True)
class GeometryEvidence:
    subject_id: str
    administrative_type_code: str
    canonical_name: str
    evidence_kind: str
    evidence_id: str
    geometry_sha256: str
    source_geometry_sha256: str
    source_dataset_id: str
    source_dataset_version: str
    source_path_reference: str
    runtime_mode: str
    qualification_reference: str
    geometry_wkb_hex: str

    def __post_init__(self) -> None:
        if _ADMIN.fullmatch(self.subject_id) is None:
            raise ValueError("geometry evidence requires NG-ADM identity")
        if self.runtime_mode not in {"simulation", "production", "shared_reference"}:
            raise ValueError("invalid geometry evidence runtime")
        if _SHA.fullmatch(self.geometry_sha256) is None or _SHA.fullmatch(self.source_geometry_sha256) is None:
            raise ValueError("geometry evidence hashes must be SHA-256")
        if not self.evidence_id or not self.source_path_reference or not self.qualification_reference:
            raise ValueError("geometry evidence provenance is incomplete")
        try:
            bytes.fromhex(self.geometry_wkb_hex)
        except ValueError as exc:
            raise ValueError("geometry evidence WKB must be hexadecimal") from exc


@dataclass(frozen=True, slots=True)
class CityCandidateEvidence:
    city_administrative_area_id: str
    root_place_id: str
    candidate_source_mode: CandidateSourceMode
    candidate_id: str
    candidate_geometry_sha256: str
    source_geometry_sha256: str
    source_dataset_id: str
    source_dataset_version: str
    source_path_reference: str
    runtime_mode: str
    geometry_wkb_hex: str
    fabric_run_id: str = ""
    package_sha256: str = ""

    def __post_init__(self) -> None:
        if _ADMIN.fullmatch(self.city_administrative_area_id) is None or not self.root_place_id.startswith("NG-PLC-"):
            raise ValueError("CITY candidate requires canonical identities")
        if self.runtime_mode != "production":
            raise ValueError("Delivery 3 CITY authority candidate runtime must be production")
        if _SHA.fullmatch(self.candidate_geometry_sha256) is None or _SHA.fullmatch(self.source_geometry_sha256) is None:
            raise ValueError("CITY candidate hashes must be SHA-256")
        if not self.candidate_id or not self.source_path_reference:
            raise ValueError("CITY candidate provenance is required")
        try:
            bytes.fromhex(self.geometry_wkb_hex)
        except ValueError as exc:
            raise ValueError("CITY candidate WKB must be hexadecimal") from exc
        if self.candidate_source_mode is CandidateSourceMode.SHARED_FACE_RECONSTRUCTION:
            if not self.fabric_run_id.startswith("fabric-run:nngla:") or _SHA.fullmatch(self.package_sha256) is None:
                raise ValueError("reconstructed CITY candidate must bind Delivery-2 run/package")


@dataclass(frozen=True, slots=True)
class CityQualificationReceipt:
    qualification_id: str
    city_administrative_area_id: str
    root_place_id: str
    candidate_source_mode: CandidateSourceMode
    candidate_id: str
    raw_candidate_geometry_sha256: str
    evaluated_candidate_geometry_sha256: str
    source_geometry_sha256: str
    source_dataset_id: str
    source_dataset_version: str
    source_path_reference: str
    fabric_run_id: str
    package_sha256: str
    validation_parent_id: str
    parent_evidence_kind: str
    parent_evidence_id: str
    raw_parent_geometry_sha256: str
    evaluated_parent_geometry_sha256: str
    parent_qualification_reference: str
    parent_source_path_reference: str
    peer_evidence_digest: str
    precision_policy_id: str
    precision_policy_sha256: str
    precision_mode: PrecisionMode
    precision_grid_size_degrees: float | None
    precision_evidence_reference: str
    valid_geometry: bool
    polygonal: bool
    non_empty: bool
    srid_correct: bool
    parent_evidence_valid: bool
    city_covered_by_parent: bool
    raw_area_outside_parent_m2: float
    area_outside_parent_m2: float
    raw_positive_city_peer_overlap_m2: float
    positive_city_peer_overlap_m2: float
    raw_positive_municipality_overlap_m2: float
    positive_municipality_overlap_m2: float
    reference_point_covered: bool
    unresolved_city_affecting_defect_count: int
    numerical_residue: bool
    source_provenance_bound: bool
    qualifier_actor_id: str
    runtime_mode: str
    status: CityQualificationStatus
    failed_predicates: tuple[str, ...]
    database_mutation: bool = False
    qualification_sha256: str = ""

    def __post_init__(self) -> None:
        if not self.qualification_id.startswith("city-qualification:nngla:"):
            raise ValueError("CITY qualification namespace required")
        if _ADMIN.fullmatch(self.city_administrative_area_id) is None or _ADMIN.fullmatch(self.validation_parent_id) is None:
            raise ValueError("CITY qualification administrative identities are invalid")
        for value in (
            self.raw_candidate_geometry_sha256, self.evaluated_candidate_geometry_sha256,
            self.source_geometry_sha256, self.raw_parent_geometry_sha256,
            self.evaluated_parent_geometry_sha256, self.peer_evidence_digest,
            self.precision_policy_sha256,
        ):
            if _SHA.fullmatch(value) is None:
                raise ValueError("CITY qualification evidence hashes must be SHA-256")
        if self.precision_mode is PrecisionMode.SOURCE_COORDINATES_EXACT_NO_GENERAL_SNAP and self.precision_grid_size_degrees is not None:
            raise ValueError("source-exact qualification cannot carry a normalization grid")
        if self.precision_mode is PrecisionMode.GOVERNED_COMMON_PRECISION and (self.precision_grid_size_degrees is None or not self.precision_evidence_reference.strip()):
            raise ValueError("governed precision qualification must bind grid and evidence")
        if self.runtime_mode != "production" or self.database_mutation:
            raise ValueError("technical CITY qualification is production-scoped and read-only")
        if not self.qualifier_actor_id.strip():
            raise ValueError("independent qualifier identity is required")
        measurements = (
            self.raw_area_outside_parent_m2, self.area_outside_parent_m2,
            self.raw_positive_city_peer_overlap_m2, self.positive_city_peer_overlap_m2,
            self.raw_positive_municipality_overlap_m2, self.positive_municipality_overlap_m2,
        )
        if any(float(v) < 0 for v in measurements) or self.unresolved_city_affecting_defect_count < 0:
            raise ValueError("CITY qualification measurements cannot be negative")
        material = self.material(include_hash=False)
        expected = stable_digest(material)
        if self.qualification_sha256 and self.qualification_sha256 != expected:
            raise ValueError("CITY qualification hash mismatch")
        object.__setattr__(self, "qualification_sha256", expected)

    def material(self, *, include_hash: bool = True) -> Mapping[str, object]:
        data = asdict(self)
        data["candidate_source_mode"] = self.candidate_source_mode.value
        data["precision_mode"] = self.precision_mode.value
        data["status"] = self.status.value
        data["failed_predicates"] = list(self.failed_predicates)
        if not include_hash:
            data.pop("qualification_sha256", None)
        return data

    @property
    def feature_qualified(self) -> bool:
        return self.status is CityQualificationStatus.CITY_READY_FOR_AUTHORITY


@dataclass(frozen=True, slots=True)
class UnresolvedTerritorialResidual:
    residual_id: str
    parent_administrative_area_id: str
    geometry_sha256: str
    geometry_wkb_hex: str
    area_m2: float
    adjacent_subject_ids: tuple[str, ...]
    originating_target_ids: tuple[str, ...]
    source_fingerprint: str
    runtime_fingerprint: str
    reason: str
    review_status: ResidualReviewStatus = ResidualReviewStatus.REVIEW_DEFERRED
    visibility: str = "INTERNAL"
    publication_status: str = "NOT_PUBLISHED"

    def __post_init__(self) -> None:
        if not self.residual_id.startswith("territorial-residual:nngla:") or _ADMIN.fullmatch(self.parent_administrative_area_id) is None:
            raise ValueError("residual identity/parent is invalid")
        if _SHA.fullmatch(self.geometry_sha256) is None or _SHA.fullmatch(self.source_fingerprint) is None or _SHA.fullmatch(self.runtime_fingerprint) is None:
            raise ValueError("residual hashes/fingerprints must be SHA-256")
        if self.area_m2 < 0 or self.visibility != "INTERNAL" or self.publication_status != "NOT_PUBLISHED":
            raise ValueError("unresolved residual must remain non-public internal evidence")
        if any(_ADMIN.fullmatch(value) is None for value in self.adjacent_subject_ids):
            raise ValueError("residual adjacency requires NG-ADM identities")


@dataclass(frozen=True, slots=True)
class FabricCompleteness:
    parent_administrative_area_id: str
    status: FabricCompletenessStatus
    expected_child_count: int
    qualified_child_count: int
    published_child_count: int
    gap_m2: float
    positive_overlap_m2: float
    evidence_sha256: str

    def __post_init__(self) -> None:
        if _ADMIN.fullmatch(self.parent_administrative_area_id) is None or _SHA.fullmatch(self.evidence_sha256) is None:
            raise ValueError("fabric completeness identity/evidence invalid")
        if min(self.expected_child_count, self.qualified_child_count, self.published_child_count) < 0:
            raise ValueError("fabric counts cannot be negative")
        if self.qualified_child_count > self.expected_child_count or self.published_child_count > self.qualified_child_count:
            raise ValueError("fabric counts are inconsistent")
        if self.gap_m2 < 0 or self.positive_overlap_m2 < 0:
            raise ValueError("fabric measurements cannot be negative")
        exact = self.gap_m2 == 0.0 and self.positive_overlap_m2 == 0.0 and self.qualified_child_count == self.expected_child_count
        if self.status is FabricCompletenessStatus.COMPLETE and not exact:
            raise ValueError("COMPLETE fabric must be exact and exhaustive")


@dataclass(frozen=True, slots=True)
class CityAuthorityAdoptionRequest:
    qualification_id: str
    qualification_sha256: str
    city_administrative_area_id: str
    candidate_id: str
    candidate_geometry_sha256: str
    candidate_source_mode: CandidateSourceMode
    validation_parent_id: str
    parent_evidence_id: str
    parent_geometry_sha256: str
    parent_qualification_reference: str
    peer_evidence_digest: str
    precision_policy_id: str
    precision_policy_sha256: str
    effective_on: str
    qualifier_actor_id: str
    submitter_actor_id: str
    approver_actor_id: str
    decision_reference: str
    rationale: str

    def __post_init__(self) -> None:
        if _ADMIN.fullmatch(self.city_administrative_area_id) is None or _ADMIN.fullmatch(self.validation_parent_id) is None:
            raise ValueError("adoption requires CITY/parent NG-ADM identities")
        for value in (self.qualification_sha256, self.candidate_geometry_sha256, self.parent_geometry_sha256, self.peer_evidence_digest, self.precision_policy_sha256):
            if _SHA.fullmatch(value) is None:
                raise ValueError("adoption evidence hashes must be SHA-256")
        actors = (self.qualifier_actor_id, self.submitter_actor_id, self.approver_actor_id)
        if any(not actor.strip() for actor in actors) or len(set(actors)) != 3:
            raise ValueError("qualifier, submitter and approver must be distinct")
        if not self.decision_reference.strip() or not self.rationale.strip():
            raise ValueError("adoption decision evidence is required")

    @property
    def decision_id(self) -> str:
        return stable_id("authority-adoption:nngla:", {
            "qualificationId": self.qualification_id,
            "qualificationSha256": self.qualification_sha256,
            "city": self.city_administrative_area_id,
            "candidate": self.candidate_id,
            "candidateSha256": self.candidate_geometry_sha256,
            "parent": self.validation_parent_id,
            "parentEvidence": self.parent_evidence_id,
            "parentSha256": self.parent_geometry_sha256,
            "peers": self.peer_evidence_digest,
            "precision": self.precision_policy_sha256,
            "effectiveOn": self.effective_on,
            "qualifier": self.qualifier_actor_id,
            "submitter": self.submitter_actor_id,
            "approver": self.approver_actor_id,
            "reference": self.decision_reference,
        })


@dataclass(frozen=True, slots=True)
class CityAuthorityReceipt:
    decision_id: str
    city_administrative_area_id: str
    geometry_id: str
    assignment_id: str
    legalization_id: str
    qualification_id: str
    transaction_sha256: str

    def __post_init__(self) -> None:
        if not self.decision_id.startswith("authority-adoption:nngla:") or _ADMIN.fullmatch(self.city_administrative_area_id) is None:
            raise ValueError("authority receipt identity invalid")
        if _GEO.fullmatch(self.geometry_id) is None or _SHA.fullmatch(self.transaction_sha256) is None:
            raise ValueError("authority receipt geometry/hash invalid")


__all__ = [
    "CandidateSourceMode", "CityQualificationStatus", "FeatureQualificationStatus",
    "FabricCompletenessStatus", "PrecisionMode", "ResidualReviewStatus",
    "PrecisionPolicy", "SOURCE_EXACT_PRECISION", "GeometryEvidence", "CityCandidateEvidence",
    "CityQualificationReceipt", "UnresolvedTerritorialResidual", "FabricCompleteness",
    "CityAuthorityAdoptionRequest", "CityAuthorityReceipt", "stable_digest", "stable_id",
]
