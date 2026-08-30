from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PRODUCTION = ROOT / "registries/nngla/city_containment_qualification"
VERIFY = ROOT / "verification/nngla/p006_7_11_15_8_1"


def test_p006_7_11_15_8_1_is_additive_and_keeps_locked_15_8_geometry_engine_out_of_delivery():
    required = (
        PRODUCTION / "contracts.py",
        PRODUCTION / "planning.py",
        PRODUCTION / "postgis.py",
        PRODUCTION / "persistence.py",
        PRODUCTION / "service.py",
        VERIFY / "preview.py",
        VERIFY / "matrix.py",
        VERIFY / "execute.py",
        VERIFY / "verify.py",
    )
    assert all(path.is_file() for path in required)
    corpus = "\n".join(path.read_text(encoding="utf-8") for path in required)
    assert "nngla_city_parent_containment_qualification" in corpus
    assert "roadmap_frontend.py" not in corpus
    assert "ST_SnapToGrid" not in corpus
    assert corpus.count("ST_Intersection") == 1


def test_operator_surface_has_read_only_preview_and_matrix_plus_explicit_writer_gate():
    preview = (VERIFY / "preview.py").read_text(encoding="utf-8")
    matrix = (VERIFY / "matrix.py").read_text(encoding="utf-8")
    execute = (VERIFY / "execute.py").read_text(encoding="utf-8")
    assert "SET TRANSACTION READ ONLY" in preview
    assert "SET TRANSACTION READ ONLY" in matrix
    assert "--execute" in execute
    assert "REFUSED:" in execute
