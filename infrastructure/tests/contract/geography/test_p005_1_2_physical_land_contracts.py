from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[4] / "data/novegeo/geography"


def test_p005_1_terrain_contract_preserves_p004_horizontal_authority_and_explicit_vertical_datum():
    terrain = json.loads((ROOT / "terrain/qualified/novegeo_terrain_v001.json").read_text())
    assert terrain["boundaryId"] == "boundary:novegeo:sovereign"
    assert terrain["boundaryVersion"] == 2
    assert terrain["coordinateReference"]["coordinateReferenceId"] == "crs:novegeo:geographic"
    assert terrain["coordinateReference"]["axisOrder"] == ["longitude", "latitude"]
    assert terrain["elevationDatum"]["elevationDatumId"] == "datum:novegeo:elevation:mean-sea-level"
    assert terrain["runtimeMode"] == "shared_reference"


def test_p005_2_landform_contract_references_terrain_without_embedding_terrain_dataset():
    landforms = json.loads((ROOT / "landforms/qualified/novegeo_landforms_v001.geojson").read_text())
    props = landforms["properties"]
    assert props["terrainDatasetId"] == "dataset:novegeo:terrain:elevation"
    assert props["terrainDatasetVersion"] == 1
    assert set(props["canonicalClasses"]) == {"mountain", "valley", "plain", "plateau"}
    assert all("terrainDatasetId" in feature["properties"] for feature in landforms["features"])
    assert all("samples" not in feature for feature in landforms["features"])
