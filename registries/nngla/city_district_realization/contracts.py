"""P006.7.11.15.9.2 governed CITY_DISTRICT realization contracts."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

PLAN_ID = "p006.7.11.15.9.2-governed-city-district-realization"
PLAN_VERSION = 1
REALIZATION_VERSION = 1
CRS_CODE = "NG-CRS-EPSG4326"
RUNTIME_EFFECT_SCOPE = "SHARED_REFERENCE"
EXPECTED_CITY_DISTRICT_COUNT = 64
EXPECTED_PER_CITY = 8
SOURCE_DATASET_ID = "dataset:novegeo:administrative-boundaries"
SOURCE_DATASET_VERSION = "1"
SOURCE_DATASET_SHA256 = "ba94b04edf9b1d63774b74548b844f5c2bf18bf9e9123f6ecf904eaa94678278"


@dataclass(frozen=True, slots=True)
class CityDistrictSourceEvidence:
    administrative_area_id: str
    canonical_name: str
    region_code: str
    source_record_id: str
    parent_source_record_id: str
    source_dataset_id: str
    source_dataset_version: str
    source_path_reference: str
    source_dataset_sha256: str
    source_geometry_sha256: str
    geometry_type_code: str
    geometry: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ParentCityAuthority:
    city_id: str
    canonical_name: str
    region_code: str
    source_record_id: str
    city_geometry_id: str
    geometry_sha256: str


@dataclass(frozen=True, slots=True)
class CityDistrictIdentity:
    administrative_area_id: str
    canonical_name: str
    region_code: str
    source_record_id: str
    parent_source_record_id: str


@dataclass(frozen=True, slots=True)
class RealizedCityDistrict:
    district_id: str
    realization_method: str
    geometry_type_code: str
    geometry: dict[str, Any]
    geometry_sha256: str
    label_point: dict[str, Any]
    area_m2: float
    area_km2: float
    perimeter_m: float
    perimeter_km: float


@dataclass(frozen=True, slots=True)
class CityDistrictPlan:
    database_name: str
    environment_name: str
    repository_revision: str
    effective_date: str
    parent_city_id: str
    parent_city_name: str
    region_code: str
    parent_city_source_record_id: str
    parent_city_geometry_id: str
    parent_city_geometry_sha256: str
    partition_qualification_id: str
    district_geometry_set_sha256: str
    district_member_set: tuple[dict[str, str], ...]
    districts: tuple[dict[str, Any], ...]
    partition: dict[str, Any]
    fingerprint: str

    @property
    def confirmation_token(self) -> str:
        return f"REALIZE-NNGLA-CITY-DISTRICT::{self.database_name}::{self.fingerprint}"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["planId"] = PLAN_ID
        payload["planVersion"] = PLAN_VERSION
        payload["confirmationToken"] = self.confirmation_token
        return payload


@dataclass(frozen=True, slots=True)
class CityDistrictExecutionResult:
    execution_id: str
    fingerprint: str
    parent_city_id: str
    database_name: str
    environment_name: str
    repository_revision: str
    status: str
    replayed: bool
    inserted_count: int
    reused_count: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
