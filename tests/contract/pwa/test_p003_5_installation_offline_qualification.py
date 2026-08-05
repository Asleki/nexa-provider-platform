from __future__ import annotations
from pathlib import Path
ROOT = Path(__file__).parents[3]
FRONTEND = ROOT / "frontend"


def test_p003_5_additive_qualification_package_exists() -> None:
    required = (
        "src/pwa/qualification/contracts.js",
        "src/pwa/qualification/source-inspector.js",
        "src/pwa/qualification/inventory.js",
        "src/pwa/qualification/offline-simulator.js",
        "src/pwa/qualification/service.js",
        "src/pwa/qualification/formatting.js",
        "src/pwa/qualification/index.js",
        "scripts/qualify-offline-pwa.mjs",
    )
    for relative in required:
        assert (FRONTEND / relative).is_file(), relative


def test_p003_5_qualification_is_read_only_and_has_stable_evidence() -> None:
    service = (FRONTEND / "src/pwa/qualification/service.js").read_text()
    contracts = (FRONTEND / "src/pwa/qualification/contracts.js").read_text()
    assert 'milestoneId: "P003.5"' in contracts
    assert "databaseWritesPerformed: 0" in contracts
    for marker in ("manifestSha256", "serviceWorkerSha256", "cachePolicySha256", "shellInventorySha256"):
        assert marker in service


def test_p003_5_qualifies_install_offline_and_recovery_boundaries() -> None:
    inventory = (FRONTEND / "src/pwa/qualification/inventory.js").read_text()
    simulator = (FRONTEND / "src/pwa/qualification/offline-simulator.js").read_text()
    service = (FRONTEND / "src/pwa/qualification/service.js").read_text()
    assert "SHELL_INVENTORY_PARITY" in inventory
    assert "MANIFEST_ICONS_EXIST" in inventory
    assert "simulateOfflineQualification" in simulator
    assert "simulateActivationCleanup" in simulator
    assert "OFFLINE_NAVIGATION_AVAILABLE" in service
    assert "STALE_CACHE_CLEANUP" in service


def test_p003_5_does_not_import_or_execute_roadmap_tooling() -> None:
    qualification_root = FRONTEND / "src/pwa/qualification"
    forbidden_markers = ("pwa_roadmap", "roadmap_frontend", "roadmap_data", "PWA_ROADMAP.md")
    for path in qualification_root.rglob("*"):
        if path.is_file():
            text = path.read_text()
            assert not any(marker in text for marker in forbidden_markers)
