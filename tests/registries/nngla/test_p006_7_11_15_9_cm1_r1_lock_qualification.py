"""P006.7.11.15.9 CM1_R1 — exact lock qualification for the CM1 seam.

This is additive regression proof.  It does not replace the historical
P006.7.11.7.20 lock tests; it verifies the narrow compatibility-successor
contract appended to that existing test module.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import runpy


ROOT = Path(__file__).resolve().parents[3]
LOCK_PATH = ROOT / "tests/registries/nngla/test_p006_7_11_7_20_operational_backend_lock.py"
LOCK = runpy.run_path(str(LOCK_PATH))

EXPECTED_CM1 = {
    "frontend/src/main.js": "811de1d1ae59778a2f6109a640b748b93ffb5acaeebb9aa199ddf5c604a19483",
    "frontend/sw.js": "65994c75cb10f5e048311d34d010633ff2b29e77adb7451d66161f4dc6fed6a9",
    "infrastructure/api/app/live_composition.py": "10c805ba28aafd04105dc2deecb124c03ce4911d0155ceac8be2f247ab8db052",
}


def test_cm1_r1_successor_hashes_match_the_already_delivered_cm1_bytes():
    assert LOCK["P006_7_11_15_9_CM1_COMPOSITION_SUCCESSOR_SHA256"] == EXPECTED_CM1
    for relative, expected in EXPECTED_CM1.items():
        path = ROOT / relative
        assert path.is_file(), relative
        assert sha256(path.read_bytes()).hexdigest() == expected


def test_cm1_r1_requires_the_predecessor_cm1_proof_files():
    proofs = tuple(LOCK["P006_7_11_15_9_CM1_PROOF_FILES"])
    assert proofs == (
        "tests/infrastructure/api/test_p006_7_11_15_9_compat_map_extension_seam.py",
        "tests/infrastructure/api/test_p006_7_11_15_9_compat_live_composition_source.py",
        "frontend/tests/app/features/p006_7_11_15_9_compat_map-extension-loader.test.mjs",
        "frontend/tests/app/features/p006_7_11_15_9_compat_main-source.test.mjs",
        "frontend/tests/pwa/p006_7_11_15_9_compat_extension-seam-refresh.test.mjs",
    )
    assert all((ROOT / relative).is_file() for relative in proofs)


def test_cm1_r1_authorization_is_exact_path_and_does_not_expand_the_lock():
    authorize = LOCK["_authorized_p006_7_11_15_9_cm1_composition_successor"]
    for relative in EXPECTED_CM1:
        assert authorize(ROOT, relative)

    assert not authorize(ROOT, "frontend/src/pwa/cache-policy.js")
    assert not authorize(ROOT, "frontend/src/app/application.js")
    assert not authorize(ROOT, "roadmap_data.py")


def test_cm1_r1_preserves_the_historical_15_7_scope_and_cache_policy_lock():
    historical = LOCK["P006_7_11_15_7_COMPOSITION_SUCCESSOR_SHA256"]
    assert set(historical) == {
        "frontend/src/main.js",
        "frontend/src/pwa/cache-policy.js",
        "frontend/sw.js",
        "infrastructure/api/app/live_composition.py",
    }
    assert historical["frontend/src/pwa/cache-policy.js"] == (
        "59354982093f52ab11a1c76c55bdc987350b3d25d81e5ccf8ee3649bf66d373b"
    )
