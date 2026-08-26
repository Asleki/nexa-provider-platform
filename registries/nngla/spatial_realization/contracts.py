"""Immutable contracts for P006.7.11.15.5 governed spatial realization.

The package is additive.  Locked Bundle 19A/19B artifacts remain evidence; this
module defines the later selection-scoped reconciliation contract used to move
eligible evidence into live NNGLA geometry authority without rewriting history.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date
from enum import Enum
from hashlib import sha256
import json
import re
from typing import Mapping

_PLACE_ID = re.compile(r"^NG-PLC-\d{6}$")
_ADMIN_ID = re.compile(r"^NG-ADM-\d{6}$")
_SPATIAL_ID = re.compile(r"^NG-SPT-\d{6}$")
_GEOMETRY_ID = re.compile(r"^NG-GEO-\d{6}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")


class RootFamily(str, Enum):
    CITY = "CITY"


class DependencyRole(str, Enum):
    EXECUTION_ROOT = "EXECUTION_ROOT"
    PLACE_SUBJECT = "PLACE_SUBJECT"
    PLACE_REFERENCE_SOURCE = "PLACE_REFERENCE_SOURCE"
    EXECUTION_ADMIN_ROOT = "EXECUTION_ADMIN_ROOT"
    EXHAUSTIVE_CHILD = "EXHAUSTIVE_CHILD"
    NON_EXHAUSTIVE_OVERLAY = "NON_EXHAUSTIVE_OVERLAY"
    VALIDATION_PARENT = "VALIDATION_PARENT"
    VALIDATION_PEER = "VALIDATION_PEER"
    SUPPORTING_SPATIAL_REFERENCE = "SUPPORTING_SPATIAL_REFERENCE"
    UNCHANGED_REFERENCE = "UNCHANGED_REFERENCE"


class GeometryEncoding(str, Enum):
    GEOJSON = "GEOJSON"
    EWKB_HEX = "EWKB_HEX"


class RepairMode(str, Enum):
    DISABLED = "DISABLED"
    SAFE_AUTOMATIC = "SAFE_AUTOMATIC"
    GOVERNED_STRUCTURAL = "GOVERNED_STRUCTURAL"


class GeometryRole(str, Enum):
    PLACE_REFERENCE_POINT = "PLACE_REFERENCE_POINT"
    SETTLEMENT_FOOTPRINT = "SETTLEMENT_FOOTPRINT"
    ADMINISTRATIVE_BOUNDARY = "ADMINISTRATIVE_BOUNDARY"


class SubjectType(str, Enum):
    PLACE = "PLACE"
    ADMINISTRATIVE_AREA = "ADMINISTRATIVE_AREA"


class ReconciliationAction(str, Enum):
    CREATE_NEW = "CREATE_NEW"
    REUSE_EXISTING = "REUSE_EXISTING"
    ASSOCIATE_EXISTING = "ASSOCIATE_EXISTING"
    CREATE_SUCCESSOR = "CREATE_SUCCESSOR"
    NO_CHANGE = "NO_CHANGE"
    BLOCKED = "BLOCKED"


class FindingSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    BLOCKING = "BLOCKING"


class FindingStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    SUPERSEDED = "SUPERSEDED"


class AssessmentStage(str, Enum):
    SOURCE_CANDIDATE = "SOURCE_CANDIDATE"
    SUCCESSOR_CANDIDATE = "SUCCESSOR_CANDIDATE"


@dataclass(frozen=True, slots=True)
class CityRoot:
    place_id: str
    source_place_code: str
    canonical_name: str
    region_code: str
    administrative_area_id: str
    validation_parent_id: str

    def __post_init__(self) -> None:
        if _PLACE_ID.fullmatch(self.place_id) is None:
            raise ValueError("city root requires canonical NG-PLC identity")
        if _ADMIN_ID.fullmatch(self.administrative_area_id) is None:
            raise ValueError("city root requires canonical NG-ADM counterpart")
        if _ADMIN_ID.fullmatch(self.validation_parent_id) is None:
            raise ValueError("city root requires canonical administrative parent")
        if not self.source_place_code.startswith("NGP-") or not self.canonical_name.strip() or not self.region_code.strip():
            raise ValueError("city root source identity, name and region are required")


@dataclass(frozen=True, slots=True)
class GeometryCandidate:
    root_place_id: str
    subject_type: SubjectType
    subject_id: str
    geometry_role: GeometryRole
    source_candidate_id: str
    geometry_type_code: str
    encoding: GeometryEncoding
    payload: str
    checksum_sha256: str
    reservation_key: str
    source_dataset_id: str
    source_dataset_version: str
    source_path_reference: str
    predecessor_source_candidate_id: str = ""
    repair_policy_id: str = ""

    def __post_init__(self) -> None:
        if _PLACE_ID.fullmatch(self.root_place_id) is None:
            raise ValueError("geometry candidate requires canonical city root")
        if self.subject_type is SubjectType.PLACE:
            if _PLACE_ID.fullmatch(self.subject_id) is None:
                raise ValueError("place geometry requires NG-PLC subject")
        elif _ADMIN_ID.fullmatch(self.subject_id) is None:
            raise ValueError("administrative geometry requires NG-ADM subject")
        if self.geometry_type_code not in {"POINT", "POLYGON", "MULTIPOLYGON"}:
            raise ValueError("unsupported realization geometry type")
        if _SHA.fullmatch(self.checksum_sha256) is None:
            raise ValueError("geometry candidate checksum must be SHA-256")
        if not self.source_candidate_id.strip() or not self.reservation_key.strip():
            raise ValueError("source candidate and reservation key are required")
        if self.encoding is GeometryEncoding.EWKB_HEX:
            try:
                bytes.fromhex(self.payload)
            except ValueError as exc:
                raise ValueError("EWKB_HEX payload must be hexadecimal") from exc
        elif not self.payload.strip().startswith("{"):
            raise ValueError("GEOJSON payload must be canonical JSON text")
        if self.predecessor_source_candidate_id and not self.repair_policy_id:
            raise ValueError("successor source candidate requires repair policy identity")

    @property
    def is_source_successor(self) -> bool:
        return bool(self.predecessor_source_candidate_id)


@dataclass(frozen=True, slots=True)
class SpatialSeed:
    subject_id: str
    source_place_code: str
    place_id: str
    longitude: float
    latitude: float

    def __post_init__(self) -> None:
        if _ADMIN_ID.fullmatch(self.subject_id) is None:
            raise ValueError("territorial seed requires NG-ADM subject")
        if not self.source_place_code.startswith("NGP-") or _PLACE_ID.fullmatch(self.place_id) is None:
            raise ValueError("territorial seed requires canonical source/place identities")
        if not (-180.0 <= float(self.longitude) <= 180.0 and -90.0 <= float(self.latitude) <= 90.0):
            raise ValueError("territorial seed coordinates are outside EPSG:4326 range")


@dataclass(frozen=True, slots=True)
class Dependency:
    root_place_id: str
    role: DependencyRole
    subject_id: str
    subject_type: str
    mutable: bool


@dataclass(frozen=True, slots=True)
class CityClosure:
    root: CityRoot
    place_reference: GeometryCandidate
    settlement_footprint: GeometryCandidate | None
    admin_root: GeometryCandidate
    exhaustive_children: tuple[GeometryCandidate, ...]
    overlays: tuple[GeometryCandidate, ...]
    validation_parent: GeometryCandidate
    regional_partition_peers: tuple[GeometryCandidate, ...]
    supporting_spatial_point_id: str
    exhaustive_child_seeds: tuple[SpatialSeed, ...]
    dependencies: tuple[Dependency, ...]

    def __post_init__(self) -> None:
        if self.place_reference.subject_id != self.root.place_id:
            raise ValueError("place-reference candidate/root mismatch")
        if self.admin_root.subject_id != self.root.administrative_area_id:
            raise ValueError("administrative root mismatch")
        if self.validation_parent.subject_id != self.root.validation_parent_id:
            raise ValueError("validation parent mismatch")
        if _SPATIAL_ID.fullmatch(self.supporting_spatial_point_id) is None:
            raise ValueError("supporting spatial reference requires NG-SPT identity")
        if not self.exhaustive_children:
            raise ValueError("city realization requires exhaustive territorial children")
        if len({item.subject_id for item in self.exhaustive_children}) != len(self.exhaustive_children):
            raise ValueError("duplicate exhaustive child")
        child_ids = {item.subject_id for item in self.exhaustive_children}
        seed_ids = {item.subject_id for item in self.exhaustive_child_seeds}
        if child_ids != seed_ids or len(self.exhaustive_child_seeds) != len(self.exhaustive_children):
            raise ValueError("every exhaustive child requires exactly one canonical reference seed")

    @property
    def desired_candidates(self) -> tuple[GeometryCandidate, ...]:
        rows = [self.place_reference]
        if self.settlement_footprint is not None:
            rows.append(self.settlement_footprint)
        rows.append(self.admin_root)
        rows.extend(self.exhaustive_children)
        return tuple(rows)

    @property
    def mutable_subject_ids(self) -> frozenset[str]:
        return frozenset(item.subject_id for item in self.desired_candidates)


@dataclass(frozen=True, slots=True)
class TopologyFinding:
    finding_id: str
    root_place_id: str
    rule_code: str
    severity: FindingSeverity
    status: FindingStatus
    subject_id: str
    related_subject_id: str = ""
    geometry_role: str = ""
    predicate: str = ""
    expected: str = ""
    actual: str = ""
    assessment_stage: AssessmentStage = AssessmentStage.SOURCE_CANDIDATE
    raw_predicate_result: str = ""
    difference_dimension: int | None = None
    measurement_method: str = ""
    area_km2: float | None = None
    area_ratio: float | None = None
    residual_class: str = "NONE"
    difference_bbox: str = ""
    representative_point: str = ""
    repair_eligibility: str = "NOT_APPLICABLE"
    repair_strategy: str = ""

    @property
    def blocking(self) -> bool:
        return self.severity is FindingSeverity.BLOCKING and self.status is FindingStatus.OPEN

    def resolved(self) -> "TopologyFinding":
        return replace(self, status=FindingStatus.RESOLVED)

    def superseded(self) -> "TopologyFinding":
        return replace(self, status=FindingStatus.SUPERSEDED)


@dataclass(frozen=True, slots=True)
class TopologyAssessment:
    root_place_id: str
    candidates: tuple[GeometryCandidate, ...]
    findings: tuple[TopologyFinding, ...]
    repair_applied: bool = False

    @property
    def blocking_findings(self) -> tuple[TopologyFinding, ...]:
        return tuple(item for item in self.findings if item.blocking)

    @property
    def execution_ready(self) -> bool:
        return not self.blocking_findings


@dataclass(frozen=True, slots=True)
class PlaceTargetState:
    place_id: str
    source_place_code: str
    spatial_assignment_status: str
    geometry_reference: str | None


@dataclass(frozen=True, slots=True)
class AdminTargetState:
    administrative_area_id: str
    administrative_candidate_id: str
    source_record_id: str
    boundary_status: str
    geometry_reference: str | None
    lifecycle_status: str
    candidate_status: str


@dataclass(frozen=True, slots=True)
class TargetGeometryState:
    geometry_id: str
    subject_id: str
    geometry_role: str
    checksum_sha256: str
    valid_from: str
    qualification_status: str
    publication_status: str
    source_geometry_id: str

    def __post_init__(self) -> None:
        if _GEOMETRY_ID.fullmatch(self.geometry_id) is None:
            raise ValueError("target geometry state requires NG-GEO identity")


@dataclass(frozen=True, slots=True)
class TargetSnapshot:
    database_name: str
    environment_name: str
    places: Mapping[str, PlaceTargetState] = field(default_factory=dict)
    admins: Mapping[str, AdminTargetState] = field(default_factory=dict)
    active_geometries: Mapping[str, tuple[TargetGeometryState, ...]] = field(default_factory=dict)
    reservations: Mapping[str, tuple[str, str]] = field(default_factory=dict)
    available: bool = True

    @property
    def digest(self) -> str:
        payload = {
            "database": self.database_name,
            "environment": self.environment_name,
            "available": self.available,
            "places": [
                (key, value.source_place_code, value.spatial_assignment_status, value.geometry_reference)
                for key, value in sorted(self.places.items())
            ],
            "admins": [
                (
                    key, value.administrative_candidate_id, value.source_record_id, value.boundary_status,
                    value.geometry_reference, value.lifecycle_status, value.candidate_status,
                )
                for key, value in sorted(self.admins.items())
            ],
            "geometries": [
                (
                    subject, tuple(
                        (g.geometry_id, g.geometry_role, g.checksum_sha256, g.valid_from,
                         g.qualification_status, g.publication_status, g.source_geometry_id)
                        for g in sorted(rows, key=lambda item: (item.geometry_role, item.geometry_id))
                    )
                )
                for subject, rows in sorted(self.active_geometries.items())
            ],
            "reservations": sorted((key, tuple(value)) for key, value in self.reservations.items()),
        }
        return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class ReconciliationItem:
    root_place_id: str
    subject_id: str
    subject_type: SubjectType
    geometry_role: GeometryRole
    candidate_checksum: str
    source_candidate_id: str
    action: ReconciliationAction
    reason: str
    existing_geometry_id: str = ""


@dataclass(frozen=True, slots=True)
class SpatialRealizationPreview:
    plan_id: str
    plan_version: int
    normalized_root_ids: tuple[str, ...]
    source_sha256: str
    repository_revision: str
    database_name: str
    environment_name: str
    target_snapshot_digest: str
    topology_policy_id: str
    repair_policy_id: str
    repair_mode: str
    effective_date: str
    closures: tuple[CityClosure, ...]
    assessments: tuple[TopologyAssessment, ...]
    reconciliation: tuple[ReconciliationItem, ...]
    fingerprint: str

    def __post_init__(self) -> None:
        try:
            date.fromisoformat(self.effective_date)
        except ValueError as exc:
            raise ValueError("spatial realization preview effective_date must be ISO YYYY-MM-DD") from exc

    @property
    def blocking_findings(self) -> tuple[TopologyFinding, ...]:
        return tuple(f for assessment in self.assessments for f in assessment.blocking_findings)

    @property
    def blocked_actions(self) -> tuple[ReconciliationItem, ...]:
        return tuple(item for item in self.reconciliation if item.action is ReconciliationAction.BLOCKED)

    @property
    def execution_ready(self) -> bool:
        return bool(self.normalized_root_ids) and not self.blocking_findings and not self.blocked_actions

    @property
    def candidate_geometry_writes(self) -> int:
        return sum(item.action in {ReconciliationAction.CREATE_NEW, ReconciliationAction.CREATE_SUCCESSOR} for item in self.reconciliation)

    @property
    def candidate_associations(self) -> int:
        return sum(item.action is ReconciliationAction.ASSOCIATE_EXISTING for item in self.reconciliation) + sum(
            item.action in {ReconciliationAction.CREATE_NEW, ReconciliationAction.CREATE_SUCCESSOR}
            and item.geometry_role in {GeometryRole.PLACE_REFERENCE_POINT, GeometryRole.ADMINISTRATIVE_BOUNDARY}
            for item in self.reconciliation
        )

    @property
    def planned_geometry_writes(self) -> int:
        return self.candidate_geometry_writes if self.execution_ready else 0

    @property
    def planned_associations(self) -> int:
        return self.candidate_associations if self.execution_ready else 0


@dataclass(frozen=True, slots=True)
class SpatialRealizationExecutionReceipt:
    execution_id: str
    fingerprint_sha256: str
    database_name: str
    environment_name: str
    repository_revision: str
    submitter_actor_id: str
    approver_actor_id: str
    selected_root_count: int
    geometry_insert_count: int
    association_count: int
    reused_count: int
    status: str
    replayed: bool = False

    def __post_init__(self) -> None:
        if not self.execution_id.startswith("nnglarun:spatial-realization:"):
            raise ValueError("spatial realization execution namespace required")
        if _SHA.fullmatch(self.fingerprint_sha256) is None:
            raise ValueError("receipt fingerprint must be SHA-256")
        if not self.submitter_actor_id or not self.approver_actor_id or self.submitter_actor_id == self.approver_actor_id:
            raise ValueError("distinct submitter and approver are required")
        if self.selected_root_count < 1 or self.geometry_insert_count < 0 or self.association_count < 0 or self.reused_count < 0:
            raise ValueError("receipt counts are invalid")
        if self.status not in {"APPLIED", "REUSED"}:
            raise ValueError("receipt status must be APPLIED or REUSED")
        if (self.status == "REUSED") != self.replayed:
            raise ValueError("replay/status mismatch")


class FabricLevel(str, Enum):
    REGION_LOCAL_AREAS = "REGION_LOCAL_AREAS"
    CITY_DISTRICTS = "CITY_DISTRICTS"
    MUNICIPALITY_TOWNSHIPS = "MUNICIPALITY_TOWNSHIPS"


class FabricInputRole(str, Enum):
    PARENT = "PARENT"
    EXHAUSTIVE_SIBLING = "EXHAUSTIVE_SIBLING"
    NON_EXHAUSTIVE_OVERLAY = "NON_EXHAUSTIVE_OVERLAY"


class FaceClassification(str, Enum):
    UNIQUE_EXISTING_OWNER = "UNIQUE_EXISTING_OWNER"
    MULTIPLE_EXISTING_OWNERS = "MULTIPLE_EXISTING_OWNERS"
    MICRO_UNASSIGNED = "MICRO_UNASSIGNED"
    MATERIAL_UNASSIGNED = "MATERIAL_UNASSIGNED"
    PARENT_BOUNDARY_CONFLICT = "PARENT_BOUNDARY_CONFLICT"
    AMBIGUOUS_PROVENANCE = "AMBIGUOUS_PROVENANCE"


class FaceDecisionKind(str, Enum):
    PRESERVE_UNIQUE = "PRESERVE_UNIQUE"
    TEST_ONLY_GOVERNANCE_FIXTURE = "TEST_ONLY_GOVERNANCE_FIXTURE"
    GOVERNED_REVIEW = "GOVERNED_REVIEW"


@dataclass(frozen=True, slots=True)
class FabricRuntimeSignature:
    engine_family: str
    python_version: str
    geometry_engine_version: str
    geos_version: str
    projection_engine_version: str
    proj_version: str
    topology_crs: str
    diagnostic_crs: str
    precision_policy_id: str
    precision_grid: float | None = None

    def __post_init__(self) -> None:
        required = (
            self.engine_family, self.python_version, self.geometry_engine_version,
            self.geos_version, self.projection_engine_version, self.proj_version,
            self.topology_crs, self.diagnostic_crs, self.precision_policy_id,
        )
        if any(not str(value).strip() for value in required):
            raise ValueError("fabric runtime signature fields are required")
        if self.precision_grid is not None and float(self.precision_grid) <= 0:
            raise ValueError("precision grid must be positive when configured")

    @property
    def digest(self) -> str:
        payload = {
            "engine_family": self.engine_family,
            "python_version": self.python_version,
            "geometry_engine_version": self.geometry_engine_version,
            "geos_version": self.geos_version,
            "projection_engine_version": self.projection_engine_version,
            "proj_version": self.proj_version,
            "topology_crs": self.topology_crs,
            "diagnostic_crs": self.diagnostic_crs,
            "precision_policy_id": self.precision_policy_id,
            "precision_grid": self.precision_grid,
        }
        return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class FabricInput:
    input_role: FabricInputRole
    subject_id: str
    administrative_type_code: str
    canonical_name: str
    source_candidate_id: str
    geometry_checksum_sha256: str
    source_path_reference: str

    def __post_init__(self) -> None:
        if _ADMIN_ID.fullmatch(self.subject_id) is None:
            raise ValueError("fabric input requires canonical NG-ADM identity")
        if _SHA.fullmatch(self.geometry_checksum_sha256) is None:
            raise ValueError("fabric input geometry checksum must be SHA-256")
        if not self.administrative_type_code.strip() or not self.canonical_name.strip():
            raise ValueError("fabric input administrative type and canonical name are required")
        if not self.source_candidate_id.strip() or not self.source_path_reference.strip():
            raise ValueError("fabric input source lineage is required")


@dataclass(frozen=True, slots=True)
class ParentFabricScope:
    scope_id: str
    requested_root_place_id: str
    parent: FabricInput
    level: FabricLevel
    exhaustive_siblings: tuple[FabricInput, ...]
    overlays: tuple[FabricInput, ...]
    runtime_signature: FabricRuntimeSignature
    input_digest: str

    def __post_init__(self) -> None:
        if not self.scope_id.startswith("fabric-scope:nngla:"):
            raise ValueError("fabric scope identity namespace required")
        if _PLACE_ID.fullmatch(self.requested_root_place_id) is None:
            raise ValueError("fabric scope requires canonical requested root")
        if self.parent.input_role is not FabricInputRole.PARENT:
            raise ValueError("fabric scope parent input role mismatch")
        if not self.exhaustive_siblings:
            raise ValueError("fabric scope requires exhaustive siblings")
        if any(item.input_role is not FabricInputRole.EXHAUSTIVE_SIBLING for item in self.exhaustive_siblings):
            raise ValueError("fabric scope exhaustive sibling role mismatch")
        if any(item.input_role is not FabricInputRole.NON_EXHAUSTIVE_OVERLAY for item in self.overlays):
            raise ValueError("fabric scope overlay role mismatch")
        sibling_ids = tuple(item.subject_id for item in self.exhaustive_siblings)
        if len(set(sibling_ids)) != len(sibling_ids):
            raise ValueError("fabric scope exhaustive siblings must be unique")
        if set(sibling_ids) & {item.subject_id for item in self.overlays}:
            raise ValueError("fabric scope overlays cannot also be exhaustive owners")
        if _SHA.fullmatch(self.input_digest) is None:
            raise ValueError("fabric scope input digest must be SHA-256")

    @property
    def fingerprint(self) -> str:
        payload = {
            "scope_id": self.scope_id,
            "requested_root_place_id": self.requested_root_place_id,
            "parent": self.parent.subject_id,
            "level": self.level.value,
            "siblings": [item.subject_id for item in self.exhaustive_siblings],
            "overlays": [item.subject_id for item in self.overlays],
            "runtime": self.runtime_signature.digest,
            "input": self.input_digest,
        }
        return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class BoundaryConflictDecisionKind(str, Enum):
    TEST_ONLY_HIERARCHY_FIXTURE = "TEST_ONLY_HIERARCHY_FIXTURE"
    GOVERNED_REVIEW = "GOVERNED_REVIEW"


@dataclass(frozen=True, slots=True)
class BoundaryConflictDecision:
    defect_id: str
    defect_geometry_sha256: str
    decision_kind: BoundaryConflictDecisionKind
    decision_reference: str
    action: str
    rationale: str

    def __post_init__(self) -> None:
        if not self.defect_id.startswith("fabric-defect:nngla:"):
            raise ValueError("boundary conflict decision requires fabric-defect identity")
        if _SHA.fullmatch(self.defect_geometry_sha256) is None:
            raise ValueError("boundary conflict decision requires geometry SHA-256")
        if self.action not in {"EXCLUDE_OUTSIDE_QUALIFIED_PARENT", "REQUIRE_REVIEW"}:
            raise ValueError("unsupported boundary conflict action")
        if not self.decision_reference.strip() or not self.rationale.strip():
            raise ValueError("boundary conflict decision evidence is required")


@dataclass(frozen=True, slots=True)
class FaceAssignmentDecision:
    face_id: str
    face_geometry_sha256: str
    owner_subject_id: str
    decision_kind: FaceDecisionKind
    decision_reference: str
    rationale: str

    def __post_init__(self) -> None:
        if not self.face_id.startswith("fabric-face:nngla:"):
            raise ValueError("face assignment requires fabric-face identity")
        if _SHA.fullmatch(self.face_geometry_sha256) is None:
            raise ValueError("face assignment requires geometry SHA-256")
        if _ADMIN_ID.fullmatch(self.owner_subject_id) is None:
            raise ValueError("face assignment owner requires NG-ADM identity")
        if not self.decision_reference.strip() or not self.rationale.strip():
            raise ValueError("face assignment decision evidence is required")


__all__ = [name for name in globals() if not name.startswith("_")]
