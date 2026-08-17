from datetime import date
from registries.nngla.spatial_fabric.bundle17k import *
from registries.nngla.spatial_fabric.bundle17k._shared import DAY_ZERO_CONTROL_PATH,csv_rows

def test_bundle17k_contract_preserves_identity_and_history_with_new_geometry_ids():
 a=MemoryGeometryIdAllocator(); new=a.reserve(idempotency_key='contract:geometry'); c=form_geometry_change_candidate(subject_type='ROAD',subject_id='NG-RD-000001',geometry_role_code='ROAD_ALIGNMENT',current_geometry_id='NG-GEO-000002',proposed_geometry_reference='contract:new',change_reason_code='REALIGNMENT',change_nature='REALIGNMENT',source_reference='contract',runtime_mode='production',effective_on='2026-08-18'); c=bind_reserved_geometry(c,new); l=form_supersession(c); assert c.subject_id=='NG-RD-000001' and new=='NG-GEO-002433' and l.predecessor_geometry_id=='NG-GEO-000002'
def test_bundle17k_contract_keeps_correction_subdivision_and_physical_state_semantically_distinct():
 sub=form_subdivision('NV-01-001-0001',('NV-01-001-0002','NV-01-001-0003'),effective_on=date(2026,8,17),source_reference='contract'); st=form_physical_state_change(subject_type='ISLAND',subject_id='NG-FEAT-000001',prior_state='EXPOSED',proposed_state='PARTIALLY_SUBMERGED',source_reference='contract'); assert sub.action.value=='SUBDIVISION' and st.geometry_change_candidate_id==''
def test_bundle17k_contract_preserves_day_zero_survey_and_sql_is_additive():
 assert csv_rows(DAY_ZERO_CONTROL_PATH)==(); assert qualify_schema17k_sql(load_schema17k_sql())==(); assert bundle17k_is_qualified()
