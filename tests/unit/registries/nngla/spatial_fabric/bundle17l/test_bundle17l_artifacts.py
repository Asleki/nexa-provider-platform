
from registries.nngla.spatial_fabric.bundle17l import artifact_paths
from registries.nngla.spatial_fabric.bundle17l._shared import csv_rows

def test_required_17l_artifacts_exist_with_truthful_counts():
    p=artifact_paths(); assert all(x.exists() for x in p.values()); assert len(csv_rows(p['qualification_rules']))==22; assert len(csv_rows(p['recognition_candidates']))==37; assert len(csv_rows(p['observation_links']))==49; assert len(csv_rows(p['recognition_results']))==37
