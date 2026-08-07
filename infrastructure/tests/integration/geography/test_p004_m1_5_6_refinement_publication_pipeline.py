import json
from pathlib import Path

from infrastructure.geography.authoring import validate_boundary_source_package
from infrastructure.geography.refinement import qualify_v002_boundary, build_v001_to_v002_supersession
from infrastructure.geography.publication import build_v002_multi_resolution_publication

ROOT = Path(__file__).parents[4]
BOUNDARY = ROOT / "data/novegeo/geography/world-boundary"


def test_10a_10b_10c_refinement_chain_is_version_continuous() -> None:
    authoring = validate_boundary_source_package(BOUNDARY)
    qualification = qualify_v002_boundary(BOUNDARY)
    supersession = build_v001_to_v002_supersession(BOUNDARY)
    publication = build_v002_multi_resolution_publication(BOUNDARY)

    assert authoring.boundary_version == qualification.boundary_version == publication.boundary_version == 2
    assert supersession.predecessor_version == 1
    assert supersession.successor_version == 2
    assert publication.qualification_id == qualification.qualification_id
    assert publication.qualification_receipt_sha256 == qualification.receipt_sha256
    assert publication.source_authoritative_vertex_count == authoring.unique_vertex_count == 1048
    assert publication.select("standard").vertex_count < publication.source_authoritative_vertex_count
    assert publication.select("overview").vertex_count < publication.select("standard").vertex_count


def test_runtime_standard_publication_is_not_the_historical_v001_polygon() -> None:
    v001 = json.loads((BOUNDARY / "publication/novegeo_world_boundary_v001.geojson").read_text(encoding="utf-8"))
    v002 = json.loads((ROOT / "frontend/public/geography/novegeo/world-boundary/v002/standard.geojson").read_text(encoding="utf-8"))
    assert v002["features"][0]["properties"]["sourceBoundaryVersion"] == 2
    assert v002["features"][0]["properties"]["derivativeVertexCount"] == 493
    assert v002["features"][0]["geometry"] != v001["features"][0]["geometry"]
