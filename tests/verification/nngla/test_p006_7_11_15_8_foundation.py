from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PRODUCTION = ROOT / "registries/nngla/city_realization"
VERIFY = ROOT / "verification/nngla/p006_7_11_15_8"


def test_p006_7_11_15_8_is_additive_and_does_not_require_new_migration_or_roadmap_edit():
    required = (
        PRODUCTION / "contracts.py",
        PRODUCTION / "source.py",
        PRODUCTION / "planning.py",
        PRODUCTION / "postgis.py",
        PRODUCTION / "persistence.py",
        PRODUCTION / "service.py",
        VERIFY / "preview.py",
        VERIFY / "execute.py",
        VERIFY / "verify.py",
    )
    assert all(path.is_file() for path in required)
    corpus = "\n".join(path.read_text(encoding="utf-8") for path in required)
    assert "nngla_city_geometry_record" in corpus
    assert "nngla_city_publication" in corpus
    assert "nngla_city_public_read_v1" in corpus
    assert "nngla_execution_receipt" in corpus
    assert "nngla_execution_item" in corpus
    assert "roadmap_frontend.py" not in corpus


def test_realization_is_linear_and_historical_city_authority_is_not_a_runtime_dependency():
    postgis = (PRODUCTION / "postgis.py").read_text(encoding="utf-8")
    service = (PRODUCTION / "service.py").read_text(encoding="utf-8")
    assert "ST_Intersection" in postgis
    assert postgis.count("ST_Intersection") == 1
    for forbidden in (
        "nngla_city_feature_qualification",
        "nngla_administrative_geometry_adoption_decision",
        "nngla_administrative_geometry_assignment",
        "nngla_city_authority_receipt",
        "ST_SnapToGrid",
    ):
        assert forbidden not in service
        assert forbidden not in postgis
