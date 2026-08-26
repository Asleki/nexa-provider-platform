"""Memory and PostgreSQL adapters for selection-scoped spatial realization."""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import date, datetime, timezone
from hashlib import sha256
import json

from registries.nngla.spatial_fabric.bundle17k.geometry_allocator import MemoryGeometryIdAllocator
from registries.nngla.spatial_fabric.bundle19a.source import load_settlement_requirements
from registries.nngla.spatial_fabric.bundle19b.source import load_administrative_baseline

from .contracts import (
    AdminTargetState,
    CityClosure,
    GeometryCandidate,
    GeometryEncoding,
    GeometryRole,
    PlaceTargetState,
    SpatialRealizationExecutionReceipt,
    SpatialRealizationPreview,
    SubjectType,
    TargetGeometryState,
    TargetSnapshot,
)
from .preview import PLAN_ID, PLAN_VERSION

RUNTIME_MODE = "production"
EFFECT_SCOPE = "SHARED_REFERENCE"
CRS_CODE = "NG-CRS-EPSG4326"

def _normalize_effective_date(value: str | None) -> str:
    text = str(value or date.today().isoformat()).strip()
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as exc:
        raise ValueError("effective_date must be ISO YYYY-MM-DD") from exc


_REQUIRED_RELATIONS = (
    "geography.nngla_place_reference",
    "geography.nngla_administrative_area",
    "geography.nngla_geometry_authority_record",
    "geography.nngla_geometry_version",
    "geography.nngla_geometry_id_reservation",
    "geography.nngla_geometry_supersession_link",
    "geography.nngla_execution_receipt",
    "geography.nngla_execution_item",
    "geography.world_boundary_version",
)


def _stable_id(prefix: str, *parts: object) -> str:
    return prefix + sha256("\x1f".join(str(part) for part in parts).encode()).hexdigest()


