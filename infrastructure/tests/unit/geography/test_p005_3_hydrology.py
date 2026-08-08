from pathlib import Path
import json
import pytest
from infrastructure.geography.hydrology import validate_hydrology_dataset, qualify_hydrology_dataset, HydrologyValidationError
ROOT=Path(__file__).resolve().parents[4]
PATH=ROOT/'data/novegeo/geography/hydrology/qualified/novegeo_hydrology_v001.json'

def test_p005_3_hydrology_is_qualified_and_terrain_descending():
    value=json.loads(PATH.read_text())
    validate_hydrology_dataset(value)
    receipt=qualify_hydrology_dataset(PATH)
    assert receipt.decision=='qualified'
    assert receipt.river_count==5
    assert receipt.lake_count==3
    assert receipt.drainage_network_count==4
    for river in value['rivers']:
        profile=river['elevationProfileMeters']
        assert all(b<a for a,b in zip(profile,profile[1:]))

def test_p005_3_rejects_uphill_river_flow():
    value=json.loads(PATH.read_text())
    value['rivers'][0]['elevationProfileMeters'][1]=value['rivers'][0]['elevationProfileMeters'][0]+1
    with pytest.raises(HydrologyValidationError,match='descend'):
        validate_hydrology_dataset(value)

def test_bundle_11_0b_river_confluences_are_exact_shared_coordinates():
    value=json.loads(PATH.read_text())
    validate_hydrology_dataset(value)
    rivers={river['riverId']:river for river in value['rivers']}
    junctions={junction['junctionId']:junction for junction in value['junctions']}
    assert len(junctions)==4
    for river in value['rivers']:
        jid=river.get('downstreamJunctionId')
        if not jid:
            assert river['riverClass']=='principal'
            continue
        junction=junctions[jid]
        coordinate=[junction['coordinate']['longitude'],junction['coordinate']['latitude']]
        assert river['geometry']['coordinates'][-1]==coordinate
        assert coordinate in rivers[river['downstreamRiverId']]['geometry']['coordinates']
        assert river['riverId'] in junction['incomingRiverIds']


def test_bundle_11_0b_rejects_near_miss_confluence_and_preserves_lakes_without_distributaries():
    value=json.loads(PATH.read_text())
    assert all(lake['hydrologicRole']=='closed_basin_lake' and lake['surfaceOutlet']=='none_declared' for lake in value['lakes'])
    assert all(not network['riverIds'] and not network['junctionIds'] for network in value['drainageNetworks'] if network['outletType']=='closed_basin')
    incoming=next(river for river in value['rivers'] if river.get('downstreamJunctionId'))
    incoming['geometry']['coordinates'][-1][0]+=0.000001
    with pytest.raises(HydrologyValidationError,match='exact shared coordinate'):
        validate_hydrology_dataset(value)
