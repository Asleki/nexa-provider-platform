"""P006.7.11.15.10 R2 — historical PWA lock plus exact later maintenance successors."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[3]
LOCK_PATH = ROOT / "tests/registries/nngla/test_p006_7_11_7_20_operational_backend_lock.py"
LOCK = runpy.run_path(str(LOCK_PATH))

EXPECTED = {
    "frontend/sw.js": "e3271948407449bde5d4da9124d339b7bc61196b82fdcc26fb5b447dd6f30091",
    "frontend/src/pwa/cache-policy.js": "d8f1fcaf98733b95c4c19f3d069a54b79598665dd7cfdb213985d3e35d4263a4",
}

EXPECTED_15_10_1_3_SUCCESSORS = {
    "frontend/sw.js": "1db4bdcac4ac719762f3e29e8647de2b6efe6eede3393f8573e36562ce28897c",
    "frontend/src/pwa/cache-policy.js": "baa55cbe2c227615084f9666568710d9c25259ec8feb673cf28fe4d990807d20",
}

EXPECTED_P006_UI_10_1_R2_SUCCESSORS = {
    "frontend/sw.js": "7fb8964ddbb9efe64948eb842dd6534f5b6cba2bd8caf87ed56d914064bda84d",
    "frontend/src/pwa/cache-policy.js": "2df032f691d551937fb9e0a34ff15b291c218abe14ed69ad99a7a36425e231e2",
}


def test_r2_historical_successor_scope_and_hash_evidence_are_preserved():
    assert LOCK["P006_7_11_15_10_R2_PWA_SUCCESSOR_SHA256"] == EXPECTED
    assert set(EXPECTED) == {"frontend/sw.js", "frontend/src/pwa/cache-policy.js"}


def test_r2_or_exact_later_pwa_successor_is_authorized():
    authorize = LOCK["_authorized_p006_7_11_15_10_r2_pwa_successor"]
    authorize_15_10_1_3 = LOCK["_authorized_p006_7_11_15_10_1_3_unified_environmental_successor"]
    authorize_ui_r2 = LOCK["_authorized_p006_ui_10_1_r2_installed_pwa_activation_successor"]
    styling = LOCK["P006_7_11_15_10_1_STYLING_ARCHITECTURE_SUCCESSOR_SHA256"]

    for relative in EXPECTED:
        digest = sha256((ROOT / relative).read_bytes()).hexdigest()
        allowed = {
            EXPECTED[relative],
            styling[relative],
            EXPECTED_15_10_1_3_SUCCESSORS[relative],
            EXPECTED_P006_UI_10_1_R2_SUCCESSORS[relative],
        }
        assert digest in allowed
        assert authorize(ROOT, relative)
        if digest == EXPECTED_P006_UI_10_1_R2_SUCCESSORS[relative]:
            assert authorize_ui_r2(ROOT, relative)
            assert not authorize_15_10_1_3(ROOT, relative)

    assert not authorize(ROOT, "frontend/src/main.js")
    assert not authorize(ROOT, "roadmap_data.py")
    assert not authorize_ui_r2(ROOT, "frontend/src/main.js")
    assert not authorize_ui_r2(ROOT, "roadmap_data.py")


def test_r2_preserves_locked_cache_abi_and_has_historical_and_successor_proofs():
    worker = (ROOT / "frontend/sw.js").read_text(encoding="utf-8")
    policy = (ROOT / "frontend/src/pwa/cache-policy.js").read_text(encoding="utf-8")
    assert 'CACHE_NAME = "nexilabs-shell-v17"' in worker
    assert 'PWA_CACHE_VERSION = "nexilabs-shell-v17"' in policy
    historical = LOCK["P006_7_11_15_10_R2_PWA_PROOF_FILES"]
    styling = LOCK["P006_7_11_15_10_1_STYLING_ARCHITECTURE_PROOF_FILES"]
    ui_r2 = LOCK["P006_UI_10_1_R2_INSTALLED_PWA_ACTIVATION_PROOF_FILES"]
    assert all((ROOT / relative).is_file() for relative in historical)
    assert all((ROOT / relative).is_file() for relative in styling)
    assert all((ROOT / relative).is_file() for relative in ui_r2)


def test_15_10_1_3_pwa_successor_remains_historical_and_exact():
    successor = LOCK["P006_7_11_15_10_1_3_UNIFIED_ENVIRONMENTAL_PRODUCTION_SHA256"]
    assert EXPECTED_15_10_1_3_SUCCESSORS == {
        relative: successor[relative] for relative in EXPECTED_15_10_1_3_SUCCESSORS
    }
    assert set(EXPECTED_15_10_1_3_SUCCESSORS) == set(EXPECTED)


def test_p006_ui_10_1_r2_is_exact_v17_maintenance_only():
    successor = LOCK["P006_UI_10_1_R2_INSTALLED_PWA_ACTIVATION_SUCCESSOR_SHA256"]
    assert successor == EXPECTED_P006_UI_10_1_R2_SUCCESSORS
    assert set(successor) == set(EXPECTED)
    assert not any("roadmap" in relative.lower() for relative in successor)
    assert not any(relative.startswith(("backend/", "infrastructure/", "database/")) for relative in successor)
