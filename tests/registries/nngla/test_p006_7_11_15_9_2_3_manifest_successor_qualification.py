import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


EXPECTED = {
    "frontend/public/geography/novegeo/map-extensions/manifest.json": [
        {
            "extensionId": "nngla-map-extension:municipality:v1",
            "order": 100,
            "module": "./src/app/features/novegeo-municipality-map-experience.js",
        },
        {
            "extensionId": "nngla-map-extension:city-district:v1",
            "order": 200,
            "module": "./src/app/features/novegeo-city-district-map-experience.js",
        },
        {
            "extensionId": "nngla-map-extension:town:v1",
            "order": 300,
            "module": "./src/app/features/novegeo-town-map-experience.js",
        },
    ],
    "infrastructure/api/app/nngla_map_extensions/extension_manifest.json": [
        {
            "extensionId": "nngla-map-extension:municipality:v1",
            "order": 100,
            "module": (
                "infrastructure.api.app.nngla_map_extensions.layers."
                "municipality_spatial_publication"
            ),
        },
        {
            "extensionId": "nngla-map-extension:city-district:v1",
            "order": 200,
            "module": (
                "infrastructure.api.app.nngla_map_extensions.layers."
                "city_district_spatial_publication"
            ),
        },
        {
            "extensionId": "nngla-map-extension:town:v1",
            "order": 300,
            "module": (
                "infrastructure.api.app.nngla_map_extensions.layers."
                "town_settlement_footprint_publication"
            ),
        },
    ],
}


def test_exact_manifest_successor_contract():
    for relative, expected in EXPECTED.items():
        payload = json.loads(
            (ROOT / relative).read_text(
                encoding="utf-8"
            )
        )

        assert payload == {
            "manifestVersion": 1,
            "extensions": expected,
        }
