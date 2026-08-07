import json
from pathlib import Path

from infrastructure.geography.publication import build_v002_multi_resolution_publication

ROOT = Path(__file__).parents[4]
BOUNDARY = ROOT / "data/novegeo/geography/world-boundary"
MANIFEST = BOUNDARY / "publication/v002/publication-manifest.json"
FRONTEND_MANIFEST = ROOT / "frontend/public/geography/novegeo/world-boundary/v002/manifest.json"


def test_governed_manifest_matches_runtime_publication_contract() -> None:
    expected = build_v002_multi_resolution_publication(BOUNDARY).to_dict()
    governed = json.loads(MANIFEST.read_text(encoding="utf-8"))
    frontend = json.loads(FRONTEND_MANIFEST.read_text(encoding="utf-8"))
    assert governed == expected
    assert frontend == expected
    assert governed["activation"] == {
        "active": True,
        "activatedByMilestone": "P004.M1.5",
        "predecessorBoundaryVersion": 1,
    }
    assert [item["resolutionClass"] for item in governed["representations"]] == ["overview", "standard"]


def test_public_runtime_assets_preserve_v002_lineage_and_islands() -> None:
    for resolution, expected_vertices in (("overview", 197), ("standard", 493)):
        payload = json.loads((ROOT / f"frontend/public/geography/novegeo/world-boundary/v002/{resolution}.geojson").read_text(encoding="utf-8"))
        properties = payload["features"][0]["properties"]
        assert properties["sourceBoundaryVersion"] == 2
        assert properties["sourceQualificationId"] == "qualification:novegeo:world-boundary:v002"
        assert properties["resolutionClass"] == resolution
        assert properties["derivativeVertexCount"] == expected_vertices
        assert properties["polygonCount"] == 6
        assert properties["offshoreIslandCount"] == 5
