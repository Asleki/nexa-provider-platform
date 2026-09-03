"""P006.7.11.15.10 R2 — exact lock qualification for PWA refresh successors."""
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


def test_r2_successor_scope_and_hashes_are_exact():
    assert LOCK["P006_7_11_15_10_R2_PWA_SUCCESSOR_SHA256"] == EXPECTED
    authorize = LOCK["_authorized_p006_7_11_15_10_r2_pwa_successor"]
    for relative, expected in EXPECTED.items():
        assert sha256((ROOT / relative).read_bytes()).hexdigest() == expected
        assert authorize(ROOT, relative)
    assert not authorize(ROOT, "frontend/src/main.js")
    assert not authorize(ROOT, "roadmap_data.py")


def test_r2_preserves_locked_cache_abi_and_has_proof_files():
    worker = (ROOT / "frontend/sw.js").read_text(encoding="utf-8")
    policy = (ROOT / "frontend/src/pwa/cache-policy.js").read_text(encoding="utf-8")
    assert 'CACHE_NAME = "nexilabs-shell-v17"' in worker
    assert 'PWA_CACHE_VERSION = "nexilabs-shell-v17"' in policy
    proofs = LOCK["P006_7_11_15_10_R2_PWA_PROOF_FILES"]
    assert all((ROOT / relative).is_file() for relative in proofs)
