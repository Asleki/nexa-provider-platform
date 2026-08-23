from collections import Counter
from registries.nngla.spatial_fabric.bundle21a.source import current_candidates

def test_current_candidate_inventory_excludes_sovereign_boundary_and_internal_spatial_points():
    c=current_candidates(); assert len(c)==1262
    assert Counter(x.record_family for x in c)==Counter({'PLACE':700,'ADMINISTRATIVE_AREA':192,'ROAD':350,'GEOGRAPHIC_FEATURE':20})
    assert all(not x.subject_id.startswith('NG-SPT-') for x in c)