class MemorySpatialRealizationRepository:
    """Mixed-state memory target used to prove batch/idempotency behavior."""

    def __init__(self, *, database_name: str = "memory_novegeo", environment_name: str = "test", effective_date: str | None = None) -> None:
        self.database_name = database_name
        self.environment_name = environment_name
        self.effective_date = _normalize_effective_date(effective_date)
        self.places = {
            row.place_id: {
                "source_place_code": row.source_place_code,
                "spatial_assignment_status": "UNMAPPED_PENDING_ASSOCIATION",
                "geometry_reference": None,
            }
            for row in load_settlement_requirements()
        }
        self.admins = {
            row["administrative_area_id"]: {
                "administrative_candidate_id": row["administrative_candidate_id"],
                "source_record_id": row["source_record_id"],
                "boundary_status": "BOUNDARY_PENDING_LEGALIZATION",
                "geometry_reference": None,
                "lifecycle_status": "PROVISIONAL",
                "candidate_status": "READY_NONSPATIAL",
            }
            for row in load_administrative_baseline()
        }
        self.allocator = MemoryGeometryIdAllocator()
        self.geometries: dict[str, dict[str, object]] = {}
        self.receipts: dict[str, SpatialRealizationExecutionReceipt] = {}
        self.execution_items: dict[str, tuple[dict[str, object], ...]] = {}

    @contextmanager
    def transaction(self):
        allocator_state = (set(self.allocator._occupied), int(self.allocator._next), dict(self.allocator._by_key))
        backup = (
            deepcopy(self.places), deepcopy(self.admins), deepcopy(self.geometries),
            dict(self.receipts), deepcopy(self.execution_items), allocator_state,
        )
        try:
            yield self
        except Exception:
            self.places, self.admins, self.geometries, self.receipts, self.execution_items, allocator_state = backup
            occupied, next_value, by_key = allocator_state
            self.allocator._occupied = set(occupied)
            self.allocator._next = int(next_value)
            self.allocator._by_key = dict(by_key)
            raise

    def snapshot(self, closures: tuple[CityClosure, ...]) -> TargetSnapshot:
        place_ids = {closure.root.place_id for closure in closures}
        admin_ids = set()
        subject_ids = set(place_ids)
        for closure in closures:
            admin_ids.update(item.subject_id for item in closure.desired_candidates if item.subject_type is SubjectType.ADMINISTRATIVE_AREA)
            admin_ids.add(closure.validation_parent.subject_id)
            admin_ids.update(item.subject_id for item in closure.overlays)
            admin_ids.update(item.subject_id for item in closure.regional_partition_peers)
            subject_ids.update(item.subject_id for item in closure.desired_candidates)
            subject_ids.update(admin_ids)
        places = {
            pid: PlaceTargetState(pid,row["source_place_code"],row["spatial_assignment_status"],row["geometry_reference"])
            for pid in sorted(place_ids) if (row := self.places.get(pid)) is not None
        }
        admins = {
            aid: AdminTargetState(
                aid,row["administrative_candidate_id"],row["source_record_id"],row["boundary_status"],
                row["geometry_reference"],row["lifecycle_status"],row["candidate_status"],
            )
            for aid in sorted(admin_ids) if (row := self.admins.get(aid)) is not None
        }
        active: dict[str, list[TargetGeometryState]] = {}
        for gid,row in self.geometries.items():
            if not row.get("active",True) or row["subject_id"] not in subject_ids:
                continue
            active.setdefault(str(row["subject_id"]),[]).append(TargetGeometryState(
                gid,str(row["subject_id"]),str(row["role"]),str(row["checksum"]),str(row.get("valid_from",self.effective_date)),
                "QUALIFIED","NOT_PUBLISHED",str(row.get("source_candidate_id","")),
            ))
        return TargetSnapshot(self.database_name,self.environment_name,places,admins,{k:tuple(v) for k,v in active.items()},{},True)

    def replay(self, fingerprint: str, root_ids: tuple[str, ...] | None = None):
        receipt=self.receipts.get(fingerprint)
        if receipt is None:return None
        if root_ids is not None:
            details=self.execution_items.get(receipt.execution_id,())
            actual=tuple(sorted({str(item.get("root_place_id","")) for item in details if item.get("root_place_id")}))
            if actual!=tuple(root_ids):return None
        return receipt

    def reserve_geometry(self, candidate: GeometryCandidate) -> str:
        return self.allocator.reserve(idempotency_key=candidate.reservation_key, authority_runtime_mode="production")

    def persist_geometry(self, candidate: GeometryCandidate, geometry_id: str, *, supersedes_geometry_id: str = "") -> None:
        if geometry_id in self.geometries:
            raise ValueError("geometry identity collision")
        self.geometries[geometry_id] = {
            "subject_id": candidate.subject_id,
            "role": candidate.geometry_role.value,
            "checksum": candidate.checksum_sha256,
            "source_candidate_id": candidate.source_candidate_id,
            "payload": candidate.payload,
            "encoding": candidate.encoding.value,
            "valid_from": self.effective_date,
            "supersedes": supersedes_geometry_id,
            "active": True,
        }

    def associate(self, candidate: GeometryCandidate, geometry_id: str) -> None:
        if candidate.geometry_role is GeometryRole.PLACE_REFERENCE_POINT:
            row=self.places[candidate.subject_id]
            if row["geometry_reference"] is not None or row["spatial_assignment_status"]!="UNMAPPED_PENDING_ASSOCIATION":
                raise RuntimeError("place is not eligible for initial realization")
            row["geometry_reference"]=geometry_id;row["spatial_assignment_status"]="AUTHORITATIVE_GEOMETRY_ASSIGNED"
        elif candidate.geometry_role is GeometryRole.ADMINISTRATIVE_BOUNDARY:
            row=self.admins[candidate.subject_id]
            if row["geometry_reference"] is not None or row["boundary_status"]!="BOUNDARY_PENDING_LEGALIZATION" or row["lifecycle_status"]!="PROVISIONAL":
                raise RuntimeError("administrative area is not eligible for initial realization")
            row["geometry_reference"]=geometry_id;row["boundary_status"]="LEGALIZED";row["lifecycle_status"]="ACTIVE";row["candidate_status"]="LEGALIZED"

    def supersede(self, candidate: GeometryCandidate, new_geometry_id: str, old_geometry_id: str) -> None:
        old=self.geometries.get(old_geometry_id)
        if old is None or old.get("subject_id")!=candidate.subject_id or old.get("role")!=candidate.geometry_role.value or not old.get("active",True):
            raise RuntimeError("supersession predecessor mismatch")
        old["active"]=False;old["superseded_by"]=new_geometry_id;old["valid_to"]=self.effective_date
        self.persist_geometry(candidate,new_geometry_id,supersedes_geometry_id=old_geometry_id)
        if candidate.geometry_role is GeometryRole.PLACE_REFERENCE_POINT:
            self.places[candidate.subject_id]["geometry_reference"]=new_geometry_id
            self.places[candidate.subject_id]["spatial_assignment_status"]="AUTHORITATIVE_GEOMETRY_ASSIGNED"
        elif candidate.geometry_role is GeometryRole.ADMINISTRATIVE_BOUNDARY:
            self.admins[candidate.subject_id]["geometry_reference"]=new_geometry_id
            self.admins[candidate.subject_id]["boundary_status"]="LEGALIZED";self.admins[candidate.subject_id]["lifecycle_status"]="ACTIVE";self.admins[candidate.subject_id]["candidate_status"]="LEGALIZED"

    def seed_candidate(self, candidate: GeometryCandidate, *, associate: bool = False) -> str:
        gid=self.reserve_geometry(candidate);self.persist_geometry(candidate,gid)
        if associate and candidate.geometry_role in {GeometryRole.PLACE_REFERENCE_POINT,GeometryRole.ADMINISTRATIVE_BOUNDARY}:self.associate(candidate,gid)
        return gid

    def persist_receipt(self, receipt: SpatialRealizationExecutionReceipt, item_details: tuple[dict[str,object],...], preview: SpatialRealizationPreview | None = None) -> None:
        self.receipts[receipt.fingerprint_sha256]=receipt;self.execution_items[receipt.execution_id]=deepcopy(item_details)

    def verify_applied(self, preview: SpatialRealizationPreview) -> None:
        snapshot=self.snapshot(preview.closures)
        for assessment in preview.assessments:
            for candidate in assessment.candidates:
                rows=[g for g in snapshot.active_geometries.get(candidate.subject_id,()) if g.geometry_role==candidate.geometry_role.value and g.checksum_sha256==candidate.checksum_sha256]
                if len(rows)!=1:raise RuntimeError(f"post-write geometry verification failed: {candidate.subject_id}:{candidate.geometry_role.value}")
                gid=rows[0].geometry_id
                if candidate.geometry_role is GeometryRole.PLACE_REFERENCE_POINT:
                    p=snapshot.places[candidate.subject_id]
                    if p.geometry_reference!=gid or p.spatial_assignment_status!="AUTHORITATIVE_GEOMETRY_ASSIGNED":raise RuntimeError("post-write place association verification failed")
                if candidate.geometry_role is GeometryRole.ADMINISTRATIVE_BOUNDARY:
                    a=snapshot.admins[candidate.subject_id]
                    if a.geometry_reference!=gid or a.boundary_status!="LEGALIZED" or a.lifecycle_status!="ACTIVE":raise RuntimeError("post-write administrative verification failed")


