from __future__ import annotations
import json
from pathlib import Path
ROOT = Path(__file__).parents[3]
FRONTEND = ROOT / "frontend"

def test_p002_5_application_shell_integration_files_exist() -> None:
    required = (
        "index.html", "src/main.js", "src/app/application.js", "styles/app.css",
        "public/brand/nexilabs/metadata/brand-tokens.css",
    )
    for relative in required:
        assert (FRONTEND / relative).is_file(), relative

def test_p003_1_manifest_contract_is_installable_and_scoped() -> None:
    manifest = json.loads((FRONTEND / "public/manifest.webmanifest").read_text())
    assert manifest["name"] == "NexiLabs NoveGeo PWA"
    assert manifest["start_url"].startswith("./")
    assert manifest["scope"] == "./"
    assert manifest["display"] == "standalone"
    assert {icon["purpose"] for icon in manifest["icons"]} == {"any", "maskable"}

def test_p003_2_service_worker_registration_contract() -> None:
    main = (FRONTEND / "src/main.js").read_text()
    registration = (FRONTEND / "src/pwa/service-worker-registration.js").read_text()
    assert "registerServiceWorker" in main
    assert 'scriptUrl = "./sw.js"' in registration
    assert 'scope = "./"' in registration
    assert 'updateViaCache: "none"' in registration

def test_p003_3_offline_shell_cache_contract() -> None:
    worker = (FRONTEND / "sw.js").read_text()
    for marker in ("cache.addAll(APP_SHELL)", 'request.mode === "navigate"', "caches.match(OFFLINE_URL)"):
        assert marker in worker
    assert 'request.method !== "GET"' in worker
    assert "self.location.origin" in worker

def test_p003_4_update_recovery_and_versioning_contract() -> None:
    worker = (FRONTEND / "sw.js").read_text()
    registration = (FRONTEND / "src/pwa/service-worker-registration.js").read_text()
    assert 'CACHE_NAME = "novegeo-shell-v3"' in worker
    assert "caches.delete" in worker
    assert "SKIP_WAITING" in worker
    assert "activateUpdate" in registration
    assert "checkForUpdate" in registration
