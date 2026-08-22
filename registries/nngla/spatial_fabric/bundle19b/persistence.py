"""Transactional memory/PostgreSQL persistence for P006.7.11.11."""
from __future__ import annotations
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime,timezone
import json
from registries.nngla.spatial_fabric.bundle17k.geometry_allocator import MemoryGeometryIdAllocator
from ._shared import EFFECT_SCOPE,RUNTIME_MODE,CRS_CODE,BUNDLE_EFFECTIVE_DATE,DATASET_ID,DATASET_VERSION,SOVEREIGN_BOUNDARY_ID,SOVEREIGN_BOUNDARY_VERSION,payload_sha256,stable_id
from .contracts import GeometryRole,AdministrativeBoundaryExecutionReceipt
from .source import load_administrative_baseline
from .postgresql_contract import REQUIRED_RELATIONS
class MemoryAdministrativeBoundaryRepository:
    def __init__(self,database_name='memory_novegeo',environment_name='test',place_spatial_ready=True):
        self.database_name=database_name; self.environment_name=environment_name; self.place_spatial_ready=place_spatial_ready
        self.admins={r['administrative_area_id']:{'candidate':r['administrative_candidate_id'],'source':r['source_record_id'],'boundary_status':'BOUNDARY_PENDING_LEGALIZATION','geometry_reference':None,'lifecycle':'PROVISIONAL'} for r in load_administrative_baseline()}
        self.allocator=MemoryGeometryIdAllocator(); self.geometries={}; self.receipts={}; self.execution_items={}
    @contextmanager
    def transaction(self):
        state=(deepcopy(self.admins),deepcopy(self.geometries),dict(self.receipts),deepcopy(self.execution_items),(set(self.allocator._occupied),int(self.allocator._next),dict(self.allocator._by_key)))
        try: yield self
        except Exception:
            self.admins,self.geometries,self.receipts,self.execution_items,a=state; self.allocator._occupied,self.allocator._next,self.allocator._by_key=set(a[0]),a[1],dict(a[2]); raise
    def replay(self,f):
        r=self.receipts.get(f)
        if not r:return None
        return AdministrativeBoundaryExecutionReceipt(r.execution_id,r.fingerprint_sha256,r.database_name,r.environment_name,r.repository_revision,r.submitter_actor_id,r.approver_actor_id,r.selected_count,r.legalized_count,r.geometry_insert_count,'REUSED',True)
    def preflight(self):
        if not self.place_spatial_ready: raise RuntimeError('P006.7.11.10 place spatial association must be complete')
        if len(self.admins)!=192: raise RuntimeError('exactly 192 canonical administrative areas required')
        if any(x['boundary_status']!='BOUNDARY_PENDING_LEGALIZATION' or x['geometry_reference'] is not None or x['lifecycle']!='PROVISIONAL' for x in self.admins.values()): raise RuntimeError('administrative baseline is not pristine')
    def qualify_geometry(self,c):
        if c.geometry['type'] not in {'Polygon','MultiPolygon'}: raise ValueError('polygonal administrative geometry required')
    def reserve_geometry(self,c): return self.allocator.reserve(idempotency_key=c.geometry_reservation_key,authority_runtime_mode='production')
    def persist_geometry(self,c,gid):
        if gid in self.geometries: raise ValueError('geometry collision')
        self.geometries[gid]={'subject_id':c.administrative_area_id,'role':'ADMINISTRATIVE_BOUNDARY','payload':deepcopy(c.geometry),'checksum':payload_sha256(c.geometry)}
    def legalize(self,c,gid):
        a=self.admins[c.administrative_area_id]
        if a['candidate']!=c.administrative_candidate_id or a['source']!=c.source_record_id: raise ValueError('administrative identity mismatch')
        if a['boundary_status']!='BOUNDARY_PENDING_LEGALIZATION' or a['geometry_reference'] is not None: raise ValueError('area not eligible')
        g=self.geometries.get(gid)
        if not g or g['subject_id']!=c.administrative_area_id: raise ValueError('boundary geometry subject mismatch')
        a.update(boundary_status='LEGALIZED',geometry_reference=gid,lifecycle='ACTIVE')
    def persist_execution_receipt(self,r,item_details): self.receipts[r.fingerprint_sha256]=r; self.execution_items[r.execution_id]=deepcopy(item_details)
