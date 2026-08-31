from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]

def test_operational_lock_has_exact_two_manifest_successor_scope():
    text = (ROOT / "tests/registries/nngla/test_p006_7_11_7_20_operational_backend_lock.py").read_text()
    assert "infrastructure/api/app/nngla_map_extensions/extension_manifest.json" in text
    assert "frontend/public/geography/novegeo/map-extensions/manifest.json" in text
    assert 'current["extensions"][:len(prior["extensions"])] == prior["extensions"]' in text
