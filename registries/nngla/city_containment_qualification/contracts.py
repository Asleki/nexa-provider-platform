"""Contracts for P006.7.11.15.8.1 CITY parent-containment qualification.

This maintenance revision does not introduce a second CITY geometry authority.
It records deterministic containment evidence for the already-approved v1 CITY
realization model and permits publication only when that evidence qualifies.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


CONTAINMENT_PLAN_ID = "p006.7.11.15.8.1-city-parent-containment-qualification"
CONTAINMENT_PLAN_VERSION = 1
QUALIFICATION_POLICY_VERSION = 1
ABSOLUTE_RESIDUE_MAX_M2 = 0.001
RATIO_RESIDUE_MAX = 1e-12


class QualificationStatus(str, Enum):
    QUALIFIED = "QUALIFIED"
    REJECTED = "REJECTED"


class QualificationBasis(str, Enum):
    STRICT_SOURCE_COVERED = "STRICT_SOURCE_COVERED"
    SINGLE_INTERSECTION_STRICT_COVERED = "SINGLE_INTERSECTION_STRICT_COVERED"
    SINGLE_INTERSECTION_ZERO_AREA_DIFFERENCE = "SINGLE_INTERSECTION_ZERO_AREA_DIFFERENCE"
    SINGLE_INTERSECTION_NUMERICAL_RESIDUE = "SINGLE_INTERSECTION_NUMERICAL_RESIDUE"
    REJECTED_INVALID_SOURCE = "REJECTED_INVALID_SOURCE"
    REJECTED_INVALID_REALIZATION = "REJECTED_INVALID_REALIZATION"
    REJECTED_EMPTY_REALIZATION = "REJECTED_EMPTY_REALIZATION"
    REJECTED_NON_POLYGONAL_REALIZATION = "REJECTED_NON_POLYGONAL_REALIZATION"
    REJECTED_LABEL_POINT = "REJECTED_LABEL_POINT"
    REJECTED_RESIDUE_EXCEEDS_POLICY = "REJECTED_RESIDUE_EXCEEDS_POLICY"


@dataclass(frozen=True, slots=True)
class ContainmentEvidence:
    source_valid: bool
    source_non_empty: bool
    source_geometry_type: str
    source_strict_covered: bool
    source_area_m2: float
    source_outside_parent_m2: float
    source_outside_parent_ratio: float
    normalized_valid: bool
    normalized_non_empty: bool
    normalized_geometry_type: str
    normalized_strict_covered: bool
    normalized_area_m2: float
    normalized_outside_parent_m2: float
    normalized_outside_parent_ratio: float
    perimeter_m: float
    label_point_covered: bool
    geometry: dict[str, Any]
    label_point: dict[str, Any]
    geometry_sha256: str
    realization_method: str
    area_removed_m2: float
    area_removed_ratio: float
    qualification_status: QualificationStatus
    qualification_basis: QualificationBasis


@dataclass(frozen=True, slots=True)
class CityContainmentQualificationPlan:
    database_name: str
    environment_name: str
    repository_revision: str
    effective_date: str
    city_id: str
    canonical_name: str
    region_code: str
    source_record_id: str
    boundary_candidate_id: str
    source_dataset_id: str
    source_dataset_version: str
    source_path_reference: str
    source_dataset_sha256: str
    source_geometry_sha256: str
    parent_region_id: str
    parent_region_name: str
    parent_region_geometry_id: str
    parent_region_geometry_sha256: str
    realization_method: str
    realization_version: int
    city_geometry_id: str
    publication_id: str
    planned_action: str
    geometry_type_code: str
    crs_code: str
    geometry: dict[str, Any]
    geometry_sha256: str
    label_point: dict[str, Any]
    source_valid: bool
    source_non_empty: bool
    source_geometry_type: str
    source_strict_covered: bool
    source_area_m2: float
    source_outside_parent_m2: float
    source_outside_parent_ratio: float
    normalized_valid: bool
    normalized_non_empty: bool
    normalized_geometry_type: str
    normalized_strict_covered: bool
    normalized_outside_parent_m2: float
    normalized_outside_parent_ratio: float
    area_m2: float
    area_km2: float
    perimeter_m: float
    perimeter_km: float
    area_removed_m2: float
    area_removed_ratio: float
    label_point_covered: bool
    qualification_id: str
    qualification_status: str
    qualification_basis_code: str
    qualification_policy_version: int
    absolute_residue_max_m2: float
    ratio_residue_max: float
    fingerprint: str

    @property
    def confirmation_token(self) -> str:
        return f"QUALIFY-NNGLA-CITY::{self.database_name}::{self.fingerprint}"

    @property
    def public_ready(self) -> bool:
        return self.qualification_status == QualificationStatus.QUALIFIED.value

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["planId"] = CONTAINMENT_PLAN_ID
        payload["planVersion"] = CONTAINMENT_PLAN_VERSION
        payload["confirmationToken"] = self.confirmation_token
        payload["publicReady"] = self.public_ready
        return payload


@dataclass(frozen=True, slots=True)
class CityContainmentExecutionResult:
    execution_id: str
    fingerprint: str
    city_id: str
    qualification_id: str
    qualification_status: str
    qualification_basis_code: str
    city_geometry_id: str
    publication_id: str
    database_name: str
    environment_name: str
    repository_revision: str
    status: str
    replayed: bool
    inserted_geometry_count: int
    inserted_qualification_count: int
    inserted_publication_count: int
    reused_geometry_count: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
