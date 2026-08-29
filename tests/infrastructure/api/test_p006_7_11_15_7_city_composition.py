from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_live_postgresql_composition_layers_city_after_locked_region_adapter():
    source = (ROOT / "infrastructure/api/app/live_composition.py").read_text()
    assert "PostgreSQLNNGLANationalMapRepository" in source
    assert "PostgreSQLRegionPublicMapRepository" in source
    assert "RegionAugmentedNNGLANationalMapRepository" in source
    assert "PostgreSQLCityPublicMapRepository" in source
    assert "CityAugmentedNNGLANationalMapRepository" in source
    assert "PostgreSQLCityAugmentedNNGLAMapReadService" in source
    assert source.index("RegionAugmentedNNGLANationalMapRepository") < source.index("CityAugmentedNNGLANationalMapRepository")
    assert "nngla_map_read_service=nngla_map_read_service" in source
    assert "roadmap" not in source.lower()
