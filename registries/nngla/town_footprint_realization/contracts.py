"""P006.7.11.15.9.3 governed TOWN multi-artifact source contracts."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

PLAN_ID = "p006.7.11.15.9.3-governed-town-footprint-realization"
PLAN_VERSION = 1
REALIZATION_VERSION = 1
CRS_CODE = "NG-CRS-EPSG4326"
RUNTIME_EFFECT_SCOPE = "SHARED_REFERENCE"
SOURCE_DATASET_ID = "dataset:novegeo:place-spatial-association"
SOURCE_DATASET_VERSION = "1"
EXPECTED_SETTLEMENT_FOOTPRINT_COUNT = 419
EXPECTED_TOWN_COUNT = 120
EXPECTED_PARENT_COUNT = 24
EXPECTED_PER_PARENT = 5
FOOTPRINT_SHA256 = "f9a9b9f87832f5bd74c277f6300ef1c203b8f202f9628f1f5dc4c9916cc41840"
REFERENCE_SHA256 = "363e3276166b165b854faff4da7ad5baf0b0b2efbcef61819a53e06fa7a2fe2f"
SOURCE_QUALIFICATION_STATUS = "QUALIFIED_CANDIDATE_NOT_LEGAL_BOUNDARY"
LEGAL_BOUNDARY_STATUS = "NOT_ADMINISTRATIVE_OR_LEGAL_BOUNDARY"
GEOMETRY_ROLE_CODE = "SETTLEMENT_FOOTPRINT"
SOURCE_BASIS = (
    "DETERMINISTIC_UNSURVEYED_SETTLEMENT_EXTENT_V1;"
    "PHYSICAL_SETTLEMENT_GEOGRAPHY_ONLY;"
    "NOT_ADMINISTRATIVE_OR_LEGAL_BOUNDARY"
)


@dataclass(frozen=True, slots=True)
class TownSourceEvidence:
    place_id: str
    canonical_name: str
    region_code: str
    source_place_code: str
    parent_source_place_code: str
    geometry_role_code: str
    legal_boundary_status: str
    qualification_status: str
    source_basis: str
    dataset_id: str
    dataset_version: str
    runtime_effect_scope: str
    source_path_reference: str
    source_dataset_sha256: str
    source_reference_sha256: str
    source_footprint_sha256: str
    source_geometry_sha256: str
    geometry_type_code: str
    geometry: dict[str, Any]


@dataclass(frozen=True, slots=True)
class TownIdentity:
    place_id: str
    canonical_name: str
    region_code: str
    source_place_code: str
    parent_source_place_code: str
    parent_place_id: str
    parent_place_type_code: str
    parent_administrative_area_id: str
    parent_municipality_geometry_id: str
    parent_municipality_geometry_sha256: str


@dataclass(frozen=True, slots=True)
class RealizedTownFootprint:
    place_id: str
    geometry_type_code: str
    geometry: dict[str, Any]
    geometry_sha256: str
    label_point: dict[str, Any]
    area_m2: float
    area_km2: float
    perimeter_m: float
    perimeter_km: float
    covered_by_parent_municipality: bool


@dataclass(frozen=True, slots=True)
class TownNationalPlan:
    database_name: str
    environment_name: str
    repository_revision: str
    effective_date: str
    source_dataset_id: str
    source_dataset_version: str
    source_dataset_sha256: str
    source_reference_sha256: str
    source_footprint_sha256: str
    town_member_set_sha256: str
    town_member_set: tuple[dict[str, str], ...]
    towns: tuple[dict[str, Any], ...]
    fingerprint: str

    @property
    def confirmation_token(self) -> str:
        return f"REALIZE-NNGLA-TOWN::{self.database_name}::{self.fingerprint}"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["planId"] = PLAN_ID
        payload["planVersion"] = PLAN_VERSION
        payload["confirmationToken"] = self.confirmation_token
        return payload


@dataclass(frozen=True, slots=True)
class TownExecutionResult:
    execution_id: str
    fingerprint: str
    database_name: str
    environment_name: str
    repository_revision: str
    status: str
    replayed: bool
    inserted_count: int
    reused_count: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
