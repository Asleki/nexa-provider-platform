"""P006.7.11.5 governed persistence adapters for NNGLA migration execution."""
from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from .geometry_payloads import load_geometry
from .source_catalogue import SourceDescriptor, SourceKind, SourceRecord
from .preview import TargetStateSnapshot


def canonical_payload_sha256(payload: dict[str, Any]) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

def stable_id(prefix: str, material: str, length: int = 24) -> str:
    return prefix + sha256(material.encode()).hexdigest()[:length]

def candidate_id(record: SourceRecord) -> str:
    for key in ("administrative_candidate_id", "road_candidate_id", "feature_candidate_id", "geometry_version_candidate_id", "address_candidate_id", "parcel_id", "title_id", "state_land_record_id"):
        value = str(record.payload.get(key, "")).strip()
        if value: return value
    return record.source_id

@dataclass(frozen=True, slots=True)
class ExistingMapping:
    source_record_id: str
    canonical_id: str
    source_payload_sha256: str

class MemoryExecutionRepository:
    """Transactional in-memory adapter used by qualification tests."""
    def __init__(self, *, database_name="npp_dev", environment_name="development", capabilities=()):
        self.database_name=database_name; self.environment_name=environment_name
        self.capabilities=set(capabilities); self.crosswalks:dict[str,ExistingMapping]={}; self.canonical:dict[str,dict]={}
        self.receipts:dict[str,object]={}; self.staged:dict[str,dict]={}; self.quarantine:list[dict]=[]
    def target_snapshot(self):
        return TargetStateSnapshot(self.database_name,self.environment_name,frozenset(self.capabilities),frozenset(self.canonical),{k:v.canonical_id for k,v in self.crosswalks.items()})
    def existing_mapping(self, source_id): return self.crosswalks.get(source_id)
    @contextmanager
    def transaction(self):
        import copy
        state=copy.deepcopy((self.crosswalks,self.canonical,self.receipts,self.staged,self.quarantine))
        try: yield self
        except Exception:
            self.crosswalks,self.canonical,self.receipts,self.staged,self.quarantine=state; raise
    def register_source(self, descriptor, source_sha256, byte_size, row_count): pass
    def register_batch(self, *args, **kwargs): pass
    def stage(self, staged_id, record, family, batch_id): self.staged[staged_id]=dict(record.payload)
    def quarantine_record(self, staged_id, record, code, message): self.quarantine.append({"staged":staged_id,"source":record.source_id,"code":code,"message":message})
    def persist_canonical(self, descriptor, record, canonical_id, runtime_mode): self.canonical.setdefault(canonical_id,dict(record.payload))
    def persist_crosswalk(self, mapping:ExistingMapping): self.crosswalks[mapping.source_record_id]=mapping
    def persist_canonicalization_receipt(self,*args,**kwargs): pass
    def persist_execution_receipt(self, receipt): self.receipts[receipt.execution_id]=receipt
    def history(self): return tuple(self.receipts.values())

