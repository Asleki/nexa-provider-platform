from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_compatibility_seam_is_after_locked_region_city_composition() -> None:
    source = (ROOT / "infrastructure/api/app/live_composition.py").read_text(encoding="utf-8")
    assert "PostgreSQLNNGLANationalMapRepository" in source
    assert "RegionAugmentedNNGLANationalMapRepository" in source
    assert "CityAugmentedNNGLANationalMapRepository" in source
    assert "PostgreSQLCityAugmentedNNGLAMapReadService" in source
    assert "NNGLAMapExtensionContext" in source
    assert "compose_nngla_map_extensions" in source
    assert source.index("RegionAugmentedNNGLANationalMapRepository") < source.index("CityAugmentedNNGLANationalMapRepository")
    assert source.index("PostgreSQLCityAugmentedNNGLAMapReadService(") < source.index("compose_nngla_map_extensions(")
    assert "region_public_map_repository" in source
    assert "city_public_map_repository" in source
    assert "roadmap" not in source.lower()