class PostgreSQLAdministrativeBoundaryRepository:
    def __init__(self,connection,environment_name): self.connection=connection; self.environment_name=environment_name
    @property
    def database_name(self):
        with self.connection.cursor() as c:c.execute('SELECT current_database()');return str(c.fetchone()[0])
    @contextmanager
    def transaction(self):
        try:yield self;self.connection.commit()
        except Exception:self.connection.rollback();raise
    def replay(self,f): return None
    def preflight(self):
        with self.connection.cursor() as c:
            for rel in REQUIRED_RELATIONS:
                c.execute('SELECT to_regclass(%s) IS NOT NULL',(rel,));
                if not c.fetchone()[0]: raise RuntimeError('required relation unavailable: '+rel)
            c.execute("SELECT COUNT(*) FROM geography.nngla_place_reference WHERE spatial_assignment_status='AUTHORITATIVE_GEOMETRY_ASSIGNED' AND geometry_reference IS NOT NULL")
            if int(c.fetchone()[0])!=700: raise RuntimeError('P006.7.11.10 live place association must be complete before .11')
            c.execute("SELECT administrative_area_id,administrative_candidate_id,source_record_id,boundary_status,geometry_reference,lifecycle_status_code FROM geography.nngla_administrative_area ORDER BY administrative_area_id")
            actual=c.fetchall(); exp=load_administrative_baseline()
            if len(actual)!=192: raise RuntimeError('live target must contain exactly 192 administrative areas')
            for a,e in zip(actual,exp):
                if str(a[0])!=e['administrative_area_id'] or str(a[1])!=e['administrative_candidate_id'] or str(a[2])!=e['source_record_id']: raise RuntimeError('canonical administrative identity mismatch')
                if str(a[3])!='BOUNDARY_PENDING_LEGALIZATION' or a[4] is not None or str(a[5])!='PROVISIONAL': raise RuntimeError('administrative area not eligible for initial legalization')
    def qualify_geometry(self,candidate):
        gj=json.dumps(candidate.geometry,separators=(',',':'))
        with self.connection.cursor() as c:
            c.execute("WITH x AS (SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s),4326) g), b AS (SELECT geometry FROM geography.world_boundary_version WHERE boundary_id=%s AND boundary_version=%s AND lifecycle_status='active' LIMIT 1) SELECT ST_IsValid(x.g),NOT ST_IsEmpty(x.g),ST_SRID(x.g)=4326,GeometryType(x.g) IN ('POLYGON','MULTIPOLYGON'),ST_CoveredBy(x.g,b.geometry) FROM x CROSS JOIN b",(gj,SOVEREIGN_BOUNDARY_ID,SOVEREIGN_BOUNDARY_VERSION)); row=c.fetchone()
            if row is None or not all(bool(v) for v in row): raise ValueError('PostGIS qualification failed: '+candidate.administrative_area_id)
    def reserve_geometry(self,candidate):
        rid=stable_id('georeserve:admin:nngla:',candidate.administrative_area_id,candidate.geometry_reservation_key)
        with self.connection.cursor() as c:c.execute('SELECT geography.nngla_reserve_geometry_id(%s,%s,%s,%s)',(rid,candidate.geometry_reservation_key,candidate.administrative_area_id,'ADMINISTRATIVE_BOUNDARY'));return str(c.fetchone()[0])
    def persist_geometry(self,candidate,gid):
        gj=json.dumps(candidate.geometry,separators=(',',':')); checksum=payload_sha256(candidate.geometry)
        coords=candidate.geometry['coordinates']; parts=len(coords) if candidate.geometry['type']=='MultiPolygon' else 1
        def vc(g):
            if g['type']=='Polygon':return sum(len(r) for r in g['coordinates'])
            return sum(len(r) for p in g['coordinates'] for r in p)
        with self.connection.cursor() as c:
            c.execute("INSERT INTO geography.nngla_geometry_authority_record(geometry_id,subject_type,subject_id,geometry_role_code,source_geometry_id,source_dataset_id,source_version,geometry_type_code,crs_code,authoritative_level,vertex_count,part_count,valid_from,valid_to,supersedes_geometry_id,superseded_by_geometry_id,qualification_status,publication_status,checksum_sha256,source_path_reference,runtime_effect_scope) VALUES(%s,'ADMINISTRATIVE_AREA',%s,'ADMINISTRATIVE_BOUNDARY',%s,%s,%s,%s,%s,'QUALIFIED_LEGAL_ADMINISTRATIVE_BOUNDARY',%s,%s,%s,NULL,NULL,NULL,'QUALIFIED','NOT_PUBLISHED',%s,'data/novegeo/nngla/spatial-fabric/bundle19b/qualified/novegeo_administrative_boundaries_v001.geojson',%s)",(gid,candidate.administrative_area_id,candidate.boundary_candidate_id,DATASET_ID,DATASET_VERSION,candidate.geometry_type_code,CRS_CODE,vc(candidate.geometry),parts,BUNDLE_EFFECTIVE_DATE,checksum,EFFECT_SCOPE))
            c.execute("INSERT INTO geography.nngla_geometry_version(geometry_id,subject_id,runtime_mode,geometry_role_code,crs_code,geometry_type_code,geometry,valid_from,valid_to,supersedes_geometry_id,source_sha256) VALUES(%s,%s,%s,'ADMINISTRATIVE_BOUNDARY',%s,%s,ST_SetSRID(ST_GeomFromGeoJSON(%s),4326),%s,NULL,NULL,%s)",(gid,candidate.administrative_area_id,RUNTIME_MODE,CRS_CODE,candidate.geometry_type_code,gj,BUNDLE_EFFECTIVE_DATE,checksum))
    def legalize(self,candidate,gid):
        with self.connection.cursor() as c:
            c.execute("UPDATE geography.nngla_administrative_area SET boundary_status='LEGALIZED',geometry_reference=%s,lifecycle_status_code='ACTIVE',candidate_status='LEGALIZED' WHERE administrative_area_id=%s AND administrative_candidate_id=%s AND source_record_id=%s AND boundary_status='BOUNDARY_PENDING_LEGALIZATION' AND geometry_reference IS NULL AND lifecycle_status_code='PROVISIONAL' RETURNING administrative_area_id",(gid,candidate.administrative_area_id,candidate.administrative_candidate_id,candidate.source_record_id))
            if c.fetchone() is None: raise RuntimeError('fail-closed administrative legalization rejected: '+candidate.administrative_area_id)
    def persist_execution_receipt(self,r,item_details):
        now=datetime.now(timezone.utc)
        with self.connection.cursor() as c:
            c.execute("INSERT INTO geography.nngla_execution_receipt(execution_id,plan_id,plan_version,fingerprint_sha256,database_name,environment_name,runtime_mode,repository_revision,source_sha256,submitter_actor_id,approver_actor_id,selected_count,inserted_count,reused_count,quarantined_count,failed_count,status,started_at,completed_at) VALUES(%s,'p006.7.11.11-administrative-boundary-legalization',1,%s,current_database(),%s,%s,%s,%s,%s,%s,192,192,0,0,0,'APPLIED',%s,%s)",(r.execution_id,r.fingerprint_sha256,self.environment_name,RUNTIME_MODE,r.repository_revision,r.fingerprint_sha256,r.submitter_actor_id,r.approver_actor_id,now,now))
            for item in item_details:c.execute("INSERT INTO geography.nngla_execution_item(execution_id,source_record_id,canonical_id,outcome,publication_ready,detail) VALUES(%s,%s,%s,'LEGALIZED',false,%s::jsonb)",(r.execution_id,item['source_record_id'],item['administrative_area_id'],json.dumps(item,sort_keys=True,separators=(',',':'))))
