"""P006.7.11.15.10.1 — exact verified-defect successor lock qualification."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[3]
LOCK_PATH = ROOT / "tests/registries/nngla/test_p006_7_11_7_20_operational_backend_lock.py"
LOCK = runpy.run_path(str(LOCK_PATH))

EXPECTED = {
    "frontend/src/map/nngla/governed-snapshot-loader.js": "4f2042e3d0f64319bd85460189d11e5aa7295c17a74431631f6313843c48528e",
    "frontend/src/map/geography/live-boundary-client.js": "4c87ca950cb2779553152b9caca964ad5db558da53c263b3b174514e27a120df",
    "frontend/src/map/nngla/national-map-client.js": "10b6854bea743538251313a67c6ed26544bff314fcade015fb0436ada6b7d5c9",
    "frontend/src/map/cartography/presentation-coordinator.js": "319406e8613cc64c7b20b63e802695f9275b95535a653614d16a3c0a5e5b80e4",
    "frontend/styles/novegeo-map-first-v1.css": "4b6f24968c9ce832ef8dfa996d5b27b0636f5d865e53efba21baf1aa045e8690",
    "frontend/src/pwa/cache-policy.js": "06826644a273905bae2259757e20100ddc59f3294eb9f51b1d4e7a246b9a1eea",
    "frontend/sw.js": "92afa24059fdfd3a20dda67e78c99cf114d3e3d015463d4d7839bdf63a14277d",
    "infrastructure/database/runtime/pool.py": "b478ca0808871c9bc4572f119d1f75ef83edaa241668653b77a2eb33fd72879b",
    "infrastructure/api/routers/nngla_map.py": "ad74d774d41f9bddc302524a501d9e5edf55dc6f8533695ffba4b630784a4865",
}

EXPECTED_15_10_1_2_SUCCESSORS = {
    "infrastructure/database/runtime/pool.py": "65aca27bed69fc12483265df826ebea8a9dd43e2d3d2e6ec32606ac9b28b9a33",
}


EXPECTED_TEST_SUCCESSORS = {
    "frontend/tests/integration/p006_7_11_15_10_map-first-css-contract.test.mjs": "b757a4a5994cb9d0630a15534338b0d07a4816115ba5f59c07213975cde16278",
    "frontend/tests/map/cartography/p006_7_11_15_10_presentation-coordinator.test.mjs": "f316272fec007d6d284d2b8bb4a451887de0222564e58c14edfdb172797eb99d",
}


def test_styling_architecture_successor_scope_is_exact_and_roadmap_free():
    assert LOCK["P006_7_11_15_10_1_STYLING_ARCHITECTURE_SUCCESSOR_SHA256"] == EXPECTED
    assert not any("roadmap" in path.lower() for path in EXPECTED)
    assert not any(path.startswith("database/migrations/") for path in EXPECTED)
    assert "frontend/src/main.js" not in EXPECTED
    assert "infrastructure/api/app/live_composition.py" not in EXPECTED
    assert LOCK["P006_7_11_15_10_1_POST_ACCEPTANCE_REMOVALS"] == ("frontend/P006_15_10_RUNTIME_DIAG.html",)


def test_styling_architecture_successor_hashes_and_authorization_are_exact():
    authorize = LOCK["_authorized_p006_7_11_15_10_1_styling_architecture_successor"]
    authorize_15_10_1_2 = LOCK["_authorized_p006_7_11_15_10_1_2_request_materialization_successor"]
    for relative, expected in EXPECTED.items():
        path = ROOT / relative
        assert path.is_file(), relative
        current_expected = EXPECTED_15_10_1_2_SUCCESSORS.get(relative, expected)
        assert sha256(path.read_bytes()).hexdigest() == current_expected
        assert authorize(ROOT, relative) or authorize_15_10_1_2(ROOT, relative)
    assert not authorize(ROOT, "roadmap_data.py")
    assert not authorize(ROOT, "frontend/src/main.js")
    assert not authorize_15_10_1_2(ROOT, "roadmap_data.py")
    assert not authorize_15_10_1_2(ROOT, "frontend/src/main.js")


def test_15_10_1_2_successor_preserves_historical_pool_hash_and_is_narrow():
    assert EXPECTED["infrastructure/database/runtime/pool.py"] == (
        "b478ca0808871c9bc4572f119d1f75ef83edaa241668653b77a2eb33fd72879b"
    )
    assert EXPECTED_15_10_1_2_SUCCESSORS == {
        "infrastructure/database/runtime/pool.py":
            "65aca27bed69fc12483265df826ebea8a9dd43e2d3d2e6ec32606ac9b28b9a33"
    }
    assert not any("roadmap" in path.lower() for path in EXPECTED_15_10_1_2_SUCCESSORS)


def test_historical_15_10_and_r2_hash_evidence_remains_present():
    assert LOCK["P006_7_11_15_10_PRESENTATION_SUCCESSOR_SHA256"]
    assert LOCK["P006_7_11_15_10_R2_PWA_SUCCESSOR_SHA256"]


def test_historical_frontend_test_successor_scope_is_exact_and_narrow():
    assert LOCK["P006_7_11_15_10_1_TEST_SUCCESSOR_SHA256"] == EXPECTED_TEST_SUCCESSORS
    assert set(EXPECTED_TEST_SUCCESSORS) == {
        "frontend/tests/integration/p006_7_11_15_10_map-first-css-contract.test.mjs",
        "frontend/tests/map/cartography/p006_7_11_15_10_presentation-coordinator.test.mjs",
    }
    assert not set(EXPECTED_TEST_SUCCESSORS).intersection(EXPECTED)
    assert not any("roadmap" in path.lower() for path in EXPECTED_TEST_SUCCESSORS)


def test_historical_frontend_test_successor_hashes_and_authorization_are_exact():
    authorize = LOCK["_authorized_p006_7_11_15_10_1_test_successor"]
    for relative, expected in EXPECTED_TEST_SUCCESSORS.items():
        path = ROOT / relative
        assert path.is_file(), relative
        assert sha256(path.read_bytes()).hexdigest() == expected
        assert authorize(ROOT, relative)

    assert not authorize(ROOT, "frontend/tests/map/cartography/p006_7_11_15_10_semantic-zoom-v2.test.mjs")
    assert not authorize(ROOT, "frontend/tests/pwa/p006_7_11_15_10_r2_map-first-shell-refresh.test.mjs")
    assert not authorize(ROOT, "roadmap_data.py")
