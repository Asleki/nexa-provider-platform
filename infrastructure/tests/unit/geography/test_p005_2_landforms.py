from pathlib import Path
import json

from infrastructure.geography.landforms import CANONICAL_LANDFORM_CLASSES, validate_landform_dataset

ROOT = Path(__file__).resolve().parents[4] / "data/novegeo/geography/landforms"


def test_p005_2_landforms_are_semantically_distinct_and_terrain_linked():
    value = json.loads((ROOT / "qualified/novegeo_landforms_v001.geojson").read_text())
    features = validate_landform_dataset(value)
    assert {feature.landform_class for feature in features} == CANONICAL_LANDFORM_CLASSES
    assert value["properties"]["terrainDatasetId"] == "dataset:novegeo:terrain:elevation"
    assert value["properties"]["terrainDatasetVersion"] == 1
    assert len({feature.landform_id for feature in features}) == len(features)