class PostgreSQLExecutionRepository:
    """DB-API adapter. Preview reads only; execution writes only inside caller transaction."""
    def __init__(self, connection, *, database_name:str, environment_name:str):
        self.connection=connection; self.database_name=database_name; self.environment_name=environment_name
    def target_snapshot(self):
        from .target_postgresql import PostgreSQLTargetInspector
        snapshot=PostgreSQLTargetInspector(self.connection).snapshot(self.database_name,self.environment_name)
        crosswalks={}
        with self.connection.cursor() as cur:
            cur.execute("SELECT to_regclass('geography.nngla_canonical_crosswalk') IS NOT NULL")
            if cur.fetchone()[0]:
                cur.execute("SELECT source_record_id,canonical_id FROM geography.nngla_canonical_crosswalk")
                crosswalks={str(a):str(b) for a,b in cur.fetchall()}
        return TargetStateSnapshot(snapshot.database_name,snapshot.environment_name,snapshot.schema_capabilities,snapshot.occupied_canonical_ids,crosswalks)
    def existing_mapping(self, source_id):
        with self.connection.cursor() as cur:
            cur.execute("""SELECT c.source_record_id,c.canonical_id,r.source_payload_sha256
                FROM geography.nngla_canonical_crosswalk c JOIN geography.nngla_canonicalization_receipt r ON r.crosswalk_id=c.crosswalk_id
                WHERE c.source_record_id=%s ORDER BY r.canonicalized_at DESC LIMIT 1""",(source_id,))
            row=cur.fetchone()
        return ExistingMapping(*map(str,row)) if row else None
    @contextmanager
    def transaction(self):
        try:
            yield self; self.connection.commit()
        except Exception:
            self.connection.rollback(); raise
    def register_source(self, descriptor:SourceDescriptor, source_sha256, byte_size, row_count):
        dataset_class = "REAL_EMPTY_GOVERNED_REGISTER" if descriptor.kind is SourceKind.EMPTY_GOVERNED_REGISTER else "REAL_COMPLETE_CONTROLLED_VOCABULARY" if descriptor.kind is SourceKind.REFERENCE_CATALOGUE else "REAL_POPULATED_DATASET"
        with self.connection.cursor() as cur:
            cur.execute("""INSERT INTO geography.nngla_source_dataset(dataset_id,dataset_version,dataset_class,migration_eligibility,data_classification,source_authority)
                VALUES(%s,%s,%s,'READY_FOR_MIGRATION_PLANNING','PUBLIC_REFERENCE','NNGLA') ON CONFLICT(dataset_id,dataset_version) DO NOTHING""",
                (descriptor.dataset_id,descriptor.dataset_version,dataset_class))
            artifact=stable_id("source-artifact:nngla:",f"{descriptor.dataset_id}|{descriptor.dataset_version}|{descriptor.relative_path}")
            cur.execute("""INSERT INTO geography.nngla_source_artifact(source_artifact_id,dataset_id,dataset_version,file_path,sha256,byte_size,row_count)
                VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(dataset_id,dataset_version,file_path) DO NOTHING""",
                (artifact,descriptor.dataset_id,descriptor.dataset_version,descriptor.relative_path,source_sha256,byte_size,row_count))
    def register_batch(self,batch_id,descriptor,runtime,effect_scope):
        with self.connection.cursor() as cur:
            cur.execute("""INSERT INTO geography.nngla_ingest_batch(ingest_batch_id,dataset_id,dataset_version,runtime_mode,effect_scope,data_classification,received_at)
                VALUES(%s,%s,%s,%s,%s,'PUBLIC_REFERENCE',now()) ON CONFLICT(ingest_batch_id) DO NOTHING""",
                (batch_id,descriptor.dataset_id,descriptor.dataset_version,runtime,effect_scope))
    def stage(self, staged_id, record, family, batch_id):
        with self.connection.cursor() as cur:
            cur.execute("""INSERT INTO geography.nngla_staged_record(staged_record_id,ingest_batch_id,source_record_id,source_file,source_row_number,record_family,candidate_id,pipeline_state,raw_payload,staged_at)
                VALUES(%s,%s,%s,%s,%s,%s,%s,'CANONICALIZATION_READY',%s::jsonb,now()) ON CONFLICT(ingest_batch_id,source_record_id) DO NOTHING""",
                (staged_id,batch_id,record.source_id,"governed-source",record.row_number,family,candidate_id(record),json.dumps(dict(record.payload))))
    def quarantine_record(self, staged_id, record, code, message):
        qid=stable_id("quarantine:nngla:",f"{staged_id}|{code}")
        with self.connection.cursor() as cur:
            cur.execute("""INSERT INTO geography.nngla_quarantine_record(quarantine_id,staged_record_id,error_code,error_message,raw_payload,quarantined_at)
                VALUES(%s,%s,%s,%s,%s::jsonb,now()) ON CONFLICT(quarantine_id) DO NOTHING""",(qid,staged_id,code,message,json.dumps(dict(record.payload))))
    def persist_canonical(self, descriptor:SourceDescriptor, record:SourceRecord, canonical_id:str|None, runtime_mode:str):
        p=record.payload; key=descriptor.source_key
        with self.connection.cursor() as cur:
            if key.startswith("names:"):
                family=key.split(":",1)[1].upper(); name_id=record.source_id
                name=str(p.get("canonical_name") or p.get("name") or ""); ascii_name=str(p.get("ascii_name") or name)
                cur.execute("""INSERT INTO geography.nngla_geographic_name(name_id,canonical_name,ascii_name,name_family,naming_status_code,runtime_effect_scope,source_dataset_id,source_basis,record_status)
                    VALUES(%s,%s,%s,%s,'PROPOSED','SHARED_REFERENCE',%s,'governed name catalogue','ACTIVE') ON CONFLICT(name_id) DO NOTHING""",
                    (name_id,name,ascii_name,family,descriptor.dataset_id)); return
            if key=="places":
                cur.execute("""INSERT INTO geography.nngla_geographic_name(name_id,canonical_name,ascii_name,name_family,naming_status_code,runtime_effect_scope,source_dataset_id,source_basis,record_status)
                    VALUES(%s,%s,%s,'SETTLEMENT',%s,'SHARED_REFERENCE',%s,%s,%s) ON CONFLICT(name_id) DO NOTHING""",
                    (p['settlement_name_record_id'],p['canonical_name'],p['ascii_name'],p['naming_status_code'],p['source_dataset_id'],p['source_basis'],p['record_status']))
                cur.execute("""INSERT INTO geography.nngla_place_reference(place_id,source_place_code,settlement_name_record_id,place_type_code,region_code,parent_source_place_code,spatial_assignment_status,geometry_reference,runtime_effect_scope,source_dataset_id)
                    VALUES(%s,%s,%s,%s,%s,NULLIF(%s,''),%s,NULLIF(%s,''),%s,%s) ON CONFLICT(place_id) DO NOTHING""",
                    (canonical_id,p['source_place_code'],p['settlement_name_record_id'],p['place_type_code'],p['region_code'],p['parent_source_place_code'],p['spatial_assignment_status'],p['geometry_reference'],p['runtime_effect_scope'],p['source_dataset_id'])); return
            if key=="administrative-areas":
                cur.execute("""INSERT INTO geography.nngla_administrative_area(administrative_area_id,administrative_candidate_id,source_record_id,administrative_type_code,canonical_name,parent_source_record_id,region_code,boundary_status,geometry_reference,lifecycle_status_code,runtime_effect_scope,candidate_status)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,NULLIF(%s,''),%s,%s,%s) ON CONFLICT(administrative_area_id) DO NOTHING""",
                    (canonical_id,p['administrative_candidate_id'],p['source_record_id'],p['administrative_type_code'],p['canonical_name'],p['parent_source_record_id'],p['region_code'],p['boundary_status'],p['geometry_reference'],p['lifecycle_status_code'],p['runtime_effect_scope'],p['candidate_status'])); return
            if key=="roads":
                cur.execute("""INSERT INTO geography.nngla_geographic_name(name_id,canonical_name,ascii_name,name_family,naming_status_code,runtime_effect_scope,source_dataset_id,source_basis,record_status)
                    VALUES(%s,%s,%s,'ROAD','PROPOSED','SHARED_REFERENCE',%s,%s,'ACTIVE') ON CONFLICT(name_id) DO NOTHING""",
                    (p['road_name_id'],p['canonical_name'],p['canonical_name'],descriptor.dataset_id,p['source_basis']))
                cur.execute("""INSERT INTO geography.nngla_road_reference_candidate(road_candidate_id,road_name_id,canonical_name,road_class_code,planning_status,geometry_status,geometry_reference,addressing_eligible,region_code,source_basis,runtime_effect_scope)
                    VALUES(%s,%s,%s,%s,%s,%s,NULLIF(%s,''),%s,NULLIF(%s,''),%s,%s) ON CONFLICT(road_candidate_id) DO NOTHING""",
                    (p['road_candidate_id'],p['road_name_id'],p['canonical_name'],p['road_class_code'],p['planning_status'],p['geometry_status'],p['geometry_reference'],str(p['addressing_eligible']).lower()=='true',p['region_code'],p['source_basis'],p['runtime_effect_scope']))
                cur.execute("""INSERT INTO geography.nngla_road(road_id,source_candidate_id,road_name_id,road_class_code,geometry_id,lifecycle_status,runtime_effect_scope)
                    VALUES(%s,%s,%s,%s,NULLIF(%s,''),%s,%s) ON CONFLICT(road_id) DO NOTHING""",
                    (canonical_id,p['road_candidate_id'],p['road_name_id'],p['road_class_code'],p['geometry_reference'],p['planning_status'],p['runtime_effect_scope'])); return
            if key=="geographic-features":
                cur.execute("""INSERT INTO geography.nngla_spatial_feature(feature_id,runtime_mode,effect_scope,record_family,lifecycle_status,effective_from,canonical_version,data_classification)
                    VALUES(%s,%s,%s,%s,%s,CURRENT_DATE,1,'PUBLIC_REFERENCE') ON CONFLICT DO NOTHING""",
                    (canonical_id,runtime_mode,p['runtime_effect_scope'],p['feature_type_code'],p['lifecycle_status_code'])); return
            if key=="geometry":
                geometry=load_geometry(record)
                cur.execute("""INSERT INTO geography.nngla_geometry_authority_record(geometry_id,subject_type,subject_id,geometry_role_code,source_geometry_id,source_dataset_id,source_version,geometry_type_code,crs_code,authoritative_level,vertex_count,part_count,valid_from,valid_to,supersedes_geometry_id,superseded_by_geometry_id,qualification_status,publication_status,checksum_sha256,source_path_reference,runtime_effect_scope)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NULLIF(%s,'')::int,NULLIF(%s,'')::int,%s,NULLIF(%s,'')::date,NULLIF(%s,''),NULLIF(%s,''),%s,%s,%s,%s,%s) ON CONFLICT(geometry_id) DO NOTHING""",
                    (canonical_id,p['subject_type'],p['subject_id'],p['geometry_role_code'],p['source_geometry_id'],p['source_dataset_id'],p['source_version'],p['geometry_type_code'],p['crs_code'],p['authoritative_level'],p['vertex_count'],p['part_count'],p['valid_from'],p['valid_to'],p['supersedes_geometry_id'],p['superseded_by_geometry_id'],p['qualification_status'],p['publication_status'],p['checksum_sha256'],p['source_path_reference'],p['runtime_effect_scope']))
                cur.execute("""INSERT INTO geography.nngla_geometry_version(geometry_id,subject_id,runtime_mode,geometry_role_code,crs_code,geometry_type_code,geometry,valid_from,valid_to,supersedes_geometry_id,source_sha256)
                    VALUES(%s,%s,%s,%s,%s,%s,ST_SetSRID(ST_GeomFromGeoJSON(%s),4326),%s,NULLIF(%s,'')::date,NULLIF(%s,''),%s) ON CONFLICT(geometry_id) DO NOTHING""",
                    (canonical_id,p['subject_id'],runtime_mode,p['geometry_role_code'],p['crs_code'],p['geometry_type_code'],json.dumps(geometry),p['valid_from'],p['valid_to'],p['supersedes_geometry_id'],p['checksum_sha256'])); return
            if key=="sovereign-boundary":
                from .source_catalogue import ROOT
                base=ROOT/"data/novegeo/geography/world-boundary"
                source=json.loads((base/"provenance/novegeo_world_boundary_v002_source-package.json").read_text())
                qual=json.loads((base/"qualification/novegeo_world_boundary_v002_qualification.json").read_text())
                pub=json.loads((base/"publication/v002/publication-manifest.json").read_text())
                geometry=json.loads((base/"candidate/novegeo_world_boundary_v002.geojson").read_text())["features"][0]["geometry"]
                crs=pub["coordinateReference"]
                cur.execute("""INSERT INTO geography.coordinate_reference(coordinate_reference_id,version,authority_name,authority_code,application_axis_order,unit,lifecycle_status,content_sha256) VALUES(%s,%s,%s,%s,%s,%s,'active',%s) ON CONFLICT DO NOTHING""",(crs["coordinateReferenceId"],crs["version"],crs["authorityName"],crs["authorityCode"],crs["axisOrder"],crs["unit"],pub["contentSha256"]))
                cur.execute("""INSERT INTO geography.world_boundary(boundary_id,dataset_id,semantic_name) VALUES(%s,%s,'NoveGeo Sovereign Boundary') ON CONFLICT DO NOTHING""",(source["boundaryId"],source["datasetId"]))
                cur.execute("""INSERT INTO geography.source_package(source_package_id,dataset_id,dataset_version,source_sha256,media_type,runtime_mode,visibility) VALUES(%s,%s,%s,%s,'application/geo+json',%s,%s) ON CONFLICT DO NOTHING""",(source["sourcePackageId"],source["datasetId"],source["datasetVersion"],source["artifacts"]["candidateGeoJson"]["sha256"],source["runtimeMode"],source["visibility"]))
                cur.execute("""INSERT INTO geography.world_boundary_version(boundary_id,boundary_version,coordinate_reference_id,coordinate_reference_version,source_package_id,runtime_mode,visibility,lifecycle_status,geometry,content_sha256,supersedes_version) VALUES(%s,%s,%s,%s,%s,%s,%s,'active',ST_SetSRID(ST_GeomFromGeoJSON(%s),4326),%s,%s) ON CONFLICT DO NOTHING""",(source["boundaryId"],source["boundaryVersion"],source["coordinateReferenceId"],source["coordinateReferenceVersion"],source["sourcePackageId"],source["runtimeMode"],source["visibility"],json.dumps(geometry),source["artifacts"]["candidateGeoJson"]["sha256"],source["supersedesBoundaryVersion"]))
                cur.execute("""INSERT INTO geography.boundary_qualification(qualification_id,boundary_id,boundary_version,validation_receipt_id,submitter_actor_id,approver_actor_id,decision,receipt_sha256) VALUES(%s,%s,%s,%s,'actor:nexadevs:source','actor:nexadevs:approver',%s,%s) ON CONFLICT DO NOTHING""",(qual["qualificationId"],qual["boundaryId"],qual["boundaryVersion"],qual["contractId"],qual["decision"],qual["receiptSha256"]))
                cur.execute("""INSERT INTO geography.boundary_publication(publication_id,boundary_id,boundary_version,runtime_mode,visibility,lifecycle_status,content_sha256) VALUES(%s,%s,%s,%s,%s,'active',%s) ON CONFLICT DO NOTHING""",(pub["publicationId"],pub["boundaryId"],pub["boundaryVersion"],pub["runtimeMode"],pub["visibility"],pub["contentSha256"]))
                return
            if key in {"addresses","parcels","titles","state-land","survey-control"}: return
            raise ValueError(f"unsupported canonical persistence source: {key}")
    def persist_crosswalk(self,mapping:ExistingMapping,*,descriptor=None,candidate=None,runtime_mode='production',effect_scope='SHARED_REFERENCE'):
        xwid=stable_id("crosswalk:nngla:",f"{descriptor.dataset_id}|{descriptor.dataset_version}|{mapping.source_record_id}|{runtime_mode}|{effect_scope}")
        with self.connection.cursor() as cur:
            cur.execute("""INSERT INTO geography.nngla_canonical_crosswalk(crosswalk_id,dataset_id,dataset_version,source_record_id,candidate_id,canonical_id,canonical_version,runtime_mode,effect_scope)
                VALUES(%s,%s,%s,%s,%s,%s,1,%s,%s) ON CONFLICT(dataset_id,dataset_version,source_record_id,runtime_mode,effect_scope) DO NOTHING""",
                (xwid,descriptor.dataset_id,descriptor.dataset_version,mapping.source_record_id,candidate or mapping.source_record_id,mapping.canonical_id,runtime_mode,effect_scope))
        return xwid
    def persist_canonicalization_receipt(self,receipt_id,crosswalk_id,staged_id,payload_sha,validation_refs):
        with self.connection.cursor() as cur:
            cur.execute("""INSERT INTO geography.nngla_canonicalization_receipt(receipt_id,crosswalk_id,staged_record_id,source_payload_sha256,validation_references,canonicalized_at,dry_run)
                VALUES(%s,%s,%s,%s,%s::jsonb,now(),false) ON CONFLICT(receipt_id) DO NOTHING""",
                (receipt_id,crosswalk_id,staged_id,payload_sha,json.dumps(list(validation_refs))))
    def persist_execution_receipt(self,receipt):
        with self.connection.cursor() as cur:
            cur.execute("""INSERT INTO geography.nngla_execution_receipt(execution_id,plan_id,plan_version,fingerprint_sha256,database_name,environment_name,runtime_mode,repository_revision,source_sha256,submitter_actor_id,approver_actor_id,selected_count,inserted_count,reused_count,quarantined_count,failed_count,status,started_at,completed_at)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(execution_id) DO NOTHING""",
                (receipt.execution_id,receipt.plan_id,receipt.plan_version,receipt.fingerprint,receipt.database_name,receipt.environment_name,receipt.runtime_mode,receipt.repository_revision,receipt.source_sha256,receipt.submitter_actor_id,receipt.approver_actor_id,receipt.selected_count,receipt.inserted_count,receipt.reused_count,receipt.quarantined_count,receipt.failed_count,receipt.status,receipt.started_at,receipt.completed_at))
            for item in receipt.items:
                cur.execute("""INSERT INTO geography.nngla_execution_item(execution_id,source_record_id,canonical_id,outcome,crosswalk_id,canonicalization_receipt_id,event_id,audit_id,publication_ready,detail)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb) ON CONFLICT(execution_id,source_record_id) DO NOTHING""",
                    (receipt.execution_id,item.source_record_id,item.canonical_id,item.outcome,item.crosswalk_id,item.canonicalization_receipt_id,item.event_id,item.audit_id,item.publication_ready,json.dumps(item.detail or {})))
    def history(self):
        with self.connection.cursor() as cur:
            cur.execute("SELECT execution_id,plan_id,fingerprint_sha256,status,selected_count,inserted_count,reused_count,quarantined_count,failed_count,completed_at FROM geography.nngla_execution_receipt ORDER BY completed_at,execution_id")
            return tuple(cur.fetchall())

__all__=["ExistingMapping","MemoryExecutionRepository","PostgreSQLExecutionRepository","canonical_payload_sha256","stable_id","candidate_id"]
