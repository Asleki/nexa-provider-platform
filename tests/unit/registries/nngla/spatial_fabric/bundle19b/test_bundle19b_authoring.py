from collections import Counter
from registries.nngla.spatial_fabric.bundle19b.authoring import load_boundary_candidates
def test_boundary_authoring_materializes_all_192_without_identity_replacement():
 rows=load_boundary_candidates(); assert len(rows)==192; assert [x.administrative_area_id for x in rows]==[f'NG-ADM-{i:06d}' for i in range(1,193)]
 assert all(x.geometry_role_code=='ADMINISTRATIVE_BOUNDARY' and x.qualification_status=='QUALIFIED' for x in rows)
def test_boundary_geometry_supports_polygon_and_multipolygon():
 c=Counter(x.geometry_type_code for x in load_boundary_candidates()); assert c['POLYGON']==183 and c['MULTIPOLYGON']==9
