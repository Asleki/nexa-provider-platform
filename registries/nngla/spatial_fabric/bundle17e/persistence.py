"""Additive Bundle 17E persistence adapters over the locked Bundle 16 PostgreSQL foundation."""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import json

from ._shared import (
    EFFECT_SCOPE,
    REQUIRED_SCHEMA_CAPABILITIES,
    RUNTIME_MODE,
    SPATIAL_DATASET_ID,
    SPATIAL_DATASET_VERSION,
    stable_id,
)
from .contracts import (
    GeometryAssignmentCandidate,
    SpatialCanonicalCrosswalk,
    SpatialExecutionReceipt,
    TargetSpatialSnapshot,
)


class MemorySpatialRepository:
    """Deterministic transaction-capable repository used for tests and dry engineering qualification."""

    def __init__(self, database_name: str = "memory_novegeo", environment_name: str = "test") -> None:
        self.database_name = database_name
        self.environment_name = environment_name
        self.spatial_points: dict[str, dict[str, str]] = {}
        self.geometries: dict[str, dict[str, str]] = {}
        self.crosswalks: dict[str, str] = {}
        self.geometry_by_subject: dict[str, str] = {}
        self.receipts: list[SpatialExecutionReceipt] = []

    def snapshot(self) -> TargetSpatialSnapshot:
        return TargetSpatialSnapshot(
            self.database_name,
            self.environment_name,
            REQUIRED_SCHEMA_CAPABILITIES,
            frozenset(self.spatial_points),
            frozenset(self.geometries),
            dict(self.crosswalks),
            dict(self.geometry_by_subject),
            True,
        )

    @contextmanager
    def transaction(self):
        backup = (
            deepcopy(self.spatial_points),
            deepcopy(self.geometries),
            deepcopy(self.crosswalks),
            deepcopy(self.geometry_by_subject),
            list(self.receipts),
        )
        try:
            yield self
        except Exception:
            (
                self.spatial_points,
                self.geometries,
                self.crosswalks,
                self.geometry_by_subject,
                self.receipts,
            ) = backup
            raise

    def persist_point(self, crosswalk: SpatialCanonicalCrosswalk, geometry: GeometryAssignmentCandidate) -> str:
        candidate_id = crosswalk.coordinate_candidate_id
        canonical_id = crosswalk.canonical_spatial_point_id
        geometry_id = geometry.geometry_id
        if candidate_id in self.crosswalks:
            if self.crosswalks[candidate_id] == canonical_id and self.geometry_by_subject.get(canonical_id) == geometry_id:
                return "REUSED"
            raise ValueError("memory target crosswalk conflict")
        if canonical_id in self.spatial_points or geometry_id in self.geometries:
            raise ValueError("memory target identifier collision")
        self.spatial_points[canonical_id] = {
            "feature_id": canonical_id,
            "record_family": "SPATIAL_REFERENCE_POINT",
            "runtime_mode": RUNTIME_MODE,
            "effect_scope": EFFECT_SCOPE,
        }
        self.geometries[geometry_id] = {
            "geometry_id": geometry_id,
            "subject_id": canonical_id,
            "longitude": geometry.longitude,
            "latitude": geometry.latitude,
        }
        self.crosswalks[candidate_id] = canonical_id
        self.geometry_by_subject[canonical_id] = geometry_id
        return "INSERTED"

    def persist_execution_receipt(self, receipt: SpatialExecutionReceipt) -> None:
        self.receipts.append(receipt)


