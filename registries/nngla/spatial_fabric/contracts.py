"""P006.7.11.7.1/.2 additive spatial-fabric contracts.

Bundle 17A classifies immutable source evidence and derives deterministic
coordinate/topology candidates.  It does not write PostgreSQL and does not
change the locked P006.7.2-P006.7.11.6 domain contracts.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
import re

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class SpatialSourceClassification(str, Enum):
    EXISTING_SPATIAL_V001 = "EXISTING_SPATIAL_V001"


class SpatialEvidenceRole(str, Enum):
    SPATIAL_REFERENCE_GRID = "SPATIAL_REFERENCE_GRID"
    SPATIAL_REFERENCE_POINT = "SPATIAL_REFERENCE_POINT"
    ENVIRONMENTAL_REFERENCE_CELL = "ENVIRONMENTAL_REFERENCE_CELL"
    ENVIRONMENT_OBSERVATION = "ENVIRONMENT_OBSERVATION"
    ENVIRONMENT_SYSTEM = "ENVIRONMENT_SYSTEM"
    SOVEREIGN_PART_REFERENCE = "SOVEREIGN_PART_REFERENCE"
    SOVEREIGN_GEOMETRY_EVIDENCE = "SOVEREIGN_GEOMETRY_EVIDENCE"
    SOVEREIGN_BOUNDARY_SEGMENT_EVIDENCE = "SOVEREIGN_BOUNDARY_SEGMENT_EVIDENCE"
    EXISTING_PHYSICAL_FEATURE_REFERENCE = "EXISTING_PHYSICAL_FEATURE_REFERENCE"
    PHYSICAL_GEOMETRY_EVIDENCE = "PHYSICAL_GEOMETRY_EVIDENCE"
    HYDROLOGY_NETWORK_REFERENCE = "HYDROLOGY_NETWORK_REFERENCE"
    DOMAIN_QUALIFIED_FEATURE_CANDIDATE = "DOMAIN_QUALIFIED_FEATURE_CANDIDATE"
    SPATIAL_ASSOCIATION_REQUIREMENT = "SPATIAL_ASSOCIATION_REQUIREMENT"
    GEOMETRY_VERTEX_PLACEHOLDER = "GEOMETRY_VERTEX_PLACEHOLDER"
    MARINE_PHYSICAL_REFERENCE = "MARINE_PHYSICAL_REFERENCE"
    MARINE_GEOMETRY_EVIDENCE = "MARINE_GEOMETRY_EVIDENCE"
    MARINE_RELATIONSHIP = "MARINE_RELATIONSHIP"
    MARINE_NAME_REFERENCE = "MARINE_NAME_REFERENCE"


class AllowedMigrationAction(str, Enum):
    QUALIFY_ONLY = "QUALIFY_ONLY"
    RECONCILE_ONLY = "RECONCILE_ONLY"
    ASSOCIATE_ONLY = "ASSOCIATE_ONLY"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    NO_DIRECT_MIGRATION = "NO_DIRECT_MIGRATION"


@dataclass(frozen=True, slots=True)
class SpatialSourceManifestEntry:
    source_file_id: str
    filename: str
    source_path: str
    source_family: str
    dataset_id: str
    dataset_version: str
    source_sha256: str
    record_count: int
    classification: SpatialSourceClassification
    evidence_role: SpatialEvidenceRole
    contains_coordinates: bool
    contains_geometry: bool
    contains_names: bool
    already_canonical_domain: str
    allowed_migration_action: AllowedMigrationAction
    status: str

    def __post_init__(self) -> None:
        if re.fullmatch(r"NG-SPFILE-\d{3}", self.source_file_id) is None:
            raise ValueError("source_file_id must use NG-SPFILE-NNN")
        if not self.filename.endswith(".csv"):
            raise ValueError("Bundle 17A manifest sources must be CSV files")
        if not self.source_path.startswith("data/novegeo/nngla/spatial-fabric/source/"):
            raise ValueError("source_path must stay inside the additive spatial-fabric source family")
        if not self.dataset_id.startswith("dataset:"):
            raise ValueError("dataset_id must use dataset: namespace")
        if not _SHA256.fullmatch(self.source_sha256):
            raise ValueError("source_sha256 must contain 64 lowercase hex characters")
        if self.record_count < 0:
            raise ValueError("record_count cannot be negative")
        if self.status != "ACTIVE_SOURCE_EVIDENCE":
            raise ValueError("Bundle 17A source manifest entries must be ACTIVE_SOURCE_EVIDENCE")


@dataclass(frozen=True, slots=True)
class CoordinateOccurrence:
    coordinate_occurrence_id: str
    source_file_id: str
    source_record_id: str
    parent_object_type: str
    parent_object_id: str
    geometry_role: str
    ring_id: str
    vertex_sequence: str
    source_longitude_text: str
    source_latitude_text: str
    source_longitude_numeric: Decimal
    source_latitude_numeric: Decimal
    crs_source_code: str
    source_version: str

    def __post_init__(self) -> None:
        if re.fullmatch(r"coordocc:nngla:[0-9a-f]{64}", self.coordinate_occurrence_id) is None:
            raise ValueError("invalid coordinate occurrence identity")
        if not self.source_file_id or not self.source_record_id:
            raise ValueError("source file and record identities are required")
        if not (Decimal("-180") <= self.source_longitude_numeric <= Decimal("180")):
            raise ValueError("longitude outside EPSG:4326 numeric range")
        if not (Decimal("-90") <= self.source_latitude_numeric <= Decimal("90")):
            raise ValueError("latitude outside EPSG:4326 numeric range")


@dataclass(frozen=True, slots=True)
class CoordinateCandidate:
    coordinate_candidate_id: str
    canonical_longitude: Decimal
    canonical_latitude: Decimal
    governed_crs_code: str
    occurrence_count: int
    land_marine_classification: str
    canonicalization_status: str

    def __post_init__(self) -> None:
        if re.fullmatch(r"coordcand:nngla:[0-9a-f]{64}", self.coordinate_candidate_id) is None:
            raise ValueError("invalid coordinate candidate identity")
        if self.governed_crs_code != "NG-CRS-EPSG4326":
            raise ValueError("Bundle 17A candidates use the locked default NoveGeo CRS contract")
        if self.occurrence_count < 1:
            raise ValueError("coordinate candidate must have at least one occurrence")
        if self.land_marine_classification != "UNRESOLVED_PENDING_17B":
            raise ValueError("Bundle 17A must defer land/marine qualification to Bundle 17B")
        if self.canonicalization_status != "CANDIDATE_ONLY_NOT_PERSISTED":
            raise ValueError("Bundle 17A coordinate candidates are not canonical PostgreSQL records")


@dataclass(frozen=True, slots=True)
class SpatialNeighborTopology:
    spatial_reference_id: str
    north_id: str
    north_east_id: str
    east_id: str
    south_east_id: str
    south_id: str
    south_west_id: str
    west_id: str
    north_west_id: str
    topology_basis: str
    topology_status: str

    def __post_init__(self) -> None:
        if not self.spatial_reference_id:
            raise ValueError("spatial_reference_id is required")
        if self.topology_status not in {"VALID", "INVALID"}:
            raise ValueError("topology_status must be VALID or INVALID")


COORDINATE_FIELD_PAIRS: tuple[tuple[str, str, str], ...] = (
    ("longitude", "latitude", "POINT"),
    ("centre_longitude", "centre_latitude", "REFERENCE_CENTRE"),
    ("reference_longitude", "reference_latitude", "REFERENCE_POINT"),
    ("candidate_reference_longitude", "candidate_reference_latitude", "CANDIDATE_REFERENCE_POINT"),
    ("start_longitude", "start_latitude", "SEGMENT_START"),
    ("end_longitude", "end_latitude", "SEGMENT_END"),
)


def parse_decimal(value: str) -> Decimal:
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid decimal coordinate {value!r}") from exc
    if not parsed.is_finite():
        raise ValueError("coordinate must be finite")
    return parsed


def canonical_decimal_text(value: Decimal) -> str:
    if value == 0:
        return "0"
    text = format(value.normalize(), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


__all__ = [
    "SpatialSourceClassification",
    "SpatialEvidenceRole",
    "AllowedMigrationAction",
    "SpatialSourceManifestEntry",
    "CoordinateOccurrence",
    "CoordinateCandidate",
    "SpatialNeighborTopology",
    "COORDINATE_FIELD_PAIRS",
    "parse_decimal",
    "canonical_decimal_text",
]
