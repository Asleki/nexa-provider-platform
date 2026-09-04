"""P006.7.11.15.10 R2 — historical lock plus .15.10.1 maintenance successor qualification."""
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


def test_r2_historical_successor_scope_and_hash_evidence_are_preserved():
    assert LOCK["P006_7_11_15_10_R2_PWA_SUCCESSOR_SHA256"] == EXPECTED
    assert set(EXPECTED) == {"frontend/sw.js", "frontend/src/pwa/cache-policy.js"}


def test_r2_or_exact_15_10_1_maintenance_successor_is_authorized():
    authorize = LOCK["_authorized_p006_7_11_15_10_r2_pwa_successor"]
    successor = LOCK["P006_7_11_15_10_1_STYLING_ARCHITECTURE_SUCCESSOR_SHA256"]
    for relative in EXPECTED:
        digest = sha256((ROOT / relative).read_bytes()).hexdigest()
        assert digest in {EXPECTED[relative], successor[relative]}
        assert authorize(ROOT, relative)
    assert not authorize(ROOT, "frontend/src/main.js")
    assert not authorize(ROOT, "roadmap_data.py")


def test_r2_preserves_locked_cache_abi_and_has_historical_and_successor_proofs():
    worker = (ROOT / "frontend/sw.js").read_text(encoding="utf-8")
    policy = (ROOT / "frontend/src/pwa/cache-policy.js").read_text(encoding="utf-8")
    assert 'CACHE_NAME = "nexilabs-shell-v17"' in worker
    assert 'PWA_CACHE_VERSION = "nexilabs-shell-v17"' in policy
    historical = LOCK["P006_7_11_15_10_R2_PWA_PROOF_FILES"]
    successor = LOCK["P006_7_11_15_10_1_STYLING_ARCHITECTURE_PROOF_FILES"]
    assert all((ROOT / relative).is_file() for relative in historical)
    assert all((ROOT / relative).is_file() for relative in successor)
