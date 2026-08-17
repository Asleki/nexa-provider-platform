
from registries.nngla.spatial_fabric.bundle17m import artifact_paths
from registries.nngla.spatial_fabric.bundle17m._shared import csv_rows

def test_required_17m_artifacts_exist_and_runtime_registers_are_truthfully_empty():
    p=artifact_paths(); assert all(x.exists() for x in p.values()); assert len(csv_rows(p['name_families']))==19 and len(csv_rows(p['assignment_rules']))==19 and len(csv_rows(p['reservations']))==0 and len(csv_rows(p['gazette_candidates']))==0 and len(csv_rows(p['assignment_results']))==20
