from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_live_postgresql_composition_adds_region_adapter_without_replacing_existing_map_service():
    source = (ROOT / "infrastructure/api/app/live_composition.py").read_text()
    assert "PostgreSQLNNGLANationalMapRepository" in source
    assert "PostgreSQLRegionPublicMapRepository" in source
    assert "RegionAugmentedNNGLANationalMapRepository" in source
    assert "PostgreSQLRegionAugmentedNNGLAMapReadService" in source
    assert "nngla_map_read_service=nngla_map_read_service" in source
    assert "roadmap" not in source.lower()
