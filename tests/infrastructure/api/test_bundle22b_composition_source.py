from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def test_bundle22b_adds_map_router_and_service_without_rewriting_generic_nngla_router():
    factory=(ROOT/"infrastructure/api/app/factory.py").read_text()
    live=(ROOT/"infrastructure/api/app/live_composition.py").read_text()
    generic=(ROOT/"infrastructure/api/routers/nngla.py").read_text()
    assert "nngla_map_router" in factory and "nngla_map_read_service" in factory
    assert "PostgreSQLNNGLANationalMapRepository" in live
    assert "nngla-map" not in generic
