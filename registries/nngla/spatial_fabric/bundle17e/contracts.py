"""Bundle 17E canonical persistence, preview and execution contracts."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json
import re
from collections.abc import Mapping


class SpatialMigrationAction(str, Enum):
    INSERT_NEW = "INSERT_NEW"
    RECONCILE_ONLY = "RECONCILE_ONLY"
    ASSOCIATE_ONLY = "ASSOCIATE_ONLY"
    REUSE_CANONICAL = "REUSE_CANONICAL"
    SUPERSEDE_GEOMETRY = "SUPERSEDE_GEOMETRY"
    QUARANTINE = "QUARANTINE"
    NO_ACTION = "NO_ACTION"


@dataclass(frozen=True, slots=True)
class SpatialCanonicalCrosswalk:
    spatial_crosswalk_id: str
    coordinate_candidate_id: str
    canonical_spatial_point_id: str
    canonical_version: int
    crosswalk_basis: str
    identity_origin: str
    source_dataset_id: str
    source_dataset_version: str
    source_artifact_sha256: str
    occurrence_crosswalk_sha256: str
    runtime_mode: str
    effect_scope: str
    status: str

    def __post_init__(self) -> None:
        if not self.spatial_crosswalk_id.startswith("crosswalk:nngla:"):
            raise ValueError("invalid spatial crosswalk identity")
        if not self.coordinate_candidate_id.startswith("coordcand:nngla:"):
            raise ValueError("invalid coordinate candidate identity")
        if re.fullmatch(r"NG-SPT-\d{6}", self.canonical_spatial_point_id) is None:
            raise ValueError("invalid canonical spatial point identity")
        if self.canonical_version != 1 or self.status != "QUALIFIED_FOR_PERSISTENCE":
            raise ValueError("initial spatial canonical crosswalk must be qualified version 1")
        for digest in (self.source_artifact_sha256, self.occurrence_crosswalk_sha256):
            if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                raise ValueError("spatial crosswalk provenance digests must be SHA-256")
        if self.runtime_mode != "production" or self.effect_scope != "SHARED_REFERENCE":
            raise ValueError("Bundle 17E bootstrap spatial truth is production-governed shared reference")


@dataclass(frozen=True, slots=True)
class GeometryAssignmentCandidate:
    geometry_assignment_candidate_id: str
    coordinate_candidate_id: str
    canonical_spatial_point_id: str
    geometry_id: str
    geometry_role_code: str
    geometry_type_code: str
    longitude: str
    latitude: str
    crs_code: str
    source_sha256: str
    geometry_payload_sha256: str
    valid_from: str
    valid_to: str
    supersedes_geometry_id: str
    assignment_status: str
    runtime_effect_scope: str

    def __post_init__(self) -> None:
        if not self.geometry_assignment_candidate_id.startswith("geoassign:nngla:"):
            raise ValueError("invalid geometry assignment candidate identity")
        if re.fullmatch(r"NG-SPT-\d{6}", self.canonical_spatial_point_id) is None:
            raise ValueError("invalid spatial point identity")
        if re.fullmatch(r"NG-GEO-\d{6}", self.geometry_id) is None:
            raise ValueError("invalid geometry identity")
        if self.geometry_role_code != "SPATIAL_REFERENCE_POINT" or self.geometry_type_code != "POINT":
            raise ValueError("Bundle 17E canonical fabric persists point geometries only")
        if self.crs_code != "NG-CRS-EPSG4326":
            raise ValueError("Bundle 17E canonical point geometry must use governed WGS84")
        if self.supersedes_geometry_id:
            raise ValueError("initial spatial-point geometry assignment cannot supersede earlier geometry")
        if self.assignment_status != "QUALIFIED_CANDIDATE" or self.runtime_effect_scope != "SHARED_REFERENCE":
            raise ValueError("invalid geometry assignment status/effect scope")
        for digest in (self.source_sha256, self.geometry_payload_sha256):
            if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                raise ValueError("geometry provenance digests must be SHA-256")


@dataclass(frozen=True, slots=True)
class EffectiveDatedSpatialAssignment:
    spatial_assignment_id: str
    subject_type: str
    subject_id: str
    geometry_id: str
    geometry_role_code: str
    effective_from: str
    effective_to: str
    assignment_version: int
    assignment_status: str
    runtime_effect_scope: str
    provenance_reference: str

    def __post_init__(self) -> None:
        if not self.spatial_assignment_id.startswith("spassign:nngla:"):
            raise ValueError("invalid effective-dated spatial assignment identity")
        if self.subject_type != "SPATIAL_REFERENCE_POINT":
            raise ValueError("Bundle 17E initial assignments are spatial reference points")
        if self.assignment_version != 1 or self.assignment_status != "QUALIFIED_FOR_PERSISTENCE":
            raise ValueError("initial assignment must be qualified version 1")
        if self.effective_to:
            raise ValueError("initial active spatial assignment cannot be closed")


@dataclass(frozen=True, slots=True)
class PersistenceQualificationResult:
    persistence_qualification_id: str
    coordinate_candidate_id: str
    canonical_spatial_point_id: str
    geometry_id: str
    migration_action: SpatialMigrationAction
    source_verified: bool
    coordinate_valid: bool
    map_reconciled: bool
    crs_valid: bool
    precision_valid: bool
    containment_valid: bool
    topology_valid: bool
    topology_applicability: str
    environment_resolved: bool
    environment_applicability: str
    conflict_free: bool
    conflict_applicability: str
    canonical_id_stable: bool
    geometry_assignment_valid: bool
    crosswalk_valid: bool
    effective_dating_valid: bool
    qualification_status: str
    findings: str
    runtime_effect_scope: str

    def __post_init__(self) -> None:
        if re.fullmatch(r"NG-SPPERSIST-\d{7}", self.persistence_qualification_id) is None:
            raise ValueError("invalid spatial persistence qualification identity")
        if self.qualification_status not in {"PASS", "FAIL"}:
            raise ValueError("qualification status must be PASS or FAIL")
        if self.runtime_effect_scope != "SHARED_REFERENCE":
            raise ValueError("Bundle 17E persistence qualification is shared reference")


@dataclass(frozen=True, slots=True)
class TargetSpatialSnapshot:
    database_name: str
    environment_name: str
    schema_capabilities: frozenset[str] = frozenset()
    occupied_spatial_ids: frozenset[str] = frozenset()
    occupied_geometry_ids: frozenset[str] = frozenset()
    candidate_crosswalks: Mapping[str, str] = field(default_factory=dict)
    geometry_by_subject: Mapping[str, str] = field(default_factory=dict)
    available: bool = True

    @classmethod
    def unavailable(cls) -> "TargetSpatialSnapshot":
        return cls("UNRESOLVED", "UNRESOLVED", available=False)

    @property
    def digest(self) -> str:
        payload = {
            "database_name": self.database_name,
            "environment_name": self.environment_name,
            "schema_capabilities": sorted(self.schema_capabilities),
            "occupied_spatial_ids": sorted(self.occupied_spatial_ids),
            "occupied_geometry_ids": sorted(self.occupied_geometry_ids),
            "candidate_crosswalks": sorted((str(k), str(v)) for k, v in self.candidate_crosswalks.items()),
            "geometry_by_subject": sorted((str(k), str(v)) for k, v in self.geometry_by_subject.items()),
            "available": self.available,
        }
        return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class SpatialQualificationResult:
    coordinate_candidate_id: str
    canonical_spatial_point_id: str
    geometry_id: str
    migration_action: SpatialMigrationAction
    selected: bool
    source_verified: bool
    coordinate_valid: bool
    map_reconciled: bool
    crs_valid: bool
    precision_valid: bool
    containment_valid: bool
    topology_valid: bool
    environment_resolved: bool
    conflict_free: bool
    qualified: bool
    quarantined: bool
    quarantine_reason: str
    database_writes: int
    fingerprint: str


@dataclass(frozen=True, slots=True)
class SpatialBatchPreview:
    batch_id: str
    selected_count: int
    qualified_count: int
    quarantined_count: int
    insert_new_count: int
    reuse_count: int
    database_writes: int
    database_name: str
    environment_name: str
    repository_revision: str
    target_snapshot_digest: str
    content_fingerprint: str
    fingerprint: str
    source_sha256: str
    schema_ready: bool
    execution_ready: bool
    items: tuple[SpatialQualificationResult, ...]


@dataclass(frozen=True, slots=True)
class SpatialExecutionItem:
    coordinate_candidate_id: str
    canonical_spatial_point_id: str
    geometry_id: str
    outcome: str
    detail: str = ""


@dataclass(frozen=True, slots=True)
class SpatialExecutionReceipt:
    execution_id: str
    plan_id: str
    plan_version: int
    fingerprint: str
    content_fingerprint: str
    database_name: str
    environment_name: str
    runtime_mode: str
    repository_revision: str
    source_sha256: str
    submitter_actor_id: str
    approver_actor_id: str
    selected_count: int
    inserted_count: int
    reused_count: int
    quarantined_count: int
    failed_count: int
    status: str
    started_at: str
    completed_at: str
    items: tuple[SpatialExecutionItem, ...]

    def __post_init__(self) -> None:
        if not self.execution_id.startswith("nnglarun:spatial:"):
            raise ValueError("invalid spatial execution identity")
        if self.submitter_actor_id == self.approver_actor_id:
            raise ValueError("submitter and approver must remain separate")
        if self.selected_count != self.inserted_count + self.reused_count + self.quarantined_count + self.failed_count:
            raise ValueError("spatial execution counts do not reconcile")
        if self.status not in {"APPLIED", "REUSED", "FAILED"}:
            raise ValueError("invalid spatial execution status")


__all__ = [
    "SpatialMigrationAction", "SpatialCanonicalCrosswalk", "GeometryAssignmentCandidate",
    "EffectiveDatedSpatialAssignment", "PersistenceQualificationResult", "TargetSpatialSnapshot",
    "SpatialQualificationResult", "SpatialBatchPreview", "SpatialExecutionItem", "SpatialExecutionReceipt",
]
