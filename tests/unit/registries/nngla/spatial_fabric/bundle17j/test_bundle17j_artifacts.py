from csv import DictReader
from registries.nngla.spatial_fabric.bundle17j import artifact_paths

def rows(p):
 with p.open(encoding='utf-8') as h:return tuple(DictReader(h))
def test_required_evidence_artifacts_present_and_populated():
 paths=artifact_paths(); assert set(paths)=={'novegeo_allocator_concurrency_scenarios','novegeo_allocator_collision_cases','novegeo_allocator_recovery_cases','novegeo_allocator_expected_results','novegeo_allocator_stress_results'}; assert all(p.exists() for p in paths.values()); assert all(rows(p) for p in paths.values())
def test_stress_evidence_never_falsely_claims_postgresql_execution():
 r=rows(artifact_paths()['novegeo_allocator_stress_results']); pg=[x for x in r if x['execution_basis']=='POSTGRESQL_INTEGRATION']; assert len(pg)==1 and pg[0]['status']=='CONTRACT_READY_NOT_EXECUTED'
