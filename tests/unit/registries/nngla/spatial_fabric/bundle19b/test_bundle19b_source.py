from collections import Counter
from registries.nngla.spatial_fabric.bundle19b._shared import EXPECTED_TYPE_COUNTS
from registries.nngla.spatial_fabric.bundle19b.source import load_administrative_baseline,load_place_reference_evidence
def test_locked_admin_baseline_is_exact_and_unmapped():
 rows=load_administrative_baseline(); assert len(rows)==192; assert Counter(r['administrative_type_code'] for r in rows)==Counter(EXPECTED_TYPE_COUNTS)
 assert [r['administrative_area_id'] for r in rows]==[f'NG-ADM-{i:06d}' for i in range(1,193)]
 assert all(r['boundary_status']=='BOUNDARY_PENDING_LEGALIZATION' and not r['geometry_reference'] and r['lifecycle_status_code']=='PROVISIONAL' for r in rows)
def test_bundle19a_place_spatial_evidence_is_complete(): assert len(load_place_reference_evidence())==700
