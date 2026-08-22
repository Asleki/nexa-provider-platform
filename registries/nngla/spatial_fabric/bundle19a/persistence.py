"""Fail-closed transactional persistence for governed place spatial association."""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import json

from registries.nngla.spatial_fabric.bundle17k.geometry_allocator import MemoryGeometryIdAllocator

from ._shared import (
    BUNDLE_EFFECTIVE_DATE,
    CRS_CODE,
    EFFECT_SCOPE,
    PLACE_DATASET_ID,
    PLACE_DATASET_VERSION,
    RUNTIME_MODE,
    SOURCE_REPOSITORY_REVISION,
    SOVEREIGN_BOUNDARY_ID,
    SOVEREIGN_BOUNDARY_VERSION,
    payload_sha256,
    stable_id,
)
from .contracts import GeometryRole, PlaceSpatialExecutionReceipt
from .footprints import derive_point_only_exceptions, derive_settlement_footprints
from .postgresql_contract import REQUIRED_RELATIONS
from .siting import derive_place_reference_points
from .source import load_settlement_requirements


def point_geojson(point) -> dict[str, object]:
    return {"type": "Point", "coordinates": [point.longitude, point.latitude]}


def footprint_geojson(footprint) -> dict[str, object]:
    return {"type": "Polygon", "coordinates": [[[lon, lat] for lon, lat in footprint.ring]]}


def geometry_payload_sha256(payload: dict[str, object]) -> str:
    return payload_sha256(payload)


