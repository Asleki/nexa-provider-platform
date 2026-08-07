import json
from pathlib import Path
import pytest
from infrastructure.geography.refinement import BoundaryRefinementError, qualify_v002_boundary, build_v001_to_v002_supersession
ROOT=Path(__file__).parents[4]; BOUNDARY_ROOT=ROOT/'data/novegeo/geography/world-boundary'

def test_v002_qualification_is_deterministic_and_preserves_high_resolution_source():
    first=qualify_v002_boundary(BOUNDARY_ROOT); second=qualify_v002_boundary(BOUNDARY_ROOT)
    assert first==second
    assert first.decision=='qualified'
    assert first.boundary_version==2 and first.supersedes_boundary_version==1
    assert first.polygon_count==6 and first.offshore_island_count==5
    assert first.unique_vertex_count==1048 and first.mainland_vertex_count==744
    assert first.extent[1] < 0 < first.extent[3]
    assert len(first.receipt_sha256)==64

def test_supersession_preserves_historical_v001_and_defers_runtime_activation():
    receipt=build_v001_to_v002_supersession(BOUNDARY_ROOT)
    assert receipt.predecessor_version==1 and receipt.successor_version==2
    assert receipt.predecessor_result_lifecycle=='superseded'
    assert receipt.successor_result_lifecycle=='qualified'
    assert receipt.historical_predecessor_retained is True
    assert receipt.runtime_activation_deferred_to=='P004.M1.5'
    assert (BOUNDARY_ROOT/'qualified/novegeo_world_boundary_v001.geojson').is_file()
    assert not (BOUNDARY_ROOT/'qualified/novegeo_world_boundary_v002.geojson').exists()