class PostgreSQLSpatialRepository:
    """PostgreSQL/PostGIS adapter that inserts only into the already-locked generic NNGLA persistence tables."""

    _CAPABILITY_RELATIONS = {
        "nngla_execution_foundation": "geography.nngla_execution_receipt",
        "nngla_spatial_feature": "geography.nngla_spatial_feature",
        "nngla_geometry_version": "geography.nngla_geometry_version",
        "nngla_geometry_authority_record": "geography.nngla_geometry_authority_record",
        "nngla_canonical_crosswalk": "geography.nngla_canonical_crosswalk",
    }

    def __init__(self, connection) -> None:
        self.connection = connection

    def snapshot(self, database_name: str = "npp", environment_name: str = "unknown") -> TargetSpatialSnapshot:
        capabilities: set[str] = set()
        occupied_spatial: set[str] = set()
        occupied_geometry: set[str] = set()
        candidate_crosswalks: dict[str, str] = {}
        geometry_by_subject: dict[str, str] = {}
        with self.connection.cursor() as cur:
            for capability, relation in self._CAPABILITY_RELATIONS.items():
                cur.execute("SELECT to_regclass(%s) IS NOT NULL", (relation,))
                if bool(cur.fetchone()[0]):
                    capabilities.add(capability)
            if "nngla_spatial_feature" in capabilities:
                cur.execute("SELECT DISTINCT feature_id FROM geography.nngla_spatial_feature WHERE record_family='SPATIAL_REFERENCE_POINT'")
                occupied_spatial.update(str(row[0]) for row in cur.fetchall())
            if "nngla_geometry_authority_record" in capabilities:
                cur.execute("SELECT geometry_id FROM geography.nngla_geometry_authority_record")
                occupied_geometry.update(str(row[0]) for row in cur.fetchall())
            if "nngla_canonical_crosswalk" in capabilities:
                cur.execute(
                    "SELECT candidate_id, canonical_id FROM geography.nngla_canonical_crosswalk "
                    "WHERE dataset_id=%s AND dataset_version=%s AND runtime_mode=%s AND effect_scope=%s",
                    (SPATIAL_DATASET_ID, SPATIAL_DATASET_VERSION, RUNTIME_MODE, EFFECT_SCOPE),
                )
                candidate_crosswalks.update((str(row[0]), str(row[1])) for row in cur.fetchall())
            if "nngla_geometry_version" in capabilities:
                cur.execute(
                    "SELECT subject_id, geometry_id FROM geography.nngla_geometry_version "
                    "WHERE geometry_role_code='SPATIAL_REFERENCE_POINT' AND runtime_mode=%s AND valid_to IS NULL",
                    (RUNTIME_MODE,),
                )
                geometry_by_subject.update((str(row[0]), str(row[1])) for row in cur.fetchall())
        return TargetSpatialSnapshot(
            database_name,
            environment_name,
            frozenset(capabilities),
            frozenset(occupied_spatial),
            frozenset(occupied_geometry),
            candidate_crosswalks,
            geometry_by_subject,
            True,
        )

    @contextmanager
    def transaction(self):
        try:
            yield self
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def ensure_source_contract(self, source_sha256: str, source_path: str, row_count: int, byte_size: int) -> None:
        source_artifact_id = stable_id("sourceart:nngla:", SPATIAL_DATASET_ID, SPATIAL_DATASET_VERSION, source_sha256)
        with self.connection.cursor() as cur:
            cur.execute(
                "INSERT INTO geography.nngla_source_dataset"
                "(dataset_id,dataset_version,dataset_class,migration_eligibility,data_classification,source_authority) "
                "VALUES(%s,%s,'REAL_POPULATED_DATASET','READY_FOR_MIGRATION_PLANNING','PUBLIC_REFERENCE','NNGLA') "
                "ON CONFLICT(dataset_id,dataset_version) DO NOTHING",
                (SPATIAL_DATASET_ID, SPATIAL_DATASET_VERSION),
            )
            cur.execute(
                "INSERT INTO geography.nngla_source_artifact"
                "(source_artifact_id,dataset_id,dataset_version,file_path,sha256,byte_size,row_count) "
                "VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(source_artifact_id) DO NOTHING",
                (source_artifact_id, SPATIAL_DATASET_ID, SPATIAL_DATASET_VERSION, source_path, source_sha256, byte_size, row_count),
            )

    def persist_point(self, crosswalk: SpatialCanonicalCrosswalk, geometry: GeometryAssignmentCandidate) -> str:
        canonical_id = crosswalk.canonical_spatial_point_id
        with self.connection.cursor() as cur:
            cur.execute(
                "INSERT INTO geography.nngla_spatial_feature"
                "(feature_id,runtime_mode,effect_scope,record_family,lifecycle_status,effective_from,effective_to,canonical_version,data_classification) "
                "VALUES(%s,%s,%s,'SPATIAL_REFERENCE_POINT','ACTIVE',%s,NULL,1,'PUBLIC_REFERENCE') "
                "ON CONFLICT(feature_id,runtime_mode,canonical_version) DO NOTHING",
                (canonical_id, RUNTIME_MODE, EFFECT_SCOPE, geometry.valid_from),
            )
            cur.execute(
                "INSERT INTO geography.nngla_geometry_authority_record"
                "(geometry_id,subject_type,subject_id,geometry_role_code,source_geometry_id,source_dataset_id,source_version,"
                "geometry_type_code,crs_code,authoritative_level,vertex_count,part_count,valid_from,valid_to,supersedes_geometry_id,"
                "superseded_by_geometry_id,qualification_status,publication_status,checksum_sha256,source_path_reference,runtime_effect_scope) "
                "VALUES(%s,'SPATIAL_REFERENCE_POINT',%s,'SPATIAL_REFERENCE_POINT',%s,%s,%s,'POINT','NG-CRS-EPSG4326',"
                "'CANONICAL_SPATIAL_REFERENCE',1,1,%s,NULL,NULL,NULL,'QUALIFIED','NOT_PUBLISHED',%s,%s,%s) "
                "ON CONFLICT(geometry_id) DO NOTHING",
                (
                    geometry.geometry_id, canonical_id, geometry.coordinate_candidate_id, SPATIAL_DATASET_ID,
                    SPATIAL_DATASET_VERSION, geometry.valid_from, geometry.geometry_payload_sha256,
                    "data/novegeo/nngla/spatial-fabric/source/05_spatial_candidates/novegeo_coordinate_candidates_v002.csv",
                    EFFECT_SCOPE,
                ),
            )
            cur.execute(
                "INSERT INTO geography.nngla_geometry_version"
                "(geometry_id,subject_id,runtime_mode,geometry_role_code,crs_code,geometry_type_code,geometry,valid_from,valid_to,"
                "supersedes_geometry_id,source_sha256) "
                "VALUES(%s,%s,%s,'SPATIAL_REFERENCE_POINT','NG-CRS-EPSG4326','POINT',"
                "ST_SetSRID(ST_MakePoint(%s::double precision,%s::double precision),4326),%s,NULL,NULL,%s) "
                "ON CONFLICT(geometry_id) DO NOTHING",
                (
                    geometry.geometry_id, canonical_id, RUNTIME_MODE, geometry.longitude, geometry.latitude,
                    geometry.valid_from, geometry.source_sha256,
                ),
            )
            cur.execute(
                "INSERT INTO geography.nngla_canonical_crosswalk"
                "(crosswalk_id,dataset_id,dataset_version,source_record_id,candidate_id,canonical_id,canonical_version,runtime_mode,effect_scope) "
                "VALUES(%s,%s,%s,%s,%s,%s,1,%s,%s) "
                "ON CONFLICT(dataset_id,dataset_version,source_record_id,runtime_mode,effect_scope) DO NOTHING",
                (
                    crosswalk.spatial_crosswalk_id, SPATIAL_DATASET_ID, SPATIAL_DATASET_VERSION,
                    crosswalk.coordinate_candidate_id, crosswalk.coordinate_candidate_id,
                    canonical_id, RUNTIME_MODE, EFFECT_SCOPE,
                ),
            )
        return "INSERTED"

    def persist_execution_receipt(self, receipt: SpatialExecutionReceipt) -> None:
        with self.connection.cursor() as cur:
            cur.execute(
                "INSERT INTO geography.nngla_execution_receipt"
                "(execution_id,plan_id,plan_version,fingerprint_sha256,database_name,environment_name,runtime_mode,repository_revision,"
                "source_sha256,submitter_actor_id,approver_actor_id,selected_count,inserted_count,reused_count,quarantined_count,failed_count,"
                "status,started_at,completed_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                "ON CONFLICT(execution_id) DO NOTHING",
                (
                    receipt.execution_id, receipt.plan_id, receipt.plan_version, receipt.fingerprint, receipt.database_name,
                    receipt.environment_name, receipt.runtime_mode, receipt.repository_revision, receipt.source_sha256,
                    receipt.submitter_actor_id, receipt.approver_actor_id, receipt.selected_count, receipt.inserted_count,
                    receipt.reused_count, receipt.quarantined_count, receipt.failed_count, receipt.status,
                    receipt.started_at, receipt.completed_at,
                ),
            )
            for item in receipt.items:
                cur.execute(
                    "INSERT INTO geography.nngla_execution_item"
                    "(execution_id,source_record_id,canonical_id,outcome,crosswalk_id,canonicalization_receipt_id,event_id,audit_id,publication_ready,detail) "
                    "VALUES(%s,%s,%s,%s,NULL,NULL,NULL,NULL,false,%s::jsonb) ON CONFLICT(execution_id,source_record_id) DO NOTHING",
                    (
                        receipt.execution_id, item.coordinate_candidate_id, item.canonical_spatial_point_id, item.outcome,
                        json.dumps({"geometry_id": item.geometry_id, "detail": item.detail}),
                    ),
                )


__all__ = ["MemorySpatialRepository", "PostgreSQLSpatialRepository"]
