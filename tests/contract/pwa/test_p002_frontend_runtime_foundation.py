"""Contract tests for P002.1 and P002.2 frontend runtime foundation."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FRONTEND = ROOT / "frontend"


def _text(relative: str) -> str:
    return (FRONTEND / relative).read_text(encoding="utf-8")


def test_required_frontend_runtime_files_exist() -> None:
    expected = (
        "index.html",
        "src/main.js",
        "src/app/application.js",
        "src/config/runtime-config.js",
        "src/core/application-state.js",
        "styles/app.css",
        "tests/application-state.test.mjs",
        "tests/runtime-config.test.mjs",
        "tests/application-bootstrap.test.mjs",
    )
    for relative in expected:
        assert (FRONTEND / relative).is_file(), relative


def test_html_uses_the_single_es_module_entry_point() -> None:
    html = _text("index.html")
    footer = _text("src/ui/partials/footer.html")
    assert '<script type="module" src="./src/main.js"></script>' in html
    assert 'id="nexilabs-app"' in html
    assert 'data-environment-name="development"' in html
    assert 'data-role="application-status"' in footer
    assert 'data-role="application-version"' in footer


def test_html_has_no_inline_or_third_party_script_dependency() -> None:
    html = _text("index.html")
    assert "https://" not in html
    assert "http://" not in html
    assert "cdn" not in html.lower()
    assert html.count("<script") == 1


def test_runtime_configuration_keeps_database_material_out_of_public_config() -> None:
    source = _text("src/config/runtime-config.js")
    for marker in ("postgres", "rds", "amazonaws", "5432", "database[_-]?password"):
        assert marker in source.lower()
    assert "Unsafe public runtime configuration" in source
    assert "apiBaseUrl must use HTTPS outside localhost" in source


def test_application_states_are_explicit_and_do_not_claim_future_capabilities() -> None:
    source = _text("src/core/application-state.js")
    for status in ("CREATED", "BOOTING", "READY", "DEGRADED", "FAILED", "STOPPED"):
        assert status in source
    config = _text("src/config/runtime-config.js")
    for capability in ("application_shell", "runtime_configuration", "health_state"):
        assert capability in config
    for unimplemented in ('"map"', '"offline"', '"database"', '"registry"', '"simulation_engine"'):
        assert unimplemented not in config


def test_bootstrap_has_visible_ready_and_failure_paths() -> None:
    source = _text("src/app/application.js")
    assert "ApplicationStatus.BOOTING" in source
    assert "ApplicationStatus.READY" in source
    assert "ApplicationStatus.FAILED" in source
    assert "bootstrap_failure" in source
    assert "data-role='application-status'" in source


def test_browser_entry_uses_only_public_document_configuration() -> None:
    source = _text("src/main.js")
    assert "documentElement" in source
    assert "createRuntimeConfig" in source
    assert "mountNexiLabsShell" in source
    assert "process.env" not in source
    assert "PGHOST" not in source
    assert "PGPASSWORD" not in source


def test_base_styles_are_responsive_and_health_aware() -> None:
    css = _text("styles/app.css")
    assert "@media" in css
    assert 'data-health-status="READY"' in css
    assert 'data-health-status="FAILED"' in css
    assert ".application-shell" in css
