from __future__ import annotations
from .geometry_guard import geometry_namespace_baseline
from .postgresql_contract import load_schema17j_sql,qualify_schema17j_sql
from .recovery import collision_contract,different_scope_visible_number_contract,idempotent_address_replay
from .stress import run_address_stress,run_address_display_stress,run_parcel_stress,run_site_stress,run_title_stress
def bundle17j_is_qualified():
    results=(run_address_stress(1000),run_address_display_stress(1000),run_parcel_stress(1000),run_site_stress(1000),run_title_stress(1000))
    b=geometry_namespace_baseline()
    return all(r.status=='PASS' and r.duplicate_identity_count==0 for r in results) and b['max_geometry_id']=='NG-GEO-002432' and b['next_candidate_id']=='NG-GEO-002433' and b['collision_free'] and collision_contract() and different_scope_visible_number_contract() and idempotent_address_replay() and qualify_schema17j_sql(load_schema17j_sql())==()
__all__=['bundle17j_is_qualified']