class MemoryPlaceSpatialRepository:
    """Transaction-capable memory adapter proving lifecycle/idempotency without a live database."""

    def __init__(self, *, database_name: str = "memory_novegeo", environment_name: str = "test") -> None:
        self.database_name = database_name
        self.environment_name = environment_name
        self.places = {
            row.place_id: {
                "source_place_code": row.source_place_code,
                "spatial_assignment_status": "UNMAPPED_PENDING_ASSOCIATION",
                "geometry_reference": None,
            }
            for row in load_settlement_requirements()
        }
        self.allocator = MemoryGeometryIdAllocator()
        self.geometries: dict[str, dict[str, object]] = {}
        self.receipts: dict[str, PlaceSpatialExecutionReceipt] = {}
        self.execution_items: dict[str, tuple[dict[str, object], ...]] = {}

    @contextmanager
    def transaction(self):
        allocator_state = (set(self.allocator._occupied), int(self.allocator._next), dict(self.allocator._by_key))
        backup = (deepcopy(self.places), deepcopy(self.geometries), dict(self.receipts), deepcopy(self.execution_items), allocator_state)
        try:
            yield self
        except Exception:
            self.places, self.geometries, self.receipts, self.execution_items, allocator_state = backup
            occupied, next_value, by_key = allocator_state
            self.allocator._occupied = set(occupied)
            self.allocator._next = int(next_value)
            self.allocator._by_key = dict(by_key)
            raise

    def replay(self, fingerprint_sha256: str):
        receipt = self.receipts.get(fingerprint_sha256)
        if receipt is None:
            return None
        return PlaceSpatialExecutionReceipt(
            execution_id=receipt.execution_id,
            fingerprint_sha256=receipt.fingerprint_sha256,
            database_name=receipt.database_name,
            environment_name=receipt.environment_name,
            repository_revision=receipt.repository_revision,
            submitter_actor_id=receipt.submitter_actor_id,
            approver_actor_id=receipt.approver_actor_id,
            selected_place_count=receipt.selected_place_count,
            associated_place_count=receipt.associated_place_count,
            geometry_insert_count=receipt.geometry_insert_count,
            footprint_insert_count=receipt.footprint_insert_count,
            point_only_count=receipt.point_only_count,
            status="REUSED",
            replayed=True,
        )

    def preflight(self) -> None:
        if len(self.places) != 700:
            raise RuntimeError("memory target does not contain exactly 700 canonical places")
        for row in self.places.values():
            if row["spatial_assignment_status"] != "UNMAPPED_PENDING_ASSOCIATION" or row["geometry_reference"] is not None:
                raise RuntimeError("memory target is not the expected unmapped Bundle 19A baseline")

    def qualify_geometry(self, subject_id: str, role: GeometryRole, payload: dict[str, object]) -> None:
        if not subject_id.startswith("NG-PLC-"):
            raise ValueError("place geometry subject must be canonical NG-PLC identity")
        if role not in {GeometryRole.PLACE_REFERENCE_POINT, GeometryRole.SETTLEMENT_FOOTPRINT}:
            raise ValueError("unsupported place geometry role")
        if payload.get("type") not in {"Point", "Polygon"}:
            raise ValueError("unsupported geometry payload")

    def reserve_geometry(self, subject_id: str, role: GeometryRole, idempotency_key: str) -> str:
        return self.allocator.reserve(idempotency_key=idempotency_key, authority_runtime_mode="production")

    def persist_geometry(self, *, geometry_id: str, subject_id: str, role: GeometryRole, payload: dict[str, object], source_candidate_id: str) -> None:
        if geometry_id in self.geometries:
            raise ValueError("geometry identifier collision")
        self.geometries[geometry_id] = {
            "subject_id": subject_id,
            "geometry_role_code": role.value,
            "payload": payload,
            "source_candidate_id": source_candidate_id,
            "checksum_sha256": geometry_payload_sha256(payload),
        }

    def associate_place_reference(self, *, place_id: str, source_place_code: str, geometry_id: str) -> None:
        row = self.places.get(place_id)
        if row is None or row["source_place_code"] != source_place_code:
            raise ValueError("canonical place/source crosswalk mismatch")
        if row["spatial_assignment_status"] != "UNMAPPED_PENDING_ASSOCIATION" or row["geometry_reference"] is not None:
            raise ValueError("place is not eligible for initial spatial association")
        geom = self.geometries.get(geometry_id)
        if geom is None or geom["subject_id"] != place_id or geom["geometry_role_code"] != GeometryRole.PLACE_REFERENCE_POINT.value:
            raise ValueError("place reference must point at existing PLACE_REFERENCE_POINT geometry")
        row["spatial_assignment_status"] = "AUTHORITATIVE_GEOMETRY_ASSIGNED"
        row["geometry_reference"] = geometry_id

    def associate_existing_geometry(self, *, place_id: str, geometry_id: str) -> dict[str, str]:
        row = self.places.get(place_id)
        if row is None:
            raise ValueError("canonical place does not exist")
        geom = self.geometries.get(geometry_id)
        if geom is None or geom["subject_id"] != place_id or geom["geometry_role_code"] != GeometryRole.PLACE_REFERENCE_POINT.value:
            raise ValueError("ASSOCIATE_GEOMETRY requires an existing PLACE_REFERENCE_POINT geometry for the same place")
        self.associate_place_reference(
            place_id=place_id, source_place_code=str(row["source_place_code"]), geometry_id=geometry_id
        )
        return {"place_id": place_id, "geometry_id": geometry_id}

    def persist_execution_receipt(self, receipt: PlaceSpatialExecutionReceipt, *, item_details: tuple[dict[str, object], ...]) -> None:
        self.receipts[receipt.fingerprint_sha256] = receipt
        self.execution_items[receipt.execution_id] = deepcopy(item_details)


