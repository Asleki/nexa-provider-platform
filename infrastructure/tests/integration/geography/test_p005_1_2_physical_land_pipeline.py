from pathlib import Path
import json

from infrastructure.geography.terrain import qualify_terrain_dataset, validate_terrain_dataset
from infrastructure.geography.landforms import validate_landform_dataset

ROOT = Path(__file__).resolve().parents[4]


def test_p005_1_2_physical_land_publication_pipeline_is_qualified_and_browser_safe():
    terrain_root = ROOT / "data/novegeo/geography/terrain"
    land_root = ROOT / "data/novegeo/geography/landforms"
    terrain = json.loads((terrain_root / "qualified/novegeo_terrain_v001.json").read_text())
    landforms = json.loads((land_root / "qualified/novegeo_landforms_v001.geojson").read_text())
    terrain_manifest = json.loads((terrain_root / "publication/v001/publication-manifest.json").read_text())
    landform_manifest = json.loads((land_root / "publication/v001/publication-manifest.json").read_text())

    receipt = qualify_terrain_dataset(terrain_root / "qualified/novegeo_terrain_v001.json")
    samples = validate_terrain_dataset(terrain)
    features = validate_landform_dataset(landforms)

    assert receipt.decision == "qualified"
    assert terrain_manifest["activation"]["active"] is True
    assert terrain_manifest["activation"]["activatedByMilestone"] == "P005.1"
    assert landform_manifest["activation"]["active"] is True
    assert landform_manifest["activation"]["activatedByMilestone"] == "P005.2"
    assert len(samples) > 1000
    assert len(features) >= 8

    browser_terrain = json.loads((ROOT / "frontend/public/geography/novegeo/terrain/v001/standard.json").read_text())
    browser_landforms = json.loads((ROOT / "frontend/public/geography/novegeo/landforms/v001/standard.geojson").read_text())
    assert browser_terrain["sourceContentSha256"] == terrain["contentSha256"]
    assert browser_landforms["properties"]["terrainDatasetVersion"] == 1
    assert all(feature["geometry"]["type"] == "Point" for feature in browser_landforms["features"])