class PostgreSQLSpatialRealizationRepository:
    """Uses existing NNGLA geometry/execution tables; .15.5 adds no migration."""

    def __init__(self, connection, *, environment_name: str, effective_date: str | None = None) -> None:
        if not str(environment_name).strip():raise ValueError("environment_name is required")
        self.connection=connection;self.environment_name=str(environment_name).strip();self.effective_date=_normalize_effective_date(effective_date)

    @property
    def database_name(self)->str:
        with self.connection.cursor() as cur:cur.execute("SELECT current_database()");return str(cur.fetchone()[0])

    @contextmanager
    def transaction(self):
        # Preview reads may have opened an implicit transaction.  They are read-only
        # by contract, so close that transaction before starting the single atomic
        # execution transaction.
        self.connection.commit()
        tx = getattr(self.connection, "transaction", None)
        if callable(tx):
            with tx():
                yield self
            return
        try:
            yield self
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def _assert_capabilities(self)->None:
        with self.connection.cursor() as cur:
            for relation in _REQUIRED_RELATIONS:
                cur.execute("SELECT to_regclass(%s) IS NOT NULL",(relation,))
                if not bool(cur.fetchone()[0]):raise RuntimeError("required .15.5 relation unavailable: "+relation)
            cur.execute("SELECT to_regprocedure('geography.nngla_reserve_geometry_id(text,text,text,text)') IS NOT NULL")
            if not bool(cur.fetchone()[0]):raise RuntimeError("governed NG-GEO allocator function is unavailable")

    def snapshot(self, closures: tuple[CityClosure,...])->TargetSnapshot:
        self._assert_capabilities()
        place_ids=sorted({c.root.place_id for c in closures})
        admin_ids=set();subject_ids=set(place_ids)
        for closure in closures:
            for item in closure.desired_candidates:
                subject_ids.add(item.subject_id)
                if item.subject_type is SubjectType.ADMINISTRATIVE_AREA:admin_ids.add(item.subject_id)
            admin_ids.add(closure.validation_parent.subject_id)
            admin_ids.update(item.subject_id for item in closure.overlays)
            admin_ids.update(item.subject_id for item in closure.regional_partition_peers)
        subject_ids.update(admin_ids);admin_ids=sorted(admin_ids);subject_ids=sorted(subject_ids)
        places={};admins={};active={};reservations={}
        with self.connection.cursor() as cur:
            cur.execute("SELECT place_id,source_place_code,spatial_assignment_status,geometry_reference FROM geography.nngla_place_reference WHERE place_id=ANY(%s) ORDER BY place_id",(place_ids,))
            for row in cur.fetchall():places[str(row[0])]=PlaceTargetState(str(row[0]),str(row[1]),str(row[2]),None if row[3] is None else str(row[3]))
            cur.execute("SELECT administrative_area_id,administrative_candidate_id,source_record_id,boundary_status,geometry_reference,lifecycle_status_code,candidate_status FROM geography.nngla_administrative_area WHERE administrative_area_id=ANY(%s) ORDER BY administrative_area_id",(admin_ids,))
            for row in cur.fetchall():admins[str(row[0])]=AdminTargetState(str(row[0]),str(row[1]),str(row[2]),str(row[3]),None if row[4] is None else str(row[4]),str(row[5]),str(row[6]))
            cur.execute("SELECT g.geometry_id,g.subject_id,g.geometry_role_code,a.checksum_sha256,g.valid_from,a.qualification_status,a.publication_status,a.source_geometry_id FROM geography.nngla_geometry_version g JOIN geography.nngla_geometry_authority_record a ON a.geometry_id=g.geometry_id WHERE g.subject_id=ANY(%s) AND g.valid_to IS NULL ORDER BY g.subject_id,g.geometry_role_code,g.geometry_id",(subject_ids,))
            for row in cur.fetchall():active.setdefault(str(row[1]),[]).append(TargetGeometryState(str(row[0]),str(row[1]),str(row[2]),str(row[3]),str(row[4]),str(row[5]),str(row[6]),str(row[7])))
            cur.execute("SELECT idempotency_key,geometry_id,subject_id FROM geography.nngla_geometry_id_reservation WHERE subject_id=ANY(%s) ORDER BY idempotency_key",(subject_ids,))
            for row in cur.fetchall():reservations[str(row[0])]=(str(row[1]),str(row[2]))
        return TargetSnapshot(self.database_name,self.environment_name,places,admins,{k:tuple(v) for k,v in active.items()},reservations,True)

    def replay(self,fingerprint:str,root_ids:tuple[str,...] | None=None):
        with self.connection.cursor() as cur:
            cur.execute("SELECT execution_id,database_name,environment_name,repository_revision,submitter_actor_id,approver_actor_id,selected_count,inserted_count,reused_count,status FROM geography.nngla_execution_receipt WHERE fingerprint_sha256=%s AND database_name=current_database() AND environment_name=%s",(fingerprint,self.environment_name));row=cur.fetchone()
            if row is None:return None
            execution_id=str(row[0])
            if root_ids is not None:
                cur.execute("SELECT DISTINCT detail->>'root_place_id' FROM geography.nngla_execution_item WHERE execution_id=%s AND COALESCE(detail->>'root_place_id','')<>'' ORDER BY 1",(execution_id,))
                actual=tuple(str(item[0]) for item in cur.fetchall())
                if actual!=tuple(root_ids):return None
            cur.execute("SELECT COUNT(*) FILTER (WHERE COALESCE((detail->>'association_applied')::boolean,false)) FROM geography.nngla_execution_item WHERE execution_id=%s",(execution_id,));association_count=int(cur.fetchone()[0] or 0)
        return SpatialRealizationExecutionReceipt(execution_id,fingerprint,str(row[1]),str(row[2]),str(row[3]),str(row[4]),str(row[5]),int(row[6]),int(row[7]),association_count,int(row[8]),"REUSED",True)

    def reserve_geometry(self,candidate:GeometryCandidate)->str:
        reservation_id=_stable_id("georeserve:realization:nngla:",candidate.subject_id,candidate.geometry_role.value,candidate.reservation_key)
        with self.connection.cursor() as cur:
            cur.execute("SELECT geography.nngla_reserve_geometry_id(%s,%s,%s,%s)",(reservation_id,candidate.reservation_key,candidate.subject_id,candidate.geometry_role.value));row=cur.fetchone()
        if row is None or not str(row[0]).startswith("NG-GEO-"):raise RuntimeError("governed allocator did not return NG-GEO identity")
        return str(row[0])

    @staticmethod
    def _geometry_expression(candidate:GeometryCandidate):
        if candidate.encoding is GeometryEncoding.GEOJSON:return "ST_SetSRID(ST_GeomFromGeoJSON(%s),4326)",(candidate.payload,)
        return "ST_GeomFromEWKB(decode(%s,'hex'))",(candidate.payload,)

    def persist_geometry(self,candidate:GeometryCandidate,geometry_id:str,*,supersedes_geometry_id:str="")->None:
        expr,params=self._geometry_expression(candidate)
        authoritative_level={
            GeometryRole.PLACE_REFERENCE_POINT:"QUALIFIED_PLACE_REFERENCE",
            GeometryRole.SETTLEMENT_FOOTPRINT:"QUALIFIED_SETTLEMENT_FOOTPRINT",
            GeometryRole.ADMINISTRATIVE_BOUNDARY:"QUALIFIED_LEGAL_ADMINISTRATIVE_BOUNDARY",
        }[candidate.geometry_role]
        with self.connection.cursor() as cur:
            sql=f"""WITH x AS (SELECT {expr} geometry)
            INSERT INTO geography.nngla_geometry_authority_record
            (geometry_id,subject_type,subject_id,geometry_role_code,source_geometry_id,source_dataset_id,source_version,geometry_type_code,crs_code,authoritative_level,vertex_count,part_count,valid_from,valid_to,supersedes_geometry_id,superseded_by_geometry_id,qualification_status,publication_status,checksum_sha256,source_path_reference,runtime_effect_scope)
            SELECT %s,%s,%s,%s,%s,%s,%s,upper(replace(ST_GeometryType(geometry),'ST_','')),%s,%s,ST_NPoints(geometry),CASE WHEN ST_GeometryType(geometry)='ST_MultiPolygon' THEN ST_NumGeometries(geometry) ELSE 1 END,%s,NULL,NULLIF(%s,''),NULL,'QUALIFIED','NOT_PUBLISHED',%s,%s,%s FROM x"""
            values=params+(geometry_id,candidate.subject_type.value,candidate.subject_id,candidate.geometry_role.value,candidate.source_candidate_id,candidate.source_dataset_id,candidate.source_dataset_version,CRS_CODE,authoritative_level,self.effective_date,supersedes_geometry_id,candidate.checksum_sha256,candidate.source_path_reference,EFFECT_SCOPE)
            cur.execute(sql,values)
            sql=f"""WITH x AS (SELECT {expr} geometry)
            INSERT INTO geography.nngla_geometry_version(geometry_id,subject_id,runtime_mode,geometry_role_code,crs_code,geometry_type_code,geometry,valid_from,valid_to,supersedes_geometry_id,source_sha256)
            SELECT %s,%s,%s,%s,%s,upper(replace(ST_GeometryType(geometry),'ST_','')),geometry,%s,NULL,NULLIF(%s,''),%s FROM x"""
            cur.execute(sql,params+(geometry_id,candidate.subject_id,RUNTIME_MODE,candidate.geometry_role.value,CRS_CODE,self.effective_date,supersedes_geometry_id,candidate.checksum_sha256))

    def associate(self,candidate:GeometryCandidate,geometry_id:str)->None:
        with self.connection.cursor() as cur:
            if candidate.geometry_role is GeometryRole.PLACE_REFERENCE_POINT:
                cur.execute("UPDATE geography.nngla_place_reference SET spatial_assignment_status='AUTHORITATIVE_GEOMETRY_ASSIGNED',geometry_reference=%s WHERE place_id=%s AND spatial_assignment_status='UNMAPPED_PENDING_ASSOCIATION' AND geometry_reference IS NULL RETURNING place_id",(geometry_id,candidate.subject_id));row=cur.fetchone()
                if row is None:raise RuntimeError("fail-closed place realization association rejected: "+candidate.subject_id)
            elif candidate.geometry_role is GeometryRole.ADMINISTRATIVE_BOUNDARY:
                cur.execute("UPDATE geography.nngla_administrative_area SET boundary_status='LEGALIZED',geometry_reference=%s,lifecycle_status_code='ACTIVE',candidate_status='LEGALIZED' WHERE administrative_area_id=%s AND boundary_status='BOUNDARY_PENDING_LEGALIZATION' AND geometry_reference IS NULL AND lifecycle_status_code='PROVISIONAL' RETURNING administrative_area_id",(geometry_id,candidate.subject_id));row=cur.fetchone()
                if row is None:raise RuntimeError("fail-closed administrative realization rejected: "+candidate.subject_id)

    def supersede(self,candidate:GeometryCandidate,new_geometry_id:str,old_geometry_id:str)->None:
        self.persist_geometry(candidate,new_geometry_id,supersedes_geometry_id=old_geometry_id)
        link_id=_stable_id("geosupersede:realization:nngla:",candidate.subject_id,candidate.geometry_role.value,old_geometry_id,new_geometry_id)
        with self.connection.cursor() as cur:
            cur.execute("UPDATE geography.nngla_geometry_version SET valid_to=%s WHERE geometry_id=%s AND valid_to IS NULL RETURNING geometry_id",(self.effective_date,old_geometry_id))
            if cur.fetchone() is None:raise RuntimeError("active predecessor geometry not found for supersession")
            cur.execute("UPDATE geography.nngla_geometry_authority_record SET valid_to=%s,superseded_by_geometry_id=%s WHERE geometry_id=%s AND valid_to IS NULL RETURNING geometry_id",(self.effective_date,new_geometry_id,old_geometry_id))
            if cur.fetchone() is None:raise RuntimeError("authority predecessor geometry not found for supersession")
            cur.execute("INSERT INTO geography.nngla_geometry_supersession_link(link_id,subject_id,geometry_role_code,predecessor_geometry_id,successor_geometry_id,effective_on,change_reason_code,survey_id,authority_runtime_mode,source_reference) VALUES(%s,%s,%s,%s,%s,%s,'P006_7_11_15_5_TOPOLOGY_RECONCILIATION',NULL,'production',%s)",(link_id,candidate.subject_id,candidate.geometry_role.value,old_geometry_id,new_geometry_id,self.effective_date,candidate.source_candidate_id))
            if candidate.geometry_role is GeometryRole.PLACE_REFERENCE_POINT:
                cur.execute("UPDATE geography.nngla_place_reference SET geometry_reference=%s,spatial_assignment_status='AUTHORITATIVE_GEOMETRY_ASSIGNED' WHERE place_id=%s AND geometry_reference=%s RETURNING place_id",(new_geometry_id,candidate.subject_id,old_geometry_id))
            elif candidate.geometry_role is GeometryRole.ADMINISTRATIVE_BOUNDARY:
                cur.execute("UPDATE geography.nngla_administrative_area SET geometry_reference=%s,boundary_status='LEGALIZED',lifecycle_status_code='ACTIVE',candidate_status='LEGALIZED' WHERE administrative_area_id=%s AND geometry_reference=%s RETURNING administrative_area_id",(new_geometry_id,candidate.subject_id,old_geometry_id))
            else:return
            if cur.fetchone() is None:raise RuntimeError("canonical association did not follow geometry supersession")

    def persist_receipt(self,receipt:SpatialRealizationExecutionReceipt,item_details:tuple[dict[str,object],...],preview:SpatialRealizationPreview)->None:
        now=datetime.now(timezone.utc)
        with self.connection.cursor() as cur:
            cur.execute("INSERT INTO geography.nngla_execution_receipt(execution_id,plan_id,plan_version,fingerprint_sha256,database_name,environment_name,runtime_mode,repository_revision,source_sha256,submitter_actor_id,approver_actor_id,selected_count,inserted_count,reused_count,quarantined_count,failed_count,status,started_at,completed_at) VALUES(%s,%s,%s,%s,current_database(),%s,%s,%s,%s,%s,%s,%s,%s,%s,0,0,'APPLIED',%s,%s)",(receipt.execution_id,PLAN_ID,PLAN_VERSION,receipt.fingerprint_sha256,self.environment_name,RUNTIME_MODE,receipt.repository_revision,preview.source_sha256,receipt.submitter_actor_id,receipt.approver_actor_id,receipt.selected_root_count,receipt.geometry_insert_count,receipt.reused_count,now,now))
            for item in item_details:
                cur.execute("INSERT INTO geography.nngla_execution_item(execution_id,source_record_id,canonical_id,outcome,publication_ready,detail) VALUES(%s,%s,%s,%s,false,%s::jsonb)",(receipt.execution_id,str(item['action_id']),str(item['subject_id']),str(item['outcome']),json.dumps(item,sort_keys=True,separators=(",",":"))))

    def verify_applied(self,preview:SpatialRealizationPreview)->None:
        snapshot=self.snapshot(preview.closures)
        for assessment in preview.assessments:
            for candidate in assessment.candidates:
                rows=[g for g in snapshot.active_geometries.get(candidate.subject_id,()) if g.geometry_role==candidate.geometry_role.value and g.checksum_sha256==candidate.checksum_sha256]
                if len(rows)!=1:raise RuntimeError(f"post-write geometry verification failed: {candidate.subject_id}:{candidate.geometry_role.value}")
                gid=rows[0].geometry_id
                if candidate.geometry_role is GeometryRole.PLACE_REFERENCE_POINT:
                    p=snapshot.places.get(candidate.subject_id)
                    if p is None or p.geometry_reference!=gid or p.spatial_assignment_status!="AUTHORITATIVE_GEOMETRY_ASSIGNED":raise RuntimeError("post-write place association verification failed")
                if candidate.geometry_role is GeometryRole.ADMINISTRATIVE_BOUNDARY:
                    a=snapshot.admins.get(candidate.subject_id)
                    if a is None or a.geometry_reference!=gid or a.boundary_status!="LEGALIZED" or a.lifecycle_status!="ACTIVE":raise RuntimeError("post-write administrative verification failed")


__all__=["MemorySpatialRealizationRepository","PostgreSQLSpatialRealizationRepository"]
