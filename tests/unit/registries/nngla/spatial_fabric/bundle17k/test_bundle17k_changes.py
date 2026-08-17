import pytest
from registries.nngla.spatial_fabric.bundle17k import *

def test_same_subject_keeps_identity_while_geometry_version_changes():
 c=form_geometry_change_candidate(subject_type='ROAD',subject_id='NG-RD-000001',geometry_role_code='ROAD_ALIGNMENT',current_geometry_id='NG-GEO-000002',proposed_geometry_reference='fixture:new',change_reason_code='REALIGNMENT',change_nature='REALIGNMENT',source_reference='test',runtime_mode='production',effective_on='2026-08-18')
 c=bind_reserved_geometry(c,MemoryGeometryIdAllocator().reserve(idempotency_key='road')); link=form_supersession(c)
 assert c.subject_id=='NG-RD-000001' and link.predecessor_geometry_id!=link.successor_geometry_id
def test_correction_and_physical_change_are_distinct(): assert GeometryChangeNature.CORRECTION!=GeometryChangeNature.PHYSICAL_CHANGE
def test_physical_state_change_does_not_require_geometry_change():
 r=form_physical_state_change(subject_type='ISLAND',subject_id='NG-FEAT-000001',prior_state='EXPOSED',proposed_state='PARTIALLY_SUBMERGED',source_reference='test'); assert r.geometry_change_candidate_id==''
def test_supersession_requires_new_reserved_geometry():
 c=form_geometry_change_candidate(subject_type='RIVER',subject_id='NG-FEAT-000002',geometry_role_code='CENTERLINE',current_geometry_id='NG-GEO-000003',proposed_geometry_reference='fixture',change_reason_code='SHIFT',change_nature='PHYSICAL_CHANGE',source_reference='test')
 with pytest.raises(ValueError): form_supersession(c)
