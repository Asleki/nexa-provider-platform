from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[3]

def test_backend_cm1_manifest_registers_municipality_first():
    payload = json.loads((ROOT / "infrastructure/api/app/nngla_map_extensions/extension_manifest.json").read_text())
    assert payload["manifestVersion"] == 1
    assert payload["extensions"][0] == {
        "extensionId": "nngla-map-extension:municipality:v1",
        "order": 100,
        "module": "infrastructure.api.app.nngla_map_extensions.layers.municipality_spatial_publication",
    }

def test_extension_requires_locked_region_and_city_resources():
    text = (ROOT / "infrastructure/api/app/nngla_map_extensions/layers/municipality_spatial_publication.py").read_text()
    assert "region_public_map_repository" in text
    assert "city_public_map_repository" in text
    assert "live_composition" not in text
