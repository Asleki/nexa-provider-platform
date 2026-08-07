import json
from pathlib import Path

from infrastructure.geography.authoring import validate_boundary_source_package
from infrastructure.geography.geometry import normalize_boundary_geometry

ROOT = Path(__file__).parents[4]
BOUNDARY_ROOT = ROOT / "data/novegeo/geography/world-boundary"


def test_v002_high_resolution_candidate_is_valid_mainland_with_islands_and_crosses_equator():
    receipt = validate_boundary_source_package(BOUNDARY_ROOT)
    candidate = json.loads((BOUNDARY_ROOT / "candidate/novegeo_world_boundary_v002.geojson").read_text(encoding="utf-8"))
    geometry = candidate["features"][0]["geometry"]
    normalized = normalize_boundary_geometry(geometry)

    assert normalized["type"] == "MultiPolygon"
    assert receipt.polygon_count == 6
    assert receipt.offshore_island_count == 5
    assert receipt.mainland_vertex_count >= 500
    assert receipt.unique_vertex_count >= 750
    assert receipt.extent[1] < 0 < receipt.extent[3]


def test_v001_is_preserved_while_v002_remains_candidate_only():
    v001_publication = BOUNDARY_ROOT / "publication/novegeo_world_boundary_v001.geojson"
    v002_publication = BOUNDARY_ROOT / "publication/novegeo_world_boundary_v002.geojson"
    v002_qualified = BOUNDARY_ROOT / "qualified/novegeo_world_boundary_v002.geojson"
    assert v001_publication.is_file()
    assert not v002_publication.exists()
    assert not v002_qualified.exists()
