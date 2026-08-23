import csv,json
from registries.nngla.spatial_fabric.bundle21a.materialize import materialize
from registries.nngla.spatial_fabric.bundle21a._shared import CANDIDATES,DECISIONS,PROJECTION_CANDIDATES,SUMMARY

def test_bundle21a_artifacts_are_truthful_pre_live_execution():
    s=materialize(); assert s['total_candidates']==1262 and s['current_public_decisions']==0 and s['excluded_internal_spatial_reference_points']==2411
    assert len(list(csv.DictReader(open(CANDIDATES))))==1262
    assert len(list(csv.DictReader(open(DECISIONS))))==1262
    assert len(list(csv.DictReader(open(PROJECTION_CANDIDATES))))==1262
    assert json.load(open(SUMMARY))['publication_policy'].startswith('FAIL_CLOSED')
