from collections import Counter
from registries.nngla.spatial_fabric.bundle19b.authoring import load_boundary_candidates
from registries.nngla.spatial_fabric.bundle19b.legalization import load_legalization_decisions
from registries.nngla.spatial_fabric.bundle19b.postgresql_contract import bundle19b_requires_schema_migration
from registries.nngla.spatial_fabric.bundle19b.qualification import qualification_findings
from registries.nngla.spatial_fabric.bundle19b.source import load_administrative_baseline

def test_p006_7_11_11_locks_administrative_identity_topology_and_legalization():
 baseline=load_administrative_baseline(); boundaries=load_boundary_candidates(); decisions=load_legalization_decisions()
 assert qualification_findings()==(); assert len(baseline)==len(boundaries)==len(decisions)==192
 assert [r['administrative_area_id'] for r in baseline]==[x.administrative_area_id for x in boundaries]==[f'NG-ADM-{i:06d}' for i in range(1,193)]
 assert Counter(x.administrative_type_code for x in boundaries)==Counter({'TOWNSHIP':72,'CITY_DISTRICT':64,'MUNICIPALITY':24,'INDUSTRIAL_ZONE':16,'CITY':8,'REGION':8})
 assert all(x.geometry_role_code=='ADMINISTRATIVE_BOUNDARY' for x in boundaries)
 assert all(x.resulting_boundary_status=='LEGALIZED' and x.resulting_lifecycle_status=='ACTIVE' for x in boundaries)
 assert all(x.geometry_reservation_key.startswith('p006.7.11.11:administrative-boundary:NG-ADM-') for x in boundaries)
 assert bundle19b_requires_schema_migration() is False
