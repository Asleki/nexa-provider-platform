import csv,json
from registries.nngla.spatial_fabric.bundle20b.materialize import materialize
from registries.nngla.spatial_fabric.bundle20b._shared import GEOGRAPHIC_NAMES,LANDFORM_EXTENTS,SUMMARY

def test_bundle20b_artifacts_materialize():
    c=materialize(); assert c['physical_feature_names']==20 and c['landform_extent_candidates']==11
    assert len(list(csv.DictReader(open(GEOGRAPHIC_NAMES))))==20
    assert len(json.load(open(LANDFORM_EXTENTS))['features'])==11
    assert 'NO_AUTOMATIC_OFFICIAL_EFFECT' in json.load(open(SUMMARY))['naming_effect']
