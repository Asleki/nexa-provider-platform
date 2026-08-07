from pathlib import Path
import json

import pytest

from infrastructure.geography.terrain import (
    TerrainValidationError,
    qualify_terrain_dataset,
    sample_elevation,
    validate_terrain_dataset,
)

ROOT = Path(__file__).resolve().parents[4] / "data/novegeo/geography/terrain"


def test_p005_1_qualified_terrain_declares_vertical_reference_and_land_only_nodata():
    value = json.loads((ROOT / "qualified/novegeo_terrain_v001.json").read_text())
    samples = validate_terrain_dataset(value)
    assert value["elevationDatum"]["unit"] == "metre"
    assert value["sampling"]["noDataValue"] is None
    assert value["sampling"]["landOnly"] is True
    assert len(samples) > 1000
    assert {sample.landform_class for sample in samples} == {"mountain", "valley", "plain", "plateau"}


def test_p005_1_terrain_qualification_and_sampling_are_deterministic():
    path = ROOT / "qualified/novegeo_terrain_v001.json"
    value = json.loads(path.read_text())
    receipt = qualify_terrain_dataset(path)
    first = sample_elevation(value, 36.5, 0.5)
    second = sample_elevation(value, 36.5, 0.5)
    assert receipt.decision == "qualified"
    assert receipt.sample_count == len(value["samples"])
    assert first == second


def test_p005_1_rejects_zero_as_nodata_semantic():
    value = json.loads((ROOT / "qualified/novegeo_terrain_v001.json").read_text())
    value["sampling"]["noDataValue"] = 0
    with pytest.raises(TerrainValidationError, match="no-data"):
        validate_terrain_dataset(value)
