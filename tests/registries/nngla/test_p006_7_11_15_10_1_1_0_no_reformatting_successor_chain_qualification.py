"""P006.7.11.15.10.1.1.0 — no-reformatting successor-chain qualification.

This is additive proof. It does not replace predecessor lock tests.
"""
from __future__ import annotations

from pathlib import Path
import runpy


ROOT = Path(__file__).resolve().parents[3]
LOCK_PATH = ROOT / "tests/registries/nngla/test_p006_7_11_7_20_operational_backend_lock.py"
CM1_PATH = ROOT / "tests/registries/nngla/test_p006_7_11_15_9_cm1_r1_lock_qualification.py"

EXPECTED_TEST_SUCCESSORS = {
    "frontend/tests/integration/p006_7_11_15_10_map-first-css-contract.test.mjs":
        "b757a4a5994cb9d0630a15534338b0d07a4816115ba5f59c07213975cde16278",
    "frontend/tests/map/cartography/p006_7_11_15_10_presentation-coordinator.test.mjs":
        "f316272fec007d6d284d2b8bb4a451887de0222564e58c14edfdb172797eb99d",
}

EXPECTED_15_10_1_SW = (
    "92afa24059fdfd3a20dda67e78c99cf114d3e3d015463d4d7839bdf63a14277d"
)


def test_historical_operational_lock_source_markers_remain_verbatim():
    text = LOCK_PATH.read_text(encoding="utf-8")
    assert 'current["extensions"][:len(prior["extensions"])] == prior["extensions"]' in text
    assert 'if status == "??":' in text
    assert "Locked production or roadmap surfaces changed during later additive work." in text


def test_15_10_1_and_15_10_1_1_successor_scopes_remain_exact_and_roadmap_free():
    lock = runpy.run_path(str(LOCK_PATH))

    production = lock["P006_7_11_15_10_1_STYLING_ARCHITECTURE_SUCCESSOR_SHA256"]
    assert production["frontend/sw.js"] == EXPECTED_15_10_1_SW
    assert not any("roadmap" in path.lower() for path in production)

    test_successors = lock["P006_7_11_15_10_1_TEST_SUCCESSOR_SHA256"]
    assert test_successors == EXPECTED_TEST_SUCCESSORS
    assert not any("roadmap" in path.lower() for path in test_successors)

    removals = lock["P006_7_11_15_10_1_POST_ACCEPTANCE_REMOVALS"]
    assert removals == ("frontend/P006_15_10_RUNTIME_DIAG.html",)


def test_frontend_test_successor_authorizer_does_not_become_a_broad_exemption():
    lock = runpy.run_path(str(LOCK_PATH))
    authorize = lock["_authorized_p006_7_11_15_10_1_test_successor"]

    assert not authorize(
        ROOT,
        "frontend/tests/map/cartography/p006_7_11_15_10_semantic-zoom-v2.test.mjs",
    )
    assert not authorize(
        ROOT,
        "frontend/tests/pwa/p006_7_11_15_10_r2_map-first-shell-refresh.test.mjs",
    )
    assert not authorize(ROOT, "roadmap_data.py")


def test_cm1_qualification_preserves_old_evidence_and_appends_exact_15_10_1_sw():
    text = CM1_PATH.read_text(encoding="utf-8")

    assert (
        '"frontend/sw.js": '
        '"65994c75cb10f5e048311d34d010633ff2b29e77adb7451d66161f4dc6fed6a9"'
    ) in text
    assert (
        '"frontend/sw.js": '
        '"e3271948407449bde5d4da9124d339b7bc61196b82fdcc26fb5b447dd6f30091"'
    ) in text
    assert EXPECTED_15_10_1_SW in text
    assert "EXPECTED_15_10_1_PWA_SUCCESSORS" in text
    assert "_authorized_p006_7_11_15_10_1_styling_architecture_successor" in text