class PostgreSQLPlaceSpatialRepository:
    """Uses existing locked NNGLA/PostGIS tables; Bundle 19A adds no schema migration."""

    def __init__(self, connection, *, environment_name: str) -> None:
        if not environment_name.strip():
            raise ValueError("environment_name is required")
        self.connection = connection
        self.environment_name = environment_name.strip()

    @property
    def database_name(self) -> str:
        with self.connection.cursor() as cur:
            cur.execute("SELECT current_database()")
            return str(cur.fetchone()[0])

    @contextmanager
    def transaction(self):
        try:
            yield self
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def replay(self, fingerprint_sha256: str):
        with self.connection.cursor() as cur:
            cur.execute(
                "SELECT execution_id,database_name,environment_name,repository_revision,submitter_actor_id,approver_actor_id,"
                "selected_count,inserted_count,status FROM geography.nngla_execution_receipt "
                "WHERE fingerprint_sha256=%s AND database_name=current_database() AND environment_name=%s",
                (fingerprint_sha256, self.environment_name),
            )
            row = cur.fetchone()
            if row is None:
                return None
            execution_id = str(row[0])
            cur.execute(
                "SELECT COUNT(*), COUNT(*) FILTER (WHERE COALESCE((detail->>'footprint_geometry_id'),'') <> ''), "
                "COUNT(*) FILTER (WHERE COALESCE((detail->>'point_only_reason'),'') <> '') "
                "FROM geography.nngla_execution_item WHERE execution_id=%s",
                (execution_id,),
            )
            item_count, footprint_count, point_only_count = (int(value or 0) for value in cur.fetchone())
        return PlaceSpatialExecutionReceipt(
            execution_id=execution_id,
            fingerprint_sha256=fingerprint_sha256,
            database_name=str(row[1]),
            environment_name=str(row[2]),
            repository_revision=str(row[3]),
            submitter_actor_id=str(row[4]),
            approver_actor_id=str(row[5]),
            selected_place_count=int(row[6]),
            associated_place_count=int(row[7]),
            geometry_insert_count=item_count + footprint_count,
            footprint_insert_count=footprint_count,
            point_only_count=point_only_count,
            status="REUSED",
            replayed=True,
        )

    def preflight(self) -> None:
        with self.connection.cursor() as cur:
            for relation in REQUIRED_RELATIONS:
                cur.execute("SELECT to_regclass(%s) IS NOT NULL", (relation,))
                if not bool(cur.fetchone()[0]):
                    raise RuntimeError(f"required Bundle 19A relation is unavailable: {relation}")
            cur.execute("SELECT to_regprocedure('geography.nngla_reserve_geometry_id(text,text,text,text)') IS NOT NULL")
            if not bool(cur.fetchone()[0]):
                raise RuntimeError("governed NG-GEO allocator function is unavailable")
            cur.execute(
                "SELECT lifecycle_status, ST_IsValid(geometry), ST_SRID(geometry) "
                "FROM geography.world_boundary_version WHERE boundary_id=%s AND boundary_version=%s "
                "ORDER BY CASE WHEN lifecycle_status='active' THEN 0 ELSE 1 END LIMIT 1",
                (SOVEREIGN_BOUNDARY_ID, SOVEREIGN_BOUNDARY_VERSION),
            )
            boundary = cur.fetchone()
            if boundary is None or str(boundary[0]) != "active" or not bool(boundary[1]) or int(boundary[2]) != 4326:
                raise RuntimeError("active valid sovereign boundary v002 is required before place spatialization")
            cur.execute(
                "SELECT place_id,source_place_code,spatial_assignment_status,geometry_reference "
                "FROM geography.nngla_place_reference ORDER BY place_id"
            )
            actual = cur.fetchall()
            expected = load_settlement_requirements()
            if len(actual) != 700:
                raise RuntimeError(f"live target must contain exactly 700 canonical places; found {len(actual)}")
            for row, source in zip(actual, expected):
                if str(row[0]) != source.place_id or str(row[1]) != source.source_place_code:
                    raise RuntimeError(f"live canonical place identity mismatch at {source.source_place_code}")
                if str(row[2]) != "UNMAPPED_PENDING_ASSOCIATION" or row[3] is not None:
                    raise RuntimeError(f"place is not eligible for initial Bundle 19A association: {source.place_id}")
            cur.execute(
                "SELECT COUNT(*) FROM geography.nngla_geometry_version "
                "WHERE subject_id LIKE 'NG-PLC-%' AND geometry_role_code IN ('PLACE_REFERENCE_POINT','SETTLEMENT_FOOTPRINT') AND valid_to IS NULL"
            )
            if int(cur.fetchone()[0]) != 0:
                raise RuntimeError("unexpected pre-existing active place geometry prevents safe initial Bundle 19A execution")

    def qualify_geometry(self, subject_id: str, role: GeometryRole, payload: dict[str, object]) -> None:
        geojson = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        with self.connection.cursor() as cur:
            cur.execute(
                "WITH candidate AS (SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s),4326) AS geom), "
                "boundary AS (SELECT geometry FROM geography.world_boundary_version "
                "WHERE boundary_id=%s AND boundary_version=%s AND lifecycle_status='active' LIMIT 1) "
                "SELECT ST_IsValid(candidate.geom), NOT ST_IsEmpty(candidate.geom), ST_SRID(candidate.geom)=4326, "
                "ST_CoveredBy(candidate.geom,boundary.geometry) FROM candidate CROSS JOIN boundary",
                (geojson, SOVEREIGN_BOUNDARY_ID, SOVEREIGN_BOUNDARY_VERSION),
            )
            row = cur.fetchone()
            if row is None or not all(bool(value) for value in row):
                raise ValueError(f"PostGIS sovereign qualification failed before geometry allocation: {subject_id}:{role.value}")

    def reserve_geometry(self, subject_id: str, role: GeometryRole, idempotency_key: str) -> str:
        reservation_id = stable_id("georeserve:place:nngla:", subject_id, role.value, idempotency_key)
        with self.connection.cursor() as cur:
            cur.execute(
                "SELECT geography.nngla_reserve_geometry_id(%s,%s,%s,%s)",
                (reservation_id, idempotency_key, subject_id, role.value),
            )
            value = cur.fetchone()
            if value is None or not str(value[0]).startswith("NG-GEO-"):
                raise RuntimeError("governed geometry allocator did not return NG-GEO identity")
            return str(value[0])

    def persist_geometry(self, *, geometry_id: str, subject_id: str, role: GeometryRole, payload: dict[str, object], source_candidate_id: str) -> None:
        geometry_type = str(payload["type"]).upper()
        checksum = geometry_payload_sha256(payload)
        source_path = (
            "data/novegeo/nngla/spatial-fabric/bundle19a/qualified/novegeo_place_reference_points_v001.csv"
            if role is GeometryRole.PLACE_REFERENCE_POINT
            else "data/novegeo/nngla/spatial-fabric/bundle19a/qualified/novegeo_settlement_footprints_v001.geojson"
        )
        if geometry_type == "POINT":
            vertex_count = 1
            authoritative_level = "QUALIFIED_PLACE_REFERENCE"
        elif geometry_type == "POLYGON":
            vertex_count = len(payload["coordinates"][0])
            authoritative_level = "QUALIFIED_SETTLEMENT_FOOTPRINT"
        else:
            raise ValueError("Bundle 19A supports POINT and POLYGON only")
        geojson = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        with self.connection.cursor() as cur:
            cur.execute(
                "INSERT INTO geography.nngla_geometry_authority_record"
                "(geometry_id,subject_type,subject_id,geometry_role_code,source_geometry_id,source_dataset_id,source_version,"
                "geometry_type_code,crs_code,authoritative_level,vertex_count,part_count,valid_from,valid_to,supersedes_geometry_id,"
                "superseded_by_geometry_id,qualification_status,publication_status,checksum_sha256,source_path_reference,runtime_effect_scope) "
                "VALUES(%s,'PLACE',%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s,NULL,NULL,NULL,'QUALIFIED','NOT_PUBLISHED',%s,%s,%s)",
                (
                    geometry_id, subject_id, role.value, source_candidate_id, PLACE_DATASET_ID, PLACE_DATASET_VERSION,
                    geometry_type, CRS_CODE, authoritative_level, vertex_count, BUNDLE_EFFECTIVE_DATE,
                    checksum, source_path, EFFECT_SCOPE,
                ),
            )
            cur.execute(
                "INSERT INTO geography.nngla_geometry_version"
                "(geometry_id,subject_id,runtime_mode,geometry_role_code,crs_code,geometry_type_code,geometry,valid_from,valid_to,supersedes_geometry_id,source_sha256) "
                "VALUES(%s,%s,%s,%s,%s,%s,ST_SetSRID(ST_GeomFromGeoJSON(%s),4326),%s,NULL,NULL,%s)",
                (geometry_id, subject_id, RUNTIME_MODE, role.value, CRS_CODE, geometry_type, geojson, BUNDLE_EFFECTIVE_DATE, checksum),
            )

    def associate_place_reference(self, *, place_id: str, source_place_code: str, geometry_id: str) -> None:
        with self.connection.cursor() as cur:
            cur.execute(
                "UPDATE geography.nngla_place_reference SET spatial_assignment_status='AUTHORITATIVE_GEOMETRY_ASSIGNED',geometry_reference=%s "
                "WHERE place_id=%s AND source_place_code=%s AND spatial_assignment_status='UNMAPPED_PENDING_ASSOCIATION' "
                "AND geometry_reference IS NULL RETURNING place_id",
                (geometry_id, place_id, source_place_code),
            )
            row = cur.fetchone()
            if row is None or str(row[0]) != place_id:
                raise RuntimeError(f"fail-closed place association update rejected for {place_id}")

    def associate_existing_geometry(self, *, place_id: str, geometry_id: str) -> dict[str, str]:
        with self.transaction():
            with self.connection.cursor() as cur:
                cur.execute(
                    "SELECT p.source_place_code,g.geometry_role_code,g.subject_id "
                    "FROM geography.nngla_place_reference p JOIN geography.nngla_geometry_version g ON g.geometry_id=%s "
                    "WHERE p.place_id=%s AND g.valid_to IS NULL",
                    (geometry_id, place_id),
                )
                row = cur.fetchone()
                if row is None or str(row[1]) != GeometryRole.PLACE_REFERENCE_POINT.value or str(row[2]) != place_id:
                    raise ValueError("ASSOCIATE_GEOMETRY requires an existing active PLACE_REFERENCE_POINT geometry for the same place")
                source_place_code = str(row[0])
            self.associate_place_reference(place_id=place_id, source_place_code=source_place_code, geometry_id=geometry_id)
        return {"place_id": place_id, "geometry_id": geometry_id}

    def persist_execution_receipt(self, receipt: PlaceSpatialExecutionReceipt, *, item_details: tuple[dict[str, object], ...]) -> None:
        now = datetime.now(timezone.utc)
        with self.connection.cursor() as cur:
            cur.execute(
                "INSERT INTO geography.nngla_execution_receipt"
                "(execution_id,plan_id,plan_version,fingerprint_sha256,database_name,environment_name,runtime_mode,repository_revision,source_sha256,"
                "submitter_actor_id,approver_actor_id,selected_count,inserted_count,reused_count,quarantined_count,failed_count,status,started_at,completed_at) "
                "VALUES(%s,'p006.7.11.10-place-spatial-association',1,%s,current_database(),%s,%s,%s,%s,%s,%s,%s,%s,0,0,0,'APPLIED',%s,%s)",
                (
                    receipt.execution_id, receipt.fingerprint_sha256, self.environment_name, RUNTIME_MODE, receipt.repository_revision,
                    receipt.fingerprint_sha256, receipt.submitter_actor_id, receipt.approver_actor_id,
                    receipt.selected_place_count, receipt.associated_place_count, now, now,
                ),
            )
            for item in item_details:
                cur.execute(
                    "INSERT INTO geography.nngla_execution_item"
                    "(execution_id,source_record_id,canonical_id,outcome,crosswalk_id,canonicalization_receipt_id,event_id,audit_id,publication_ready,detail) "
                    "VALUES(%s,%s,%s,'ASSOCIATED',NULL,NULL,NULL,NULL,false,%s::jsonb)",
                    (receipt.execution_id, item["source_place_code"], item["place_id"], json.dumps(item, sort_keys=True, separators=(",", ":"))),
                )


__all__ = [
    "point_geojson", "footprint_geojson", "geometry_payload_sha256",
    "MemoryPlaceSpatialRepository", "PostgreSQLPlaceSpatialRepository",
]
