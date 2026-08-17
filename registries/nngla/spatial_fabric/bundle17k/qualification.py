from __future__ import annotations
from ._shared import DAY_ZERO_CONTROL_PATH,csv_rows
from .geometry_allocator import MemoryGeometryIdAllocator
from .changes import form_geometry_change_candidate,bind_reserved_geometry,form_supersession
from .postgresql_contract import load_schema17k_sql,qualify_schema17k_sql
def bundle17k_is_qualified():
 if csv_rows(DAY_ZERO_CONTROL_PATH)!=(): return False
 a=MemoryGeometryIdAllocator(); gid=a.reserve(idempotency_key='17k:qualification')
 c=form_geometry_change_candidate(subject_type='ROAD',subject_id='NG-RD-000001',geometry_role_code='ROAD_ALIGNMENT',current_geometry_id='NG-GEO-000002',proposed_geometry_reference='fixture:17k',change_reason_code='SURVEY_CORRECTION',change_nature='CORRECTION',source_reference='fixture:17k',runtime_mode='production',effective_on='2026-08-17')
 c=bind_reserved_geometry(c,gid); link=form_supersession(c)
 return gid=='NG-GEO-002433' and link.predecessor_geometry_id!=link.successor_geometry_id and qualify_schema17k_sql(load_schema17k_sql())==()
__all__=['bundle17k_is_qualified']
